#!/usr/bin/env python3
"""Advisory TypeScript-lifecycle drift detector (TYPESCRIPT-7-BRIDGE-PILOTS-AND-TOOLKIT-CANON).

READ-ONLY, stdlib-only, deterministic. Given a *workspace scan* (already-extracted,
sanitized facts about each TypeScript surface) and an optional *registry*
(schemas/typescript-lifecycle-registry.schema.json), it flags drift between what a
repo actually does and what the registry says is approved. It **composes** the
`typescript-lifecycle` skill, it does not restate it:

- The runbook (surface inventory, classification, release-channel truth gate,
  compatibility method, migration classes A-G, bridge logic, blocked-package
  contract, re-verification triggers) is owned by `skills/typescript-lifecycle/SKILL.md`.
- The registry document shape is owned by
  `schemas/typescript-lifecycle-registry.schema.json`.
- Exact-head merge / triple-SHA / merge discipline are owned by
  `docs/06-operations/pr-lifecycle-rulebook.md` (this tool never merges anything).

WHY IT IS SAFE:
- It reads ONLY the JSON scan + registry you pass on the command line. It NEVER
  reads a source tree, NEVER shells out, NEVER opens a socket, and NEVER uploads
  source. The scan is a set of already-sanitized facts (versions, tsconfig option
  values, boolean CI signals) — not source code.
- It writes NOTHING (no fix mode, no registry write). `--emit-template` prints a
  skeleton to stdout only.
- It is ADVISORY: by default it exits 0 even with findings (only `--strict` exits
  non-zero). It is NOT wired as a required check or a merge gate anywhere.

Every finding carries a CERTAINTY label (honest-signal discipline):
- `certain`   — a deterministic fact from explicit fields (a removed option is
                present; a resolved version does not satisfy the declared range).
- `probable`  — derived from classification / supplied policy.
- `heuristic` — inferred from partial data (e.g. absence of a CI signal in the
                scan is not proof of absence in the repo — the vacuous-green class).

Finding classes:
- TSL001 direct-surface-unregistered   — a direct TS surface not in the registry.
- TSL002 compiler-version-mismatch     — lockfile resolved version does not satisfy
                                         the manifest's declared range.
- TSL003 direct-surface-missing-typecheck-ci — a direct surface with no CI job that
                                         actually runs its tsc/build (the vacuous
                                         Dependabot-green class).
- TSL004 unsupported-node-ts-combo     — Node/TS combination outside the registry's
                                         DECLARED support_matrix (never a hardcoded
                                         external floor).
- TSL005 removed-compiler-option       — a tsconfig reintroduces an option TS 7.0
                                         removed (target es5, moduleResolution node/
                                         classic, module amd/umd/system, baseUrl,
                                         esModuleInterop:false, allowSyntheticDefault
                                         Imports:false).
- TSL006 registry-entry-stale          — a registry entry's last_verified_at is older
                                         than the re-verification window.
- TSL007 resolved-version-regression   — a surface's observed resolved version is
                                         lower than the registry's recorded one.
- TSL008 preview-compiler-channel      — a resolved prerelease/preview build is not a
                                         stable target (channel uncertainty).
- resolved-version-forward-drift       — a surface's observed resolved version is HIGHER
                                         than the registry's recorded one (unreviewed
                                         upgrade; the approved fact is stale).

- resolved-version-forward-drift also fires when the observed and registry versions share
  the same (maj,min,patch) but differ as strings (a prerelease/channel move).
- registry-classification-mismatch  — the scan classifies a surface direct while the registry
                                      still records it non-direct (stale classification).

Plus structural guards (fail-closed): scan-read-error, scan-not-object, surfaces-missing,
surfaces-not-array, surface-not-object, surface-missing-field, surface-unknown-status,
surface-missing-classification, direct-surface-missing-version.

Modes:
    python3 scripts/typescript_lifecycle_drift.py --scan SCAN.json --registry REG.json
    python3 scripts/typescript_lifecycle_drift.py --scan SCAN.json --json
    python3 scripts/typescript_lifecycle_drift.py --scan SCAN.json --strict
    python3 scripts/typescript_lifecycle_drift.py --self-test
    python3 scripts/typescript_lifecycle_drift.py --emit-template

Scan document shape (a `typescript-workspace-scan/v1` object):
    {"schema": "typescript-workspace-scan/v1", "canonical": false,
     "generated_note": "...",
     "surfaces": [
       {"repository": "org/repo", "package_path": "pkg",
        "typescript_ref": "direct|dev|transitive|optional_peer|generated|none",
        "compiler_invocation": true, "declared_version": "^7.0.0",
        "resolved_version": "7.0.2", "target_version": "7.0.2",
        "node_version": "22.11.0",
        "tsconfig_options": {"target": "es2022", "module": "esnext"},
        "ci": {"typecheck_job": true, "build_job": true, "references_package": true}}
     ]}
The registry may be supplied inline as scan["registry"] or via --registry (the flag
overrides the inline copy).

Exit codes: 0 = advisory run complete (default; findings do NOT change this) ·
2 = usage / read error, OR (under --strict) at least one finding.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- taxonomy (kept in sync with schemas/typescript-lifecycle-registry.schema.json) ---

# typescript_ref values a scan surface may declare.
TS_REFS = ("direct", "dev", "transitive", "optional_peer", "generated", "docs_only", "none")

# Classification results (mirror the schema's typescript_status enum).
CLASS_DIRECT = "direct"
CLASS_TRANSITIVE = "transitive-only"
CLASS_GENERATED = "generated-only"
CLASS_DOCS = "docs-only"
CLASS_NONE = "no-typescript"

CERTAINTY_LEVELS = ("certain", "probable", "heuristic")

DEFAULT_MAX_AGE_DAYS = 90

# TS 7.0 removed compiler options. Each maps to a predicate over the reintroduced
# value(s). Ground truth: es5 target; classic node moduleResolution; amd/umd/systemjs
# module; baseUrl; esModuleInterop:false; allowSyntheticDefaultImports:false.
_REMOVED_TARGET = {"es5"}
_REMOVED_MODULE_RESOLUTION = {"node", "classic"}
_REMOVED_MODULE = {"amd", "umd", "system", "systemjs"}


# --- version handling (BOUNDED semver-range subset; fail-open by design) -------
# The npm range grammar is unbounded; parsing all of it is an asymptotic magnet.
# We parse the common subset (exact, ^, ~, comparators, x-ranges, space-AND,
# ||-OR) and FAIL OPEN on anything else: satisfies() returns None ("cannot
# determine"), and an indeterminate result NEVER produces a mismatch finding.

def _is_prerelease(raw):
    """True if the version string carries a prerelease tag (a '-' before any '+').
    A prerelease/preview build (e.g. 7.0.0-beta.1) must never be treated as its
    stable release for range math — see satisfies()."""
    if not isinstance(raw, str):
        return False
    s = raw.strip()
    if s[:1] in ("v", "V"):
        s = s[1:]
    plus = s.find("+")
    dash = s.find("-")
    return dash >= 0 and (plus < 0 or dash < plus)


def parse_version(raw):
    """Return (major, minor, patch) ints, or None if the leading token is not numeric.
    Strips a leading 'v', drops prerelease/build metadata, pads missing parts with 0."""
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    if s[0] in "vV":
        s = s[1:]
    # drop prerelease / build metadata
    for sep in ("-", "+"):
        idx = s.find(sep)
        if idx >= 0:
            s = s[:idx]
    parts = s.split(".")
    nums = []
    for i in range(3):
        if i < len(parts):
            tok = parts[i].strip()
            if not tok.isdigit():
                return None if i == 0 else None
            nums.append(int(tok))
        else:
            nums.append(0)
    return (nums[0], nums[1], nums[2])


def _xrange_bounds(token):
    """(low_inclusive, high_exclusive) for an x-range like '6', '6.2', '6.x', '6.2.*'.
    Returns None when the token is not an x-range shape we understand."""
    t = token.strip().lower()
    if t in ("", "*", "x"):
        return ((0, 0, 0), None)  # any
    parts = t.replace("*", "x").split(".")
    # a fully-specified 3-part numeric is NOT an x-range (it is an exact version)
    numeric = [p for p in parts if p.isdigit()]
    has_x = any(p == "x" for p in parts)
    if len(parts) >= 3 and len(numeric) == 3:
        return None
    if not parts or not parts[0].isdigit():
        return None
    maj = int(parts[0])
    if len(parts) == 1 or (len(parts) >= 2 and parts[1] == "x") or (len(parts) == 2 and has_x):
        return ((maj, 0, 0), (maj + 1, 0, 0))
    if len(parts) >= 2 and parts[1].isdigit():
        minor = int(parts[1])
        # '6.2', '6.2.x', '6.2.*'
        return ((maj, minor, 0), (maj, minor + 1, 0))
    return None


def _caret_bounds(ver):
    """npm caret upper bound for a (maj,min,patch) low."""
    maj, minor, patch = ver
    if maj > 0:
        return (maj + 1, 0, 0)
    if minor > 0:
        return (0, minor + 1, 0)
    return (0, 0, patch + 1)


def _tilde_bounds(token, ver):
    """npm tilde upper bound. ~a.b and ~a.b.c -> <a.(b+1).0 ; ~a -> <(a+1).0.0."""
    maj, minor, _ = ver
    parts = token.lstrip("~").strip().split(".")
    if len([p for p in parts if p != ""]) <= 1:
        return (maj + 1, 0, 0)
    return (maj, minor + 1, 0)


def _clause_result(version, clause):
    """True/False/None for one AND-clause (whitespace-separated comparators)."""
    tokens = clause.split()
    if not tokens:
        return None
    result = True
    for tok in tokens:
        outcome = _comparator_result(version, tok)
        if outcome is None:
            return None  # indeterminate token -> indeterminate clause (fail open)
        result = result and outcome
    return result


def _comparator_result(version, tok):
    """True/False/None for a single comparator token against a parsed version tuple."""
    tok = tok.strip()
    if not tok:
        return None
    if tok in ("*", "x", "X"):
        return True
    if tok.startswith("^"):
        low = parse_version(tok[1:])
        if low is None:
            return None
        return low <= version < _caret_bounds(low)
    if tok.startswith("~"):
        low = parse_version(tok[1:])
        if low is None:
            return None
        return low <= version < _tilde_bounds(tok, low)
    for op in (">=", "<=", ">", "<", "="):
        if tok.startswith(op):
            target = parse_version(tok[len(op):])
            if target is None:
                return None
            if op == ">=":
                return version >= target
            if op == "<=":
                return version <= target
            if op == ">":
                return version > target
            if op == "<":
                return version < target
            return version == target
    bounds = _xrange_bounds(tok)
    if bounds is not None:
        low, high = bounds
        return version >= low and (high is None or version < high)
    exact = parse_version(tok)
    if exact is not None:
        return version == exact
    return None


def satisfies(version, range_str):
    """Does `version` satisfy npm `range_str`?  True / False / None(=cannot determine).

    None is the FAIL-OPEN signal: an indeterminate range never yields a mismatch
    finding. Supports the bounded subset: exact, ^, ~, >= <= > < =, x-ranges, a
    space-separated AND clause, and '||' OR of such clauses."""
    if not isinstance(range_str, str) or not range_str.strip():
        return None
    ver = parse_version(version)
    if ver is None:
        return None
    if _is_prerelease(version):
        # A prerelease/preview build is channel-uncertain: do NOT let it satisfy a
        # normal stable range as if it were the release (fail open, never a clean pass).
        return None
    clauses = [c for c in range_str.split("||")]
    any_true = False
    all_determinate = True
    for clause in clauses:
        res = _clause_result(ver, clause.strip())
        if res is True:
            any_true = True
        elif res is None:
            all_determinate = False
    if any_true:
        return True
    if all_determinate:
        return False
    return None  # some clause indeterminate, none true -> fail open


# --- classification -----------------------------------------------------------

def classify_surface(surface):
    """Classify a scan surface into one of the four TypeScript-status classes.

    The optional/uninstalled peer and bare-transitive cases resolve to
    'transitive-only' — a lockfile/peer typescript entry is NOT a direct compiler
    surface (the classic false positive). A direct/dev dependency counts as a
    'direct' surface ONLY when it is actually compiled (compiler_invocation)."""
    if not isinstance(surface, dict):
        return CLASS_NONE
    ref = surface.get("typescript_ref") or "none"
    if ref == "none":
        return CLASS_NONE
    if ref == "generated":
        return CLASS_GENERATED
    if ref == "docs_only":
        return CLASS_DOCS
    if ref in ("transitive", "optional_peer"):
        return CLASS_TRANSITIVE
    if ref in ("direct", "dev"):
        inv = surface.get("compiler_invocation")
        if inv is True:
            return CLASS_DIRECT
        if inv is False:
            return CLASS_TRANSITIVE
        # A direct/dev ref with a MISSING compiler_invocation boolean must not
        # fail open to a safe class — a malformed/older scan for a real direct
        # dependency would then skip every direct-surface check. Fail closed.
        return "unknown"
    return "unknown"


# --- removed-option detection -------------------------------------------------

def removed_options(tsconfig_options):
    """Return a list of (option, message) for TS-7.0-removed options that are
    present/reintroduced in a tsconfig options mapping."""
    hits = []
    if not isinstance(tsconfig_options, dict):
        return hits
    target = tsconfig_options.get("target")
    if isinstance(target, str) and target.strip().lower() in _REMOVED_TARGET:
        hits.append(("target", f"target '{target}' was removed in TS 7.0 (no es5 output)"))
    mres = tsconfig_options.get("moduleResolution")
    if isinstance(mres, str) and mres.strip().lower() in _REMOVED_MODULE_RESOLUTION:
        hits.append(("moduleResolution",
                     f"moduleResolution '{mres}' (classic) was removed in TS 7.0"))
    mod = tsconfig_options.get("module")
    if isinstance(mod, str) and mod.strip().lower() in _REMOVED_MODULE:
        hits.append(("module", f"module '{mod}' was removed in TS 7.0"))
    if "baseUrl" in tsconfig_options and tsconfig_options.get("baseUrl") not in (None, ""):
        hits.append(("baseUrl", "baseUrl was removed in TS 7.0 (use paths without baseUrl)"))
    if tsconfig_options.get("esModuleInterop") is False:
        hits.append(("esModuleInterop",
                     "esModuleInterop:false was removed in TS 7.0 (interop is always on)"))
    if tsconfig_options.get("allowSyntheticDefaultImports") is False:
        hits.append(("allowSyntheticDefaultImports",
                     "allowSyntheticDefaultImports:false was removed in TS 7.0"))
    return hits


# --- finding helpers ----------------------------------------------------------

def _finding(path, line, finding_class, level, certainty, message):
    return {"path": path, "line": line, "finding_class": finding_class,
            "level": level, "certainty": certainty, "message": message}


def _relpath(path):
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _line_of(raw_lines, needle):
    """Best-effort 1-based line of `"package_path": "<needle>"` in the raw source."""
    if not raw_lines or not isinstance(needle, str) or not needle:
        return 1
    target = f'"{needle}"'
    for i, text in enumerate(raw_lines):
        if '"package_path"' in text and target in text:
            return i + 1
    return 1


# --- registry helpers ---------------------------------------------------------

def _registry_index(registry):
    """Map (repository, package_path) -> entry for a registry doc. Empty on bad input."""
    index = {}
    if not isinstance(registry, dict):
        return index
    for entry in registry.get("packages", []) or []:
        if isinstance(entry, dict):
            key = (entry.get("repository"), entry.get("package_path"))
            if key[0] and key[1]:
                index[key] = entry
    return index


def _matrix_row(registry, target_version):
    """The support_matrix row that covers target_version, or None.

    A row's target_version may be exact ('7.0.2') OR a range / x-range ('7.x',
    '^7.0.0'); an exact-equality-only lookup would silently skip TSL004 for a ranged
    row (unsupported combo reported clean). Exact match wins; otherwise the first row
    whose range the target satisfies matches."""
    if not isinstance(registry, dict) or not target_version:
        return None
    rows = [r for r in (registry.get("support_matrix", []) or []) if isinstance(r, dict)]
    for row in rows:
        if row.get("target_version") == target_version:
            return row
    for row in rows:
        rt = row.get("target_version")
        if isinstance(rt, str) and satisfies(target_version, rt) is True:
            return row
    return None


# --- core check ---------------------------------------------------------------

def check_scan_obj(rel, scan, registry=None, now=None, max_age_days=DEFAULT_MAX_AGE_DAYS,
                   raw_lines=None):
    """Return a list of finding dicts for one already-parsed scan object.

    registry: parsed registry doc or None. When None, registry-derived checks
    (TSL001/004/006/007) are skipped — they cannot be evaluated without policy."""
    findings = []
    if not isinstance(scan, dict):
        findings.append(_finding(rel, 1, "scan-not-object", "error", "certain",
                                 "top-level value is not a JSON object"))
        return findings

    # inline registry unless an external one was supplied
    if registry is None and isinstance(scan.get("registry"), dict):
        registry = scan["registry"]

    if "surfaces" not in scan:
        # A MISSING surfaces key is malformed, not an empty inventory: a truncated or
        # broken extractor would otherwise be reported clean, masking every surface.
        findings.append(_finding(rel, 1, "surfaces-missing", "error", "certain",
                                 "scan has no 'surfaces' key — a truncated or broken "
                                 "extractor would mask every TypeScript surface"))
        surfaces = []
    else:
        surfaces = scan.get("surfaces")
        if surfaces is not None and not isinstance(surfaces, list):
            findings.append(_finding(rel, 1, "surfaces-not-array", "error", "certain",
                                     "'surfaces' must be an array"))
            surfaces = []
        if not isinstance(surfaces, list):
            surfaces = []

    reg_index = _registry_index(registry)

    for index, surface in enumerate(surfaces):
        findings.extend(_check_surface(rel, index, surface, registry, reg_index, raw_lines))

    # TSL006 — registry-entry staleness (independent of any surface).
    if isinstance(registry, dict):
        findings.extend(_check_registry_staleness(rel, registry, now, max_age_days))

    return findings


def _check_surface(rel, index, surface, registry, reg_index, raw_lines):
    findings = []
    if not isinstance(surface, dict):
        findings.append(_finding(rel, 1, "surface-not-object", "error", "certain",
                                 f"surface[{index}] is not a JSON object"))
        return findings

    repo = surface.get("repository")
    pkg = surface.get("package_path")
    label = f"{repo}:{pkg}" if repo and pkg else f"[index {index}]"
    line = _line_of(raw_lines, pkg) if isinstance(pkg, str) else 1

    for field in ("repository", "package_path", "typescript_ref"):
        if not surface.get(field):
            findings.append(_finding(
                rel, line, "surface-missing-field", "error", "certain",
                f"surface[{index}] missing required field '{field}'"))

    ref = surface.get("typescript_ref")
    if ref is not None and ref not in TS_REFS:
        findings.append(_finding(
            rel, line, "surface-unknown-status", "error", "certain",
            f"surface '{label}' typescript_ref {ref!r} is not one of {list(TS_REFS)}"))

    cls = classify_surface(surface)
    if cls == "unknown":
        # A valid direct/dev ref that cannot classify (missing compiler_invocation) is a
        # structural fail-closed finding. An INVALID ref is already reported above as
        # surface-unknown-status, so don't double-flag it here.
        if ref in ("direct", "dev"):
            findings.append(_finding(
                rel, line, "surface-missing-classification", "error", "certain",
                f"surface '{label}' declares typescript_ref {ref!r} but omits the "
                "compiler_invocation boolean — cannot classify (fail-closed); supply it"))
        return findings
    if cls != CLASS_DIRECT:
        # Non-direct surfaces (transitive-only / docs-only / generated / no-TS) get no
        # compiler-surface drift checks — this is where the optional-uninstalled-peer /
        # transitive false positive is neutralised.
        return findings

    # A direct compiler surface MUST record its lockfile-resolved version; a scan that
    # omits it cannot be proven clean (fail-closed, not silently skipped).
    if not isinstance(surface.get("resolved_version"), str) or not surface.get("resolved_version").strip():
        findings.append(_finding(
            rel, line, "direct-surface-missing-version", "error", "certain",
            f"surface '{label}' is a direct compiler surface without a string resolved_version "
            "— record the lockfile-resolved compiler version (a truncated scan is not clean)"))

    # TSL005 — reintroduced removed compiler options (deterministic).
    for opt, msg in removed_options(surface.get("tsconfig_options")):
        findings.append(_finding(
            rel, line, "removed-compiler-option", "warning", "certain",
            f"surface '{label}': {msg}"))

    # TSL002 — declared range vs resolved version.
    declared = surface.get("declared_version")
    resolved = surface.get("resolved_version")
    if isinstance(declared, str) and isinstance(resolved, str):
        ok = satisfies(resolved, declared)
        if ok is False:
            findings.append(_finding(
                rel, line, "compiler-version-mismatch", "warning", "certain",
                f"surface '{label}': resolved typescript {resolved} does not satisfy "
                f"declared range {declared}"))

    # TSL008 — a resolved PRERELEASE/preview compiler is not a stable target.
    if isinstance(resolved, str) and _is_prerelease(resolved):
        findings.append(_finding(
            rel, line, "preview-compiler-channel", "warning", "probable",
            f"surface '{label}': resolved typescript {resolved} is a prerelease/preview "
            "build — a preview is not a stable release target; verify the release channel"))

    # TSL003 — a direct surface with no CI job that actually runs its compiler.
    ci = surface.get("ci")
    if not isinstance(ci, dict):
        findings.append(_finding(
            rel, line, "direct-surface-missing-typecheck-ci", "warning", "heuristic",
            f"surface '{label}' is a direct compiler surface but the scan carries no CI "
            "signal — a Dependabot 'green' with no tsc/test/build job is VACUOUS; confirm "
            "a job actually runs the compiler"))
    else:
        # Use identity (is True), not bool(): the scan is untyped JSON and a string
        # like "false" is truthy — bool("false") is True. A non-boolean CI signal must
        # not manufacture a false green.
        runs_compiler = (ci.get("typecheck_job") is True) or (ci.get("build_job") is True)
        references = ci.get("references_package")
        # Anti-vacuity rule (§9 of the skill): a green is only proof if a job runs this
        # package's tsc/build AND references THIS package. A missing references_package
        # signal is NOT proof of coverage — treat it as (heuristic) drift, not clean.
        if not runs_compiler or references is not True:
            certainty = "heuristic" if (runs_compiler and references is None) else "probable"
            findings.append(_finding(
                rel, line, "direct-surface-missing-typecheck-ci", "warning", certainty,
                f"surface '{label}' is a direct compiler surface without PROVEN CI coverage "
                "(a job that runs its tsc/build AND references this package): vacuous-green "
                "risk — an upgrade could go green without ever compiling it"))

    # registry-derived checks (need policy).
    if isinstance(registry, dict):
        entry = reg_index.get((repo, pkg))
        if entry is None:
            findings.append(_finding(
                rel, line, "direct-surface-unregistered", "warning", "certain",
                f"surface '{label}' is a direct compiler surface with no entry in the "
                "supplied registry — every direct surface must be tracked"))
        else:
            # Classification drift: the scan now sees a direct compiler surface while the
            # registry still records it as non-direct — exactly the stale classification the
            # registry exists to catch (versions alone would report clean).
            reg_status = entry.get("typescript_status")
            if isinstance(reg_status, str) and reg_status != cls:
                findings.append(_finding(
                    rel, line, "registry-classification-mismatch", "warning", "certain",
                    f"surface '{label}' is classified '{cls}' by the scan but the registry "
                    f"records typescript_status '{reg_status}' — stale classification, re-verify"))
            reg_resolved = entry.get("resolved_version")
            sv, rv = parse_version(resolved), parse_version(reg_resolved)
            if sv is not None and rv is not None:
                if sv < rv:
                    findings.append(_finding(
                        rel, line, "resolved-version-regression", "warning", "certain",
                        f"surface '{label}': observed typescript {resolved} is LOWER than the "
                        f"registry's recorded {reg_resolved} (regression)"))
                elif sv > rv:
                    # Forward drift: an unreviewed upgrade past the approved registry fact.
                    # The runbook requires re-verification when a lockfile moves; a broad
                    # manifest range can slide the resolved version up silently.
                    findings.append(_finding(
                        rel, line, "resolved-version-forward-drift", "warning", "certain",
                        f"surface '{label}': observed typescript {resolved} is HIGHER than the "
                        f"registry's recorded {reg_resolved} — an unreviewed upgrade; the "
                        "approved registry fact is stale, re-verify"))
                elif (isinstance(resolved, str) and isinstance(reg_resolved, str)
                      and resolved.strip() != reg_resolved.strip()):
                    # Same numeric (maj,min,patch) but different raw string — a prerelease vs
                    # the stable release (7.0.0-beta.1 -> 7.0.0). parse_version drops the suffix,
                    # so guard the channel/prerelease move explicitly: it needs re-verification.
                    findings.append(_finding(
                        rel, line, "resolved-version-forward-drift", "warning", "certain",
                        f"surface '{label}': observed typescript {resolved} differs from the "
                        f"registry's recorded {reg_resolved} at the same numeric version "
                        "(prerelease/channel change) — re-verify"))

        row = _matrix_row(registry, surface.get("target_version"))
        if row is not None:
            node_range = row.get("supported_node_range")
            if isinstance(node_range, str) and satisfies(surface.get("node_version"), node_range) is False:
                findings.append(_finding(
                    rel, line, "unsupported-node-ts-combo", "warning", "certain",
                    f"surface '{label}': node {surface.get('node_version')} is outside the "
                    f"declared supported range {node_range} for target {surface.get('target_version')}"))
            ts_range = row.get("supported_ts_range")
            if isinstance(ts_range, str) and satisfies(resolved, ts_range) is False:
                findings.append(_finding(
                    rel, line, "unsupported-node-ts-combo", "warning", "certain",
                    f"surface '{label}': typescript {resolved} is outside the declared "
                    f"supported range {ts_range} for target {surface.get('target_version')}"))

    return findings


def _parse_dt(raw):
    """Parse an RFC 3339 / ISO 8601 timestamp to an aware datetime, or None."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _check_registry_staleness(rel, registry, now, max_age_days):
    findings = []
    if now is None:
        now = datetime.now(timezone.utc)
    now_dt = _parse_dt(now) if isinstance(now, str) else now
    if now_dt is None:
        now_dt = datetime.now(timezone.utc)
    for entry in registry.get("packages", []) or []:
        if not isinstance(entry, dict):
            continue
        label = f"{entry.get('repository')}:{entry.get('package_path')}"
        last = _parse_dt(entry.get("last_verified_at"))
        if last is None:
            # A missing/unparsable timestamp cannot prove freshness — the schema requires
            # it and the re-verification trigger relies on it. Fail closed, don't skip.
            findings.append(_finding(
                rel, 1, "registry-entry-stale", "warning", "certain",
                f"registry entry '{label}' has a missing or unparsable last_verified_at — "
                "cannot prove freshness (fail-closed); re-verify and record a timestamp"))
            continue
        age_days = (now_dt - last).total_seconds() / 86400.0
        if age_days > max_age_days:
            findings.append(_finding(
                rel, 1, "registry-entry-stale", "warning", "certain",
                f"registry entry '{label}' last_verified_at is {age_days:.0f} days old "
                f"(> {max_age_days}d window) — re-verify against live state"))
    return findings


