#!/usr/bin/env python3
"""Validate translation review files before --apply-approved.

Deterministic offline checks for AI-QA approval workflow.
No LLM, DeepL, or external API calls.

Usage:
    python3 tools/check_translation_quality.py
    python3 tools/check_translation_quality.py --slug <slug>
    python3 tools/check_translation_quality.py --slug <slug> --lang es,fr,de,nl,pt
    python3 tools/check_translation_quality.py --strict
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
INDEX_PATH = REPO_ROOT / "index.json"
GLOSSARY_PATH = REPO_ROOT / "tools" / "translation_glossary.json"
REVIEWS_DIR = REPO_ROOT / "translations" / "reviews"

VALID_LANGS = {"es", "fr", "de", "nl", "pt"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MOCK_PATTERN = re.compile(r"\[MOCK|MOCK TRANSLATION|Placeholder text", re.IGNORECASE)
CODE_FENCE_RE = re.compile(r"^(```+|~~~+)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
URL_RE = re.compile(r"https?://[^\s)\"\]]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _load_glossary():
    if not GLOSSARY_PATH.exists():
        return {}
    return json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))


def _load_index():
    if not INDEX_PATH.exists():
        return {"articles": []}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _find_source_article(slug: str):
    """Return (folder, article_body) for a given slug, or (None, None)."""
    index = _load_index()
    for article in index.get("articles", []):
        if article.get("slug") == slug or article.get("folder") == slug:
            folder = article.get("folder", "")
            md_path = ARTICLES_DIR / folder / "article.md"
            if md_path.exists():
                text = md_path.read_text(encoding="utf-8", errors="replace")
                # Strip front matter
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        text = parts[2]
                return folder, text.lstrip(), article
            return folder, "", article
    return None, None, None


def _parse_review_file(review_path: Path):
    """Parse a review file and return dict with body, title, and status.

    Mirrors translate_articles.py::_parse_review_file to avoid import
    dependency on the translation tool.
    """
    if not review_path.exists():
        return None
    text = review_path.read_text(encoding="utf-8")

    status_re = re.compile(r"^Status:[ \t]*(\S+)", re.IGNORECASE)
    reviewer_re = re.compile(r"^Reviewer:[ \t]*([^\n]*)$", re.MULTILINE)
    reviewed_at_re = re.compile(r"^Reviewed at:[ \t]*([^\n]*)$", re.MULTILINE)
    title_re = re.compile(r"^-\s*\*\*Translated title:\*\*\s*([^\n]*)$", re.MULTILINE)
    model_re = re.compile(r"^-\s*\*\*Model:\*\*\s*([^\n]*)$", re.MULTILINE)
    approval_method_re = re.compile(r"^Approval method:[ \t]*([^\n]*)$", re.MULTILINE)
    quality_checked_at_re = re.compile(r"^Quality checked at:[ \t]*([^\n]*)$", re.MULTILINE)
    quality_check_model_re = re.compile(r"^Quality check model:[ \t]*([^\n]*)$", re.MULTILINE)
    original_title_re = re.compile(r"^-\s*\*\*Original title:\*\*\s*([^\n]*)$", re.MULTILINE)
    lang_re = re.compile(r"^-\s*\*\*Language:\*\*\s*([^\n]*)$", re.MULTILINE)

    status = "draft"
    for line in text.splitlines():
        m = status_re.match(line)
        if m:
            status = m.group(1).lower()

    def _search(pattern):
        m = pattern.search(text)
        return m.group(1).strip() if m else ""

    # Extract body between "## Translated body" and "## Review status"
    body = ""
    in_body = False
    for line in text.splitlines():
        if line.startswith("## Translated body"):
            in_body = True
            continue
        if line.startswith("## Review status"):
            break
        if in_body:
            body += line + "\n"
    body = body.strip()

    return {
        "body": body,
        "status": status,
        "reviewer": _search(reviewer_re),
        "reviewed_at": _search(reviewed_at_re),
        "translated_title": _search(title_re),
        "model": _search(model_re),
        "approval_method": _search(approval_method_re).lower(),
        "quality_checked_at": _search(quality_checked_at_re),
        "quality_check_model": _search(quality_check_model_re),
        "original_title": _search(original_title_re),
        "language": _search(lang_re),
    }


def _count_headings(text: str) -> int:
    return len(HEADING_RE.findall(text))


def _extract_links(text: str) -> set:
    """Extract Markdown links and bare URLs."""
    links = set()
    for _, url in LINK_RE.findall(text):
        links.add(url)
    for url in URL_RE.findall(text):
        links.add(url)
    return links


def _check_code_fences(text: str) -> list:
    """Return errors if code fences are unbalanced."""
    errors = []
    lines = text.splitlines()
    fence_stack = []
    for i, line in enumerate(lines, 1):
        m = CODE_FENCE_RE.match(line)
        if m:
            fence = m.group(1)
            if fence_stack:
                # Check if closing the current fence
                if line.startswith(fence_stack[-1]):
                    fence_stack.pop()
                else:
                    # Nested fence of different type — push
                    fence_stack.append(fence)
            else:
                fence_stack.append(fence)
    if fence_stack:
        errors.append(f"unbalanced code fence (opened {len(fence_stack)} fence(s) not closed)")
    return errors


def _check_glossary(source_text: str, translated_text: str, lang: str, glossary: dict) -> list:
    """Return warnings if glossary terms from source are missing in translation."""
    warnings = []
    if not glossary:
        return warnings
    source_lower = source_text.lower()
    trans_lower = translated_text.lower()
    for term, translations in glossary.items():
        expected = translations.get(lang, "")
        if not expected:
            continue
        # Only check if the source actually contains the term
        if term.lower() in source_lower:
            # The expected translation should appear in the translated text
            if expected.lower() not in trans_lower:
                # Also check for partial matches (some terms may be inflected)
                # Use a simple heuristic: check if any word from expected appears
                expected_words = expected.lower().split()
                if len(expected_words) > 1:
                    # For multi-word terms, require at least 2/3 of words
                    threshold = max(1, len(expected_words) * 2 // 3)
                    matched = sum(1 for w in expected_words if w in trans_lower)
                    if matched < threshold:
                        warnings.append(
                            f'source contained "{term}" but expected target term '
                            f'"{expected}" was not found'
                        )
                else:
                    warnings.append(
                        f'source contained "{term}" but expected target term '
                        f'"{expected}" was not found'
                    )
    return warnings


def _check_mock_placeholders(text: str) -> list:
    """Return errors if text contains obvious mock placeholder markers."""
    errors = []
    if MOCK_PATTERN.search(text):
        errors.append("contains mock/placeholder markers (e.g. [MOCK], MOCK TRANSLATION, Placeholder text)")
    return errors


def _check_untranslated_boilerplate(text: str) -> list:
    """Return warnings for common untranslated English boilerplate."""
    warnings = []
    boilerplate = [
        "click here",
        "read more",
        "learn more",
        "get started",
        "sign up",
        "download now",
    ]
    text_lower = text.lower()
    for phrase in boilerplate:
        if phrase in text_lower:
            warnings.append(f'contains untranslated English boilerplate: "{phrase}"')
    return warnings


def check_review_file(review_path: Path, strict: bool = False) -> tuple:
    """Check a single review file. Returns (errors, warnings).

    errors: list of str — must be fixed before apply
    warnings: list of str — should be reviewed
    """
    errors = []
    warnings = []

    data = _parse_review_file(review_path)
    if data is None:
        errors.append("review file not found or unreadable")
        return errors, warnings

    lang = data.get("language", "")
    if lang not in VALID_LANGS:
        errors.append(f"invalid or missing language code: '{lang}'")
        return errors, warnings

    # --- Approval readiness checks ---
    if data["status"] != "approved":
        errors.append(f"status is '{data['status']}' (must be 'approved' before apply)")

    approval_method = data.get("approval_method", "")
    if approval_method == "ai_qa":
        if not data.get("quality_checked_at"):
            errors.append("approval_method ai_qa requires 'Quality checked at'")
        elif not DATE_RE.match(data["quality_checked_at"]):
            errors.append(
                f"quality_checked_at must be YYYY-MM-DD, got: '{data['quality_checked_at']}'"
            )
        if not data.get("quality_check_model"):
            errors.append("approval_method ai_qa requires 'Quality check model'")
    elif approval_method == "human":
        # Human review files are valid but note that this tool targets AI-QA
        warnings.append("approval_method is 'human' — this checker targets AI-QA files")
        if not data.get("reviewer"):
            warnings.append("human review requires 'Reviewer'")
        if not data.get("reviewed_at"):
            warnings.append("human review requires 'Reviewed at'")
        elif not DATE_RE.match(data["reviewed_at"]):
            warnings.append(
                f"reviewed_at must be YYYY-MM-DD, got: '{data['reviewed_at']}'"
            )
    else:
        # Default to human behavior for backward compatibility
        if not data.get("reviewer"):
            warnings.append("no approval_method set; human review requires 'Reviewer'")
        if not data.get("reviewed_at"):
            warnings.append("no approval_method set; human review requires 'Reviewed at'")

    # --- Translated title checks ---
    translated_title = data.get("translated_title", "")
    if not translated_title:
        errors.append("missing 'Translated title'")
    elif translated_title.startswith("[MOCK") or "placeholder" in translated_title.lower():
        errors.append(f"translated title looks like a placeholder: '{translated_title}'")

    # --- Body checks ---
    body = data.get("body", "")
    if not body:
        errors.append("missing translated body")
    else:
        # Body structural checks
        # Code fence balance
        fence_errors = _check_code_fences(body)
        errors.extend(fence_errors)

        # Mock placeholder detection
        placeholder_errors = _check_mock_placeholders(body)
        errors.extend(placeholder_errors)

        # Untranslated boilerplate
        boilerplate_warnings = _check_untranslated_boilerplate(body)
        warnings.extend(boilerplate_warnings)

    # --- Source-comparative checks ---
    # Derive slug from filename: <slug>.<lang>.review.md
    name = review_path.name
    if name.endswith(".review.md"):
        name_without_suffix = name[:-len(".review.md")]
        slug = name_without_suffix.rsplit(".", 1)[0]
    else:
        slug = review_path.stem.rsplit(".", 1)[0]
    folder, source_body, article = _find_source_article(slug)
    if source_body is None:
        warnings.append(f"could not find source article for slug '{slug}'")
    else:
        # Heading count comparison
        source_headings = _count_headings(source_body)
        trans_headings = _count_headings(body)
        if source_headings > 0:
            ratio = trans_headings / source_headings
            if ratio < 0.5:
                errors.append(
                    f"heading count dropped severely: source={source_headings}, "
                    f"translation={trans_headings} ({ratio:.0%})"
                )
            elif ratio < 0.75:
                warnings.append(
                    f"heading count lower than source: source={source_headings}, "
                    f"translation={trans_headings} ({ratio:.0%})"
                )

        # Link preservation check
        source_links = _extract_links(source_body)
        trans_links = _extract_links(body)
        missing_links = source_links - trans_links
        if missing_links:
            # Some links may be intentionally localized; report as warning
            warnings.append(
                f"source links possibly missing in translation: {', '.join(sorted(missing_links)[:3])}"
                + ("..." if len(missing_links) > 3 else "")
            )

        # Glossary compliance
        glossary = _load_glossary()
        glossary_warnings = _check_glossary(source_body, body, lang, glossary)
        if strict:
            errors.extend(glossary_warnings)
        else:
            warnings.extend(glossary_warnings)

    return errors, warnings


def _find_review_files(slug: str = None, langs: set = None):
    """Return list of review file paths matching criteria."""
    if not REVIEWS_DIR.exists():
        return []

    files = []
    for path in REVIEWS_DIR.glob("*.review.md"):
        # Filename: <slug>.<lang>.review.md
        name = path.name
        if not name.endswith(".review.md"):
            continue
        name_without_suffix = name[:-len(".review.md")]
        parts = name_without_suffix.split(".")
        if len(parts) < 2:
            continue
        file_lang = parts[-1]
        file_slug = ".".join(parts[:-1])

        if langs and file_lang not in langs:
            continue
        if slug and file_slug != slug:
            continue
        files.append(path)

    return sorted(files)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate translation review files before --apply-approved"
    )
    parser.add_argument("--slug", type=str, default=None, help="Target a single article by slug")
    parser.add_argument(
        "--lang",
        type=str,
        default=",".join(VALID_LANGS),
        help="Comma-separated language codes (default: es,fr,de,nl,pt)",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args(argv)

    langs = {l.strip() for l in args.lang.split(",") if l.strip()}
    invalid = langs - VALID_LANGS
    if invalid:
        print(
            f"[translation-quality] ERROR: invalid language code(s): {', '.join(sorted(invalid))}",
            file=sys.stderr,
        )
        return 1

    review_files = _find_review_files(slug=args.slug, langs=langs)
    if not review_files:
        print("[translation-quality] No review files found matching criteria")
        return 0

    total_errors = 0
    total_warnings = 0
    failed_files = 0

    for review_path in review_files:
        rel_path = review_path.relative_to(REPO_ROOT)
        errors, warnings = check_review_file(review_path, strict=args.strict)

        if errors or (args.strict and warnings):
            failed_files += 1
            print(f"[translation-quality] ERROR {rel_path}:")
            for err in errors:
                print(f"  - {err}")
            if args.strict:
                for warn in warnings:
                    print(f"  - [strict] {warn}")
            else:
                for warn in warnings:
                    print(f"  - WARNING: {warn}")
        elif warnings:
            print(f"[translation-quality] WARNING {rel_path}:")
            for warn in warnings:
                print(f"  - {warn}")

        total_errors += len(errors)
        total_warnings += len(warnings)

    checked = len(review_files)
    passed = checked - failed_files

    if failed_files == 0:
        print(
            f"[translation-quality] checked={checked} passed={passed} "
            f"warnings={total_warnings} errors={total_errors}"
        )
        return 0 if not (args.strict and total_warnings) else 1
    else:
        print(
            f"[translation-quality] checked={checked} passed={passed} "
            f"warnings={total_warnings} errors={total_errors} "
            f"failed={failed_files}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
