# Architecture

{{cookiecutter.project_name}} is a static-site generator built in Python.

## Overview

Articles are stored as Markdown + JSON metadata in `articles/YYYY-MM-DD-slug/`.
`tools/rebuild_local.py` builds `index.json`, renders HTML via Jinja2, and copies static assets into `site/`.

## Build pipeline

1. `tools/normalize_tags.py` — cleans metadata
2. `tools/rebuild_local.py` — builds index, feeds, sitemap, and HTML
3. GitHub Pages (or Cloudflare Pages) serves `site/`

## Customize

- Edit `templates/` for layout changes
- Edit `static/style.css` for design changes
- Add topics to `tools/topic_mapping.json` when you have enough articles
