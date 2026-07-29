#!/usr/bin/env python3
"""Active-default Python drift guard.

`.python-version` is this repository's single source of truth for the Python
runtime. This guard fails when an *active selector* re-introduces a retired
default (3.11 / 3.12 / 3.13) or bypasses that declaration.

Three lanes, each scoped to a surface where a version string is executable
configuration rather than prose:

* ``workflow-selector`` — every ``actions/setup-python`` step, in this
  repository and in the cookiecutter template it ships, must read
  ``python-version-file: .python-version`` and must not pin ``python-version``.
* ``retired-literal`` — no retired version literal in dependency manifests,
  tool sources, or CI config.
* ``contributor-directive`` — no contributor-facing instruction telling a human
  to install or use a retired version.

Deliberately **not** scanned: ``articles/``, ``summaries/``, ``translations/``
and other prose. An article that discusses Python 3.11 is content, not a
runtime selector, and must never fail this guard.

Allowed, because the operator's adoption contract permits them:

* historical evidence — ``docs/CHANGELOG.md`` and ``docs/decisions/`` record
  what the default used to be;
* dependency release-note text, and any line carrying an explicit
  ``py-runtime-allow: <reason>`` pragma;
* a named, bounded rollback lane carrying
  ``py-runtime-rollback: owner=<who> expiry=<YYYY-MM-DD>`` — an *expired*
  rollback is a violation, so the exception cannot become permanent.

Usage:
    python3 tools/check_python_runtime_drift.py [--json] [--repo-root PATH]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

CANONICAL_DECLARATION = ".python-version"
RETIRED_SERIES = ("3.11", "3.12", "3.13")

# Surfaces where a Python version string is executable configuration.
WORKFLOW_GLOBS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "cookiecutter-archive-template/*/.github/workflows/*.yml",
    "cookiecutter-archive-template/*/.github/workflows/*.yaml",
)
LITERAL_GLOBS = (
    ".github/*.yml",
    ".github/workflows/*.yml",
    "cookiecutter-archive-template/*/.github/workflows/*.yml",
    "tools/*.py",
    "tools/*.txt",
    "tools/*.cfg",
    "tools/*.toml",
)
DIRECTIVE_FILES = ("CONTRIBUTING.md", "README.md")
DIRECTIVE_GLOBS = ("docs/*.md", "docs/*/*.md")

# Historical-evidence surfaces: they legitimately name the retired default.
EVIDENCE_PREFIXES = ("docs/CHANGELOG.md", "docs/decisions/")

ALLOW_PRAGMA = re.compile(r"py-runtime-allow:\s*(?P<reason>\S.*?)\s*(?:-->|$)")
ROLLBACK_PRAGMA = re.compile(
    r"py-runtime-rollback:\s*owner=(?P<owner>[^\s]+)\s+expiry=(?P<expiry>\d{4}-\d{2}-\d{2})"
)

# A retired version acting as a selector, not merely mentioned in a sentence.
LITERAL_SELECTOR = re.compile(
    r"""(?:
          python-version:\s*['"]?3\.(?:11|12|13)\b
        | python_requires\s*=\s*['"]?[><=~!]*\s*3\.(?:11|12|13)\b
        | requires-python\s*=\s*['"][^'"]*3\.(?:11|12|13)\b
        | \bpython3\.(?:11|12|13)\b
        | \bpy3(?:11|12|13)\b
    )""",
    re.VERBOSE,
)
# Contributor-facing imperative naming a retired series.
DIRECTIVE = re.compile(
    r"(?:install|use|require[sd]?|need[s]?|create|activate|must\s+be|running)"
    r"[^.\n]{0,60}?(?:python\s*)?3\.(?:11|12|13)\b",
    re.IGNORECASE,
)


class Finding:
    def __init__(self, lane: str, path: str, line: int, text: str, detail: str) -> None:
        self.lane = lane
        self.path = path
        self.line = line
        self.text = text.strip()
        self.detail = detail

    def as_dict(self) -> dict:
        return {
            "lane": self.lane,
            "path": self.path,
            "line": self.line,
            "text": self.text,
            "detail": self.detail,
        }

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.lane}] {self.detail}\n    {self.text}"


def _is_evidence(rel: str) -> bool:
    return any(rel == p or rel.startswith(p) for p in EVIDENCE_PREFIXES)


def _exempt(lines: list[str], index: int, today: dt.date) -> tuple[bool, str | None]:
    """Return (exempt, error) for the pragma governing ``lines[index]``.

    The pragma may sit on the offending line or the line directly above it.
    An expired rollback is not an exemption — it is its own error.
    """
    window = [lines[index]]
    if index > 0:
        window.append(lines[index - 1])

    for candidate in window:
        rollback = ROLLBACK_PRAGMA.search(candidate)
        if rollback:
            expiry = dt.date.fromisoformat(rollback.group("expiry"))
            if expiry < today:
                return False, (
                    f"rollback lane expired {expiry.isoformat()} "
                    f"(owner {rollback.group('owner')}) — remove it or renew the expiry"
                )
            return True, None
        if ALLOW_PRAGMA.search(candidate):
            return True, None
    return False, None


def _iter(repo_root: Path, globs: tuple[str, ...]):
    seen: set[Path] = set()
    for pattern in globs:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def check(repo_root: Path, today: dt.date | None = None) -> list[Finding]:
    today = today or dt.date.today()
    findings: list[Finding] = []

    declaration = repo_root / CANONICAL_DECLARATION
    if not declaration.is_file():
        findings.append(
            Finding(
                "declaration",
                CANONICAL_DECLARATION,
                0,
                "",
                "the canonical Python declaration is missing",
            )
        )
        return findings

    declared = declaration.read_text(encoding="utf-8").strip()

    # Lane 1: workflow selectors must read the declaration.
    try:
        import yaml
    except ImportError:  # pragma: no cover - PyYAML is a pinned requirement
        findings.append(
            Finding(
                "workflow-selector",
                CANONICAL_DECLARATION,
                0,
                "",
                "PyYAML is required to verify workflow selectors; refusing to pass vacuously",
            )
        )
        return findings

    for path in _iter(repo_root, WORKFLOW_GLOBS):
        rel = path.relative_to(repo_root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        try:
            document = yaml.safe_load("\n".join(lines)) or {}
        except yaml.YAMLError as exc:
            findings.append(Finding("workflow-selector", rel, 0, "", f"unparseable: {exc}"))
            continue

        for job in (document.get("jobs") or {}).values():
            for step in job.get("steps") or []:
                uses = str(step.get("uses", ""))
                if not uses.startswith("actions/setup-python"):
                    continue
                selector = step.get("with") or {}
                if "python-version" in selector:
                    line = next(
                        (i + 1 for i, l in enumerate(lines) if "python-version:" in l),
                        0,
                    )
                    findings.append(
                        Finding(
                            "workflow-selector",
                            rel,
                            line,
                            f"python-version: {selector['python-version']!r}",
                            "pins python-version inline instead of reading "
                            f"{CANONICAL_DECLARATION}",
                        )
                    )
                if selector.get("python-version-file") != CANONICAL_DECLARATION:
                    findings.append(
                        Finding(
                            "workflow-selector",
                            rel,
                            0,
                            f"{uses}",
                            "does not read "
                            f"python-version-file: {CANONICAL_DECLARATION} "
                            f"(got {selector.get('python-version-file')!r})",
                        )
                    )

    # Lane 2: retired literals in executable configuration.
    for path in _iter(repo_root, LITERAL_GLOBS):
        rel = path.relative_to(repo_root).as_posix()
        if rel == f"tools/{Path(__file__).name}" or _is_evidence(rel):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            if not LITERAL_SELECTOR.search(line):
                continue
            exempt, error = _exempt(lines, index, today)
            if error:
                findings.append(Finding("retired-literal", rel, index + 1, line, error))
            elif not exempt:
                findings.append(
                    Finding(
                        "retired-literal",
                        rel,
                        index + 1,
                        line,
                        f"retired Python default acting as a selector; declared is {declared}",
                    )
                )

    # Lane 3: contributor-facing directives, in the root guides and in docs/.
    # Historical evidence (docs/CHANGELOG.md, docs/decisions/) is exempt by path:
    # a decision record naming the retired default is a record, not a directive.
    directive_paths = [
        repo_root / name for name in DIRECTIVE_FILES if (repo_root / name).is_file()
    ]
    directive_paths.extend(_iter(repo_root, DIRECTIVE_GLOBS))

    for path in directive_paths:
        rel = path.relative_to(repo_root).as_posix()
        if _is_evidence(rel):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            if not DIRECTIVE.search(line):
                continue
            exempt, error = _exempt(lines, index, today)
            if error:
                findings.append(Finding("contributor-directive", rel, index + 1, line, error))
            elif not exempt:
                findings.append(
                    Finding(
                        "contributor-directive",
                        rel,
                        index + 1,
                        line,
                        f"directs a contributor to a retired Python default; declared is {declared}",
                    )
                )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[1]
    )
    findings = check(repo_root)

    if args.as_json:
        print(
            json.dumps(
                {
                    "declared": (repo_root / CANONICAL_DECLARATION).read_text(
                        encoding="utf-8"
                    ).strip()
                    if (repo_root / CANONICAL_DECLARATION).is_file()
                    else None,
                    "retired_series": list(RETIRED_SERIES),
                    "finding_count": len(findings),
                    "findings": [f.as_dict() for f in findings],
                },
                indent=2,
            )
        )
    elif findings:
        print(f"Python runtime drift: {len(findings)} finding(s)\n")
        for finding in findings:
            print(finding)
        print(
            "\nAllow an intentional exception with `py-runtime-allow: <reason>` or a "
            "bounded `py-runtime-rollback: owner=<who> expiry=<YYYY-MM-DD>`."
        )
    else:
        print(
            "Python runtime drift: clean — every active selector reads "
            f"{CANONICAL_DECLARATION} ({(repo_root / CANONICAL_DECLARATION).read_text(encoding='utf-8').strip()})."
        )

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