# --- templates ----------------------------------------------------------------

def _template_registry():
    return {
        "schema": "typescript-lifecycle-registry/v1",
        "canonical": False,
        "generated_note": "Generated operational state, not canon. A green entry is "
                          "only as strong as its evidence + certainty.",
        "support_matrix": [
            {"target_version": "7.0.2", "supported_node_range": ">=20.0.0",
             "supported_ts_range": "^7.0.0", "note": "example row — replace with a primary-source range"}
        ],
        "packages": [
            {
                "repository": "example-org/example-repo",
                "package_path": "packages/worker",
                "default_branch_sha": "0" * 40,
                "typescript_status": "direct",
                "declared_version": "^7.0.0",
                "resolved_version": "7.0.2",
                "target_version": "7.0.2",
                "release_channel": "stable",
                "node_version": "22.11.0",
                "package_manager": "npm",
                "framework": None,
                "build_tool": "tsc",
                "test_runner": "vitest",
                "migration_class": "A-direct-upgrade",
                "baseline_status": "pass",
                "compatibility_status": "compatible",
                "blocking_dependencies": [],
                "last_verified_at": "2026-07-11T00:00:00+00:00",
                "evidence": ["PR #0000", "npm dist-tags typescript@latest"],
                "certainty": "verified",
            }
        ],
    }


