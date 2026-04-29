# Contributing

## Archive invariants

1. Article text is immutable once published. Do not edit `article.md` after publication.
2. Canonical URLs are permanent.
3. Generated artifacts are never hand-edited.
4. No secrets or private drafts in the repository.

## Property scope

This archive is for **{{cookiecutter.publisher_name}} content only**. Do not add articles from unrelated brands or properties. If you need an archive for a different brand, fork the `cookiecutter-archive-template/` pattern and create a separate repository.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install markdown jinja2 pytest
python3 tools/rebuild_local.py
python3 -m pytest tools/tests -v
```

## PR workflow

1. Branch from `main`.
2. Make the smallest change.
3. Run validation locally.
4. Open a PR.
