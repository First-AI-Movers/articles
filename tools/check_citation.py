#!/usr/bin/env python3
"""Validate CITATION.cff metadata without network calls.

Usage:
    python3 tools/check_citation.py          # validate repo CITATION.cff
    python3 tools/check_citation.py <path>   # validate a specific file
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("[check-citation] PyYAML not installed; skipping structured validation.")
    yaml = None


REQUIRED_FIELDS = ["cff-version", "message", "title", "authors", "license"]
ALLOWED_TYPES = {"dataset", "software"}
FAKE_DOI_PATTERNS = ["XXXXXXX", "placeholder", "pending", "TODO", "FIXME", "example"]


def _has_fake_doi(value: str) -> bool:
    if not value:
        return False
    lower = value.lower()
    return any(p.lower() in lower for p in FAKE_DOI_PATTERNS)


def check(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    report = {
        "file": str(path),
        "errors": [],
        "warnings": [],
        "ok": True,
    }

    # Basic presence checks
    for field in REQUIRED_FIELDS:
        if field not in text:
            report["errors"].append(f"Missing required field: {field}")

    # Check for fake DOI in uncommented lines only
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "doi" in stripped.lower() and _has_fake_doi(stripped):
            report["errors"].append(f"Line {i}: DOI field contains placeholder ({stripped.strip()}). Remove or comment out until real DOI is issued.")

    # Structured YAML validation
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
        except Exception as exc:
            report["errors"].append(f"Invalid YAML: {exc}")
            data = None

        if data is not None:
            cff_version = data.get("cff-version", "")
            if not str(cff_version).startswith("1.2"):
                report["warnings"].append(f"cff-version is '{cff_version}'; expected 1.2.x for best compatibility.")

            authors = data.get("authors", [])
            if not authors:
                report["errors"].append("No authors listed.")
            else:
                for idx, author in enumerate(authors):
                    if not author.get("family-names") or not author.get("given-names"):
                        report["errors"].append(f"Author {idx + 1} missing family-names or given-names.")

            doc_type = data.get("type")
            if doc_type and doc_type not in ALLOWED_TYPES:
                report["warnings"].append(f"type='{doc_type}' is not a common CFF type ({ALLOWED_TYPES}).")

            doi = data.get("doi")
            if doi is not None:
                if _has_fake_doi(doi):
                    report["errors"].append(f"doi='{doi}' looks like a placeholder. Comment it out until Zenodo issues a real DOI.")

            license_val = data.get("license", "")
            if "CC-BY-4.0" not in str(license_val).upper().replace(" ", ""):
                report["warnings"].append(f"license='{license_val}' — expected CC-BY-4.0 for content corpus.")

            if "apache" in str(license_val).lower():
                report["warnings"].append("CITATION.cff license is Apache-2.0 — confirm this covers the content corpus, not just code.")

    report["ok"] = len(report["errors"]) == 0
    return report


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "CITATION.cff"
    if not target.exists():
        print(f"[check-citation] File not found: {target}")
        return 1

    report = check(target)
    print(f"[check-citation] {report['file']}")
    if report["errors"]:
        for e in report["errors"]:
            print(f"  ERROR: {e}")
    if report["warnings"]:
        for w in report["warnings"]:
            print(f"  WARNING: {w}")
    if report["ok"] and not report["warnings"]:
        print("  OK: CITATION.cff looks valid.")
    elif report["ok"]:
        print("  OK with warnings.")
    else:
        print("  FAILED: fix errors above.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