def _template_scan():
    return {
        "schema": "typescript-workspace-scan/v1",
        "canonical": False,
        "generated_note": "Generated observation of TypeScript surfaces. Facts only "
                          "(versions, tsconfig option values, boolean CI signals) — no source.",
        "surfaces": [
            {
                "repository": "example-org/example-repo",
                "package_path": "packages/worker",
                "typescript_ref": "direct",
                "compiler_invocation": True,
                "declared_version": "^7.0.0",
                "resolved_version": "7.0.2",
                "target_version": "7.0.2",
                "node_version": "22.11.0",
                "tsconfig_options": {"target": "es2022", "module": "esnext",
                                     "moduleResolution": "bundler"},
                "ci": {"typecheck_job": True, "build_job": True, "test_job": True,
                       "references_package": True},
            },
            {
                "repository": "example-org/example-repo",
                "package_path": "tools/visual-render",
                "typescript_ref": "optional_peer",
                "compiler_invocation": False,
                "declared_version": None,
                "resolved_version": None,
                "target_version": None,
                "node_version": "22.11.0",
                "tsconfig_options": {},
                "ci": {"typecheck_job": False, "build_job": False, "references_package": False},
            },
        ],
    }


# --- self-test ----------------------------------------------------------------

def _self_test_cases():
    """(name, scan, registry, expected_finding_classes). The templates are the clean
    baseline; each case mutates a copy to trigger exactly the expected class(es)."""
    reg = _template_registry()
    scan = _template_scan()
    # register the direct surface so the clean baseline is truly clean
    fresh_now = "2026-07-11T00:00:00+00:00"

    unregistered = copy.deepcopy(scan)
    empty_reg = {"schema": "typescript-lifecycle-registry/v1", "canonical": False,
                 "generated_note": "x", "packages": []}

    mismatch = copy.deepcopy(scan)
    mismatch["surfaces"][0]["declared_version"] = "^6.0.0"
    mismatch["surfaces"][0]["resolved_version"] = "7.0.2"

    no_ci = copy.deepcopy(scan)
    no_ci["surfaces"][0]["ci"] = {"typecheck_job": False, "build_job": False,
                                  "references_package": False}

    removed = copy.deepcopy(scan)
    removed["surfaces"][0]["tsconfig_options"] = {"target": "es5", "baseUrl": "./src"}

    regression = copy.deepcopy(scan)
    # lower than the registry's recorded 7.0.2, but still satisfies ^7.0.0 and the
    # matrix ^7.0.0 range, so ONLY the regression class fires (isolated case).
    regression["surfaces"][0]["resolved_version"] = "7.0.1"

    bad_node = copy.deepcopy(scan)
    bad_node["surfaces"][0]["node_version"] = "18.0.0"  # outside >=20

    unknown_ref = copy.deepcopy(scan)
    unknown_ref["surfaces"][0]["typescript_ref"] = "peerish"

    optional_peer_only = copy.deepcopy(scan)
    optional_peer_only["surfaces"] = [optional_peer_only["surfaces"][1]]  # the peer

    stale_reg = copy.deepcopy(reg)
    stale_reg["packages"][0]["last_verified_at"] = "2020-01-01T00:00:00+00:00"

    # --- fail-closed regression locks (Codex round 1, PR #1489) ---
    # a direct ref with a MISSING compiler_invocation must fail closed, not downgrade.
    missing_inv = copy.deepcopy(scan)
    del missing_inv["surfaces"][0]["compiler_invocation"]

    # a docs-only surface is a first-class non-direct class (no drift checks, no
    # surface-unknown-status).
    docs_only = copy.deepcopy(scan)
    docs_only["surfaces"][0]["typescript_ref"] = "docs_only"

    # a resolved version HIGHER than the registry is unreviewed forward drift.
    forward = copy.deepcopy(scan)
    forward["surfaces"][0]["resolved_version"] = "7.1.0"

    # a resolved PRERELEASE/preview build is not a stable target (registry=None to
    # isolate the channel finding from any registry-derived check).
    preview = copy.deepcopy(scan)
    preview["surfaces"][0]["resolved_version"] = "7.0.0-beta.1"

    # a typecheck job that does NOT reference this package is vacuous (no proof).
    no_ref = copy.deepcopy(scan)
    no_ref["surfaces"][0]["ci"] = {"typecheck_job": True, "build_job": False}

    # a RANGED support_matrix target_version ('7.x') must still match target 7.0.2.
    range_matrix_reg = copy.deepcopy(reg)
    range_matrix_reg["support_matrix"][0]["target_version"] = "7.x"
    range_scan = copy.deepcopy(scan)
    range_scan["surfaces"][0]["node_version"] = "18.0.0"

    # --- fail-closed regression locks (Codex review round 2, PR #1489) ---
    missing_ver = copy.deepcopy(scan)
    del missing_ver["surfaces"][0]["resolved_version"]
    str_ci = copy.deepcopy(scan)
    str_ci["surfaces"][0]["ci"] = {"typecheck_job": "false", "references_package": True}
    missing_ref = copy.deepcopy(scan)
    del missing_ref["surfaces"][0]["typescript_ref"]
    no_ts_reg = copy.deepcopy(reg)
    del no_ts_reg["packages"][0]["last_verified_at"]
    misclass_reg = copy.deepcopy(reg)
    misclass_reg["packages"][0]["typescript_status"] = "no-typescript"
    pre_reg = copy.deepcopy(reg)
    pre_reg["packages"][0]["resolved_version"] = "7.0.0-beta.1"
    pre_scan = copy.deepcopy(scan)
    pre_scan["surfaces"][0]["resolved_version"] = "7.0.0"

    return [
        # clean baseline: direct surface registered, fresh registry, no bad config.
        ("clean", scan, reg, []),
        ("unregistered", unregistered, empty_reg, ["direct-surface-unregistered"]),
        ("mismatch", mismatch, reg, ["compiler-version-mismatch"]),
        ("no-ci", no_ci, reg, ["direct-surface-missing-typecheck-ci"]),
        ("removed-option", removed, reg,
         ["removed-compiler-option"]),
        ("regression", regression, reg, ["resolved-version-regression"]),
        ("bad-node", bad_node, reg, ["unsupported-node-ts-combo"]),
        ("unknown-ref", unknown_ref, reg, ["surface-unknown-status"]),
        # an optional-uninstalled-peer-only workspace is CLEAN (the false positive
        # is neutralised: a peer/transitive entry is not a direct compiler surface).
        ("optional-peer-only", optional_peer_only, empty_reg, []),
        ("stale-registry", scan, stale_reg, ["registry-entry-stale"]),
        ("missing-compiler-invocation", missing_inv, reg, ["surface-missing-classification"]),
        ("docs-only", docs_only, reg, []),
        ("surfaces-missing", {}, reg, ["surfaces-missing"]),
        ("forward-drift", forward, reg, ["resolved-version-forward-drift"]),
        ("preview-channel", preview, None, ["preview-compiler-channel"]),
        ("typecheck-without-references", no_ref, reg, ["direct-surface-missing-typecheck-ci"]),
        ("ranged-matrix-row", range_scan, range_matrix_reg, ["unsupported-node-ts-combo"]),
        ("missing-direct-version", missing_ver, reg, ["direct-surface-missing-version"]),
        ("string-ci-bool", str_ci, reg, ["direct-surface-missing-typecheck-ci"]),
        ("missing-typescript-ref", missing_ref, reg, ["surface-missing-field"]),
        ("missing-timestamp", scan, no_ts_reg, ["registry-entry-stale"]),
        ("classification-mismatch", scan, misclass_reg, ["registry-classification-mismatch"]),
        ("prerelease-registry-compare", pre_scan, pre_reg, ["resolved-version-forward-drift"]),
    ], fresh_now


