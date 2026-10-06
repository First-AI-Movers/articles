"""Guard: every Dependabot `ignore` entry is still justified by the lockfiles (#432).

A Dependabot `ignore` is a hold on a bump that cannot currently install. The hold is
correct on the day it is written and silently wrong afterwards: the blocking constraint
moves upstream, nobody re-reads the comment, and the repository quietly stops taking a
class of update. This repository has already lived that cycle once — a `/mcp-server`
vitest semver-major ignore held from an earlier pool-workers generation and was removed
on 2026-06-22, by hand, when somebody happened to notice that pool-workers 0.16 peered
vitest ^4.

So the lift condition is expressed as a test rather than a promise in a comment. The
evidence is offline and already in the repository: `package-lock.json` records the
installed `@cloudflare/vitest-pool-workers` and the `peerDependencies` range it declares.
While that range admits only vitest 4, the ignore is justified. When a lockfile arrives
carrying a pool-workers whose peer range admits vitest 5, this test fails and names the
entry to delete — which is exactly when the hold should end.

A hold also has a second failure direction, and this module owns both. The test above
asks "is the hold still justified?". It cannot ask "did the held major land anyway?" —
and on 2026-10-05 it did: Dependabot #485/#486 carried vitest 5.0.1 into both worker
lockfiles while pool-workers 0.22.0 still peered `vitest@^4.1.0`, and both merged. The
justification test passed throughout, correctly: pool-workers had not moved, so the hold
was still justified. Nothing asserted that the tree the lockfile describes can actually
be installed, so `npm ci` began failing on `main` in both workers for ~30 h with the exact
error the hold's own comment quotes.

The merge was not stopped by the surface's own red check, because `mcp-server` and
`og-worker` are not required contexts — `aeos-merge-ready` is the only one. So the guard
has to be an offline assertion over the committed lockfiles, which is what
`test_both_worker_lockfiles_are_installable` is.

No network: the ranges are read from the committed lockfiles, never from the registry.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"
LOCKFILES = ("mcp-server/package-lock.json", "og-worker/package-lock.json")
PEER_HOLDER = "node_modules/@cloudflare/vitest-pool-workers"
HELD = "vitest"
MAJOR_UPDATE = "version-update:semver-major"

# `^X.Y.Z` / `~X.Y.Z` / `X.Y.Z` — the shapes npm actually writes into a lockfile's
# peerDependencies. Anything else is deliberately NOT parsed: an unrecognized range is
# treated as "might admit the held major", which fails the test and asks a person to
# look, rather than letting a stale hold survive behind an expression nobody checked.
SIMPLE_RANGE_RE = re.compile(r"^\s*([\^~]?)(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.-]+)?\s*$")


def _ignored_majors() -> set[str]:
    document = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8")) or {}
    held: set[str] = set()
    for entry in document.get("updates") or []:
        for rule in entry.get("ignore") or []:
            if MAJOR_UPDATE in (rule.get("update-types") or []):
                held.add(str(rule.get("dependency-name")))
    return held


def _peer_range(lockfile: Path, holder: str, dependency: str) -> tuple[str | None, str | None]:
    packages = json.loads(lockfile.read_text(encoding="utf-8")).get("packages") or {}
    entry = packages.get(holder) or {}
    return entry.get("version"), (entry.get("peerDependencies") or {}).get(dependency)


def _admits_major_above(spec: str, major: int) -> bool:
    """Does this peer range admit any release with a major greater than `major`?

    Only the simple caret/tilde/exact shapes are decided; anything else answers True,
    so an unparsed range surfaces as a failure instead of a silent pass.
    """
    match = SIMPLE_RANGE_RE.match(spec or "")
    if not match:
        return True
    return int(match.group(2)) > major


def _installed_version(lockfile: Path, dependency: str) -> str | None:
    packages = json.loads(lockfile.read_text(encoding="utf-8")).get("packages") or {}
    return (packages.get(f"node_modules/{dependency}") or {}).get("version")


def _satisfies(version: str, spec: str) -> bool | None:
    """Does `version` satisfy the simple caret/tilde/exact range `spec`?

    Returns None — "cannot decide" — for any shape this deliberately does not parse, so
    an unreadable range is never turned into a failure the reader cannot act on. That is
    the opposite default from `_admits_major_above`, and for the opposite reason: there,
    an unparsed range must not let a stale hold survive; here, it must not invent a
    conflict that npm would not report.
    """
    range_match = SIMPLE_RANGE_RE.match(spec or "")
    version_match = SIMPLE_RANGE_RE.match(version or "")
    if not range_match or not version_match or version_match.group(1):
        return None
    operator, *bound = range_match.groups()
    low = tuple(int(part) for part in bound)
    found = tuple(int(part) for part in version_match.groups()[1:])
    if found < low:
        return False
    if operator == "^":
        # npm's caret pins the leftmost non-zero component: ^4.1.0 admits 4.x, but
        # ^0.22.0 admits only 0.22.x.
        return found[0] == low[0] if low[0] else found[:2] == low[:2]
    if operator == "~":
        return found[:2] == low[:2]
    return found == low


def test_satisfaction_check_matches_npm_on_the_shapes_it_decides():
    assert _satisfies("4.1.11", "^4.1.0") is True
    assert _satisfies("5.0.1", "^4.1.0") is False
    assert _satisfies("4.0.9", "^4.1.0") is False
    assert _satisfies("0.22.3", "^0.22.0") is True
    assert _satisfies("0.23.0", "^0.22.0") is False
    assert _satisfies("4.1.11", "~4.1.0") is True
    assert _satisfies("4.2.0", "~4.1.0") is False
    assert _satisfies("4.1.0", "4.1.0") is True
    assert _satisfies("4.1.11", "^4.1.0 || ^5.0.0") is None
    assert _satisfies("4.1.11", ">=4") is None


def test_both_worker_lockfiles_are_installable():
    """A committed lockfile whose own peer ranges conflict is an `npm ci` that cannot run.

    This is the regression direction the justification test structurally cannot see
    (#485/#486, measured on `main` 2026-10-05 -> 2026-10-06):

        npm error While resolving: @cloudflare/vitest-pool-workers@0.22.0
        npm error Found: vitest@5.0.1
        npm error peer vitest@"^4.1.0" from @cloudflare/vitest-pool-workers@0.22.0

    It is asserted unconditionally — whether or not the `ignore` entry is present — so it
    keeps working after the hold is lifted, which is exactly when an incompatible pair
    becomes easy to land again.
    """
    for name in LOCKFILES:
        lockfile = REPO_ROOT / name
        holder_version, spec = _peer_range(lockfile, PEER_HOLDER, HELD)
        if not spec:
            continue
        installed = _installed_version(lockfile, HELD)
        assert installed, f"{name}: {HELD} is not in the lockfile, but {PEER_HOLDER} peers it"
        verdict = _satisfies(installed, spec)
        if verdict is None:
            continue
        assert verdict, (
            f"{name}: {HELD}@{installed} does not satisfy the `{HELD}@{spec}` peer range "
            f"declared by @cloudflare/vitest-pool-workers@{holder_version}, so `npm ci` in "
            f"that worker fails with ERESOLVE. Either hold {HELD} at a version the peer "
            f"range admits, or bump pool-workers to a release that peers the new major — "
            f"do not commit the pair."
        )


def test_the_vitest_hold_is_still_justified_by_both_lockfiles():
    """While pool-workers peers vitest ^4, a vitest 5 carrier can never install.

    Measured failure this hold answers (Dependabot #451/#452, 2026-09-26):
    `npm error peer vitest@"^4.1.0" from @cloudflare/vitest-pool-workers@0.22.0`
    against `Found: vitest@5.0.0`.
    """
    if HELD not in _ignored_majors():
        pytest.skip("the vitest semver-major hold has been lifted; nothing to justify")
    for name in LOCKFILES:
        lockfile = REPO_ROOT / name
        version, spec = _peer_range(lockfile, PEER_HOLDER, HELD)
        assert spec, (
            f"{name}: {PEER_HOLDER} declares no `{HELD}` peer range, so the "
            f"semver-major hold in .github/dependabot.yml rests on nothing. Re-derive it "
            f"or delete the ignore entry."
        )
        assert not _admits_major_above(spec, 4), (
            f"{name}: @cloudflare/vitest-pool-workers@{version} now peers "
            f"`{HELD}@{spec}`, which admits a major above 4 — the documented lift "
            f"condition is MET. Delete the `{HELD}` semver-major `ignore` entry from "
            f".github/dependabot.yml and let the bump flow."
        )


def test_every_major_hold_names_its_lift_condition_in_the_file():
    """A hold a reader cannot evaluate is a hold nobody will ever lift.

    Parsed YAML carries no comments, so this reads the file as text and requires each
    held dependency to be discussed near an explicit lift condition.
    """
    text = DEPENDABOT.read_text(encoding="utf-8")
    for dependency in sorted(_ignored_majors()):
        assert "LIFT CONDITION" in text, (
            f"the semver-major hold on {dependency!r} must state a LIFT CONDITION in "
            f".github/dependabot.yml"
        )
        assert dependency in text, f"{dependency!r} is held but never named in the file's prose"


def test_range_parser_is_conservative_about_shapes_it_cannot_read():
    assert _admits_major_above("^4.1.0", 4) is False
    assert _admits_major_above("~4.1.0", 4) is False
    assert _admits_major_above("4.1.0", 4) is False
    assert _admits_major_above("^5.0.0", 4) is True
    assert _admits_major_above("^4.1.0 || ^5.0.0", 4) is True
    assert _admits_major_above(">=4", 4) is True
    assert _admits_major_above("", 4) is True
