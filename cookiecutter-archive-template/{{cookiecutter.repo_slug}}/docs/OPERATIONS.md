# Operations

## Adding an article

1. Create `articles/YYYY-MM-DD-slug/article.md` with front matter
2. Create `articles/YYYY-MM-DD-slug/metadata.json`
3. Run `python3 tools/normalize_tags.py`
4. Run `python3 tools/rebuild_local.py`
5. Commit and push

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install markdown jinja2 pytest
python3 tools/rebuild_local.py
```

## See also

- `docs/ARCHITECTURE.md`
- `CONTRIBUTING.md`