def _run_self_test():
    cases, fresh_now = _self_test_cases()
    failures = []
    for idx, (name, scan, registry, expected) in enumerate(cases):
        got = sorted({f["finding_class"]
                      for f in check_scan_obj(name, scan, registry, now=fresh_now)})
        want = sorted(set(expected))
        if got != want:
            failures.append(f"case {idx} ({name}): expected {want}, got {got}")
    # certainty labels must always be in the fixed vocabulary
    for name, scan, registry, _ in cases:
        for f in check_scan_obj(name, scan, registry, now=fresh_now):
            if f["certainty"] not in CERTAINTY_LEVELS:
                failures.append(f"case ({name}): bad certainty {f['certainty']!r}")
    # version helper spot-checks
    version_checks = [
        (satisfies("7.0.2", "^7.0.0"), True),
        (satisfies("7.0.2", "^6.0.0"), False),
        (satisfies("6.5.0", "~6.5.0"), True),
        (satisfies("6.6.0", "~6.5.0"), False),
        (satisfies("7.0.2", ">=6.0.0 <8.0.0"), True),
        (satisfies("6.5.0", "6.x || 7.x"), True),
        (satisfies("5.0.0", "6.x || 7.x"), False),
        (satisfies("7.0.2", "next"), None),         # unparseable -> fail open
        (satisfies("7.0.2", "workspace:*"), None),  # unparseable -> fail open
        (satisfies("7.0.0-beta.1", "^7.0.0"), None),  # prerelease never a clean stable pass
        (satisfies("7.0.2", "7.x"), True),          # x-range matches
    ]
    for idx, (got, want) in enumerate(version_checks):
        if got != want:
            failures.append(f"version check {idx}: expected {want}, got {got}")
    if failures:
        for f in failures:
            print(f"SELF-TEST FAIL: {f}", file=sys.stderr)
        return 1
    print(f"typescript_lifecycle_drift: self-test ok ({len(cases)} cases)")
    return 0


