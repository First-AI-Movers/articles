#!/usr/bin/env python3
"""Rebuild index.json and static site for {{cookiecutter.project_name}}.

This is a minimal starter version. Expand as needed.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SITE_DIR = REPO_ROOT / "site"
STATIC_DIR = REPO_ROOT / "static"
TEMPLATE_DIR = REPO_ROOT / "templates"
SITE_BASE = "{{cookiecutter.site_url}}"


def build_index():
    folders = sorted(p.name for p in ARTICLES_DIR.iterdir() if p.is_dir())
    articles = []
    for folder in folders:
        meta_path = ARTICLES_DIR / folder / "metadata.json"
        if not meta_path.exists():
            continue
        with meta_path.open("r", encoding="utf-8") as fh:
            meta = json.load(fh)
        articles.append({
            "folder": meta.get("folder", folder),
            "slug": meta.get("slug", ""),
            "title": meta.get("title", ""),
            "published_date": meta.get("published_date", ""),
            "tags": meta.get("tags", []),
            "topics": meta.get("topics", []),
            "canonical_url": meta.get("canonical_url", ""),
        })
    articles.sort(key=lambda a: (a.get("published_date", ""), a.get("folder", "")), reverse=True)
    return {"articles": articles}


def build_site(index):
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        print("[site] jinja2 not installed; skipping site build", file=sys.stderr)
        return

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "htm", "xml", "xhtml", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )

    articles = index["articles"]
    stats = {"total": len(articles)}

    def _render(template_name, output_relpath, **ctx):
        template = env.get_template(template_name)
        html = template.render(
            site_title="{{cookiecutter.project_name}}",
            site_description="Article archive for {{cookiecutter.publisher_name}}.",
            site_url=SITE_BASE,
            rel_root="",
            stats=stats,
            latest=articles[:10],
            author_name="{{cookiecutter.author_name}}",
            author_url="{{cookiecutter.author_url}}",
            publisher_name="{{cookiecutter.publisher_name}}",
            publisher_url="{{cookiecutter.publisher_url}}",
            **ctx,
        )
        out_path = SITE_DIR / output_relpath
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

    _render("home.html.j2", "index.html")

    for art in articles:
        md_path = ARTICLES_DIR / art["folder"] / "article.md"
        body = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
        # Simple front-matter strip
        if body.startswith("---"):
            parts = body.split("---", 2)
            if len(parts) >= 3:
                body = parts[2].strip()
        # Very basic markdown-to-HTML for starter
        import markdown
        body_html = markdown.markdown(body, extensions=["extra"])
        _render("article.html.j2", f"articles/{art['slug']}/index.html",
                title=art["title"],
                published_date=art["published_date"],
                author="{{cookiecutter.author_name}}",
                canonical_url=art["canonical_url"],
                canonical_host_label="source",
                body_html=body_html,
                summary="")

    # Copy static assets
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, SITE_DIR, dirs_exist_ok=True)

    # Copy index.json
    (SITE_DIR / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(f"[site] Built {len(articles)} articles into {SITE_DIR}")


if __name__ == "__main__":
    idx = build_index()
    build_site(idx)