# --- file loading -------------------------------------------------------------

def _load_json(path):
    """Read + parse one JSON file. Returns (data, raw_lines, error_finding_or_None)."""
    rel = _relpath(path)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, None, _finding(rel, 1, "scan-read-error", "error", "certain",
                                    f"cannot read file ({exc})")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, None, _finding(rel, getattr(exc, "lineno", 1) or 1,
                                    "scan-read-error", "error", "certain",
                                    f"invalid JSON ({exc.msg})")
    return data, raw.split("\n"), None


# --- cli ----------------------------------------------------------------------

def _emit_error(json_mode, msg):
    if json_mode:
        print(json.dumps({"summary": {"scanned": 0, "findings": 0}, "findings": [],
                          "error": msg}))
    else:
        print(msg, file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scan", metavar="FILE",
                        help="workspace-scan JSON file to analyse")
    parser.add_argument("--registry", metavar="FILE",
                        help="registry JSON file (overrides an inline scan['registry'])")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS,
                        help=f"registry staleness window in days (default {DEFAULT_MAX_AGE_DAYS})")
    parser.add_argument("--now", metavar="ISO8601",
                        help="reference 'now' for staleness (default: current UTC); "
                             "supply for deterministic runs")
    parser.add_argument("--json", action="store_true",
                        help="emit a single JSON object to stdout")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 on any finding (opt-in; default advisory / exit 0)")
    parser.add_argument("--self-test", action="store_true",
                        help="run built-in fixtures and exit (0 pass, 1 fail)")
    parser.add_argument("--emit-template", action="store_true",
                        help="print a minimal valid scan + registry skeleton and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return _run_self_test()

    if args.emit_template:
        print(json.dumps({"scan": _template_scan(), "registry": _template_registry()},
                         indent=2))
        return 0

    if not args.scan:
        _emit_error(args.json, "typescript_lifecycle_drift: --scan is required "
                    "(or use --self-test / --emit-template)")
        return 2

    scan, raw_lines, err = _load_json(args.scan)
    if err is not None:
        if args.json:
            print(json.dumps({"summary": {"scanned": 0, "findings": 1},
                              "findings": [err]}, indent=2))
        else:
            print(f"  [{err['level']}] {err['finding_class']}  {err['path']}:{err['line']}: "
                  f"{err['message']}", file=sys.stderr)
        return 2

    registry = None
    if args.registry:
        registry, _, rerr = _load_json(args.registry)
        if rerr is not None:
            _emit_error(args.json, f"typescript_lifecycle_drift: registry {rerr['message']}")
            return 2

    rel = _relpath(args.scan)
    findings = check_scan_obj(rel, scan, registry, now=args.now,
                              max_age_days=args.max_age_days, raw_lines=raw_lines)

    if args.json:
        print(json.dumps({
            "summary": {"scanned": 1, "findings": len(findings),
                        "registry_supplied": bool(registry) or isinstance(scan, dict)
                        and isinstance(scan.get("registry"), dict)},
            "findings": findings,
        }, indent=2))
    else:
        print(f"typescript_lifecycle_drift: scanned {rel} [advisory]")
        for f in findings:
            print(f"  [{f['level']}/{f['certainty']}] {f['finding_class']}  "
                  f"{f['path']}:{f['line']}: {f['message']}")
        if findings:
            print(f"typescript_lifecycle_drift: {len(findings)} advisory finding(s) "
                  "(not a gate)")
        else:
            print("typescript_lifecycle_drift: ok (0 findings)")

    if args.strict and findings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
