#!/usr/bin/env python3
"""Build a deterministic citation graph between archive articles.

Scans every articles/*/article.md for explicit markdown links to other
articles in this archive. Emits citation_graph.json (nodes = articles,
edges = "references"). Does not infer citations from topic overlap.

Usage:
    python3 tools/build_citation_graph.py
    python3 tools/build_citation_graph.py --check
    python3 tools/build_citation_graph.py --out /tmp/citation_graph.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
DEFAULT_OUT = REPO_ROOT / "citation_graph.json"

# Markdown link pattern: [anchor](url)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Non-article paths we intentionally ignore on firstaimovers.com domains
_IGNORE_PATH_PREFIXES = (
    "/page/",
    "/c/",
    "/archive",
    "/subscribe",
    "/upgrade",
    "/archive?",
)

# Hosts we consider "ours" for article-link purposes
_OUR_HOSTS = {
    "articles.firstaimovers.com",
    "radar.firstaimovers.com",
    "www.firstaimovers.com",
    "firstaimovers.com",
    "insights.firstaimovers.com",
    "voices.firstaimovers.com",
}


def _load_index():
    path = REPO_ROOT / "index.json"
    if not path.exists():
        print("[citation-graph] error: index.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _build_lookup_maps(index):
    """Build URL -> folder/slug lookup maps for edge detection.

    Returns a dict mapping known article URLs to (folder, slug) tuples.
    """
    lookup = {}
    for a in index.get("articles", []):
        folder = a.get("folder", "")
        slug = a.get("slug", "")
        if not folder:
            continue

        # Local archive URLs
        if slug:
            lookup[f"https://articles.firstaimovers.com/articles/{slug}/"] = (folder, slug)
            lookup[f"/articles/{slug}/"] = (folder, slug)

        # Canonical URLs from metadata (we also read these per-article)
        canonical = a.get("canonical_url", "")
        if canonical:
            canonical = canonical.strip()
            lookup[canonical] = (folder, slug)
            if canonical.endswith("/"):
                lookup[canonical.rstrip("/")] = (folder, slug)

    # Also scan metadata.json on disk for canonical URLs (index.json may lag)
    for meta_path in ARTICLES_DIR.glob("*/metadata.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        folder = meta_path.parent.name
        slug = meta.get("slug", "")
        canonical = meta.get("canonical_url", "")
        if canonical:
            canonical = canonical.strip()
            lookup[canonical] = (folder, slug)
            if canonical.endswith("/"):
                lookup[canonical.rstrip("/")] = (folder, slug)
        if slug:
            lookup[f"https://articles.firstaimovers.com/articles/{slug}/"] = (folder, slug)
            lookup[f"/articles/{slug}/"] = (folder, slug)

    return lookup


def _build_slug_map(index):
    """Map slug -> folder for Beehiiv /p/<slug> and trailing-slug matching."""
    slug_map = {}
    for a in index.get("articles", []):
        slug = a.get("slug", "")
        folder = a.get("folder", "")
        if slug and folder:
            slug_map[slug] = folder
    # Also scan disk
    for meta_path in ARTICLES_DIR.glob("*/metadata.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        slug = meta.get("slug", "")
        folder = meta_path.parent.name
        if slug and folder:
            slug_map[slug] = folder
    return slug_map


def _is_our_host(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() in _OUR_HOSTS
    except Exception:
        return False


def _is_ignored_path(url):
    """Return True if URL path matches a non-article page prefix."""
    try:
        parsed = urlparse(url)
        path = parsed.path
        for prefix in _IGNORE_PATH_PREFIXES:
            if path.startswith(prefix):
                return True
        # Root homepage links
        if path in ("", "/"):
            return True
        return False
    except Exception:
        return True


def _resolve_link(url, lookup, slug_map, self_canonical, self_slug):
    """Return (target_folder, target_slug, matched_url) or None."""
    if not url:
        return None

    is_relative = url.startswith("/")
    if not is_relative and not url.startswith("http"):
        return None

    # For absolute URLs, ignore external non-our-host links
    if not is_relative and not _is_our_host(url):
        return None

    # Ignore non-article pages
    if _is_ignored_path(url):
        return None

    # Self-link check: link starts with this article's canonical URL
    if self_canonical and url.startswith(self_canonical):
        return None

    # Self-link check: link contains this article's slug as the last path segment
    try:
        parsed = urlparse(url)
        path_last = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
        if path_last and path_last == self_slug:
            return None
    except Exception:
        pass

    # 1. Direct prefix match against lookup (canonical + local URLs)
    for known_url, (folder, slug) in lookup.items():
        if url.startswith(known_url):
            return folder, slug, known_url

    # 2. Slug match for Beehiiv /p/<slug> or any path ending in a known slug
    try:
        parsed = urlparse(url)
        path_last = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
        if path_last in slug_map:
            folder = slug_map[path_last]
            return folder, path_last, url
    except Exception:
        pass

    return None


def _extract_links_from_article(folder, lookup, slug_map):
    """Return list of edge dicts for a single article.

    Each edge dict has keys:
        source_folder, target_folder, source_slug, target_slug,
        type, matched_url, anchor_text
    """
    md_path = ARTICLES_DIR / folder / "article.md"
    meta_path = ARTICLES_DIR / folder / "metadata.json"
    if not md_path.exists() or not meta_path.exists():
        return []

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    self_canonical = meta.get("canonical_url", "").strip()
    self_slug = meta.get("slug", "")

    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    edges = []
    seen = set()
    for anchor_text, url in _MARKDOWN_LINK_RE.findall(text):
        url = url.strip()
        resolved = _resolve_link(url, lookup, slug_map, self_canonical, self_slug)
        if not resolved:
            continue
        target_folder, target_slug, matched_url = resolved
        if target_folder == folder:
            continue  # skip self-links
        key = (folder, target_folder, matched_url, anchor_text)
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "source_folder": folder,
            "target_folder": target_folder,
            "source_slug": self_slug or folder,
            "target_slug": target_slug or target_folder,
            "type": "explicit-link",
            "matched_url": matched_url,
            "anchor_text": anchor_text.strip(),
        })

    return edges


def build_graph():
    """Build the citation graph from index.json + article Markdown."""
    index = _load_index()
    lookup = _build_lookup_maps(index)
    slug_map = _build_slug_map(index)

    nodes = []
    for a in index.get("articles", []):
        folder = a.get("folder", "")
        slug = a.get("slug", "")
        canonical = a.get("canonical_url", "")
        local_url = f"https://articles.firstaimovers.com/articles/{slug}/" if slug else ""
        nodes.append({
            "folder": folder,
            "slug": slug or folder,
            "title": a.get("title", ""),
            "published_date": a.get("published_date", ""),
            "local_url": local_url,
            "canonical_url": canonical,
            "topics": a.get("topics", []) or a.get("tags", []),
        })

    # Deterministic node ordering
    nodes.sort(key=lambda n: (n.get("published_date", ""), n.get("title", "")), reverse=True)

    edges = []
    for a in index.get("articles", []):
        folder = a.get("folder", "")
        if not folder:
            continue
        edges.extend(_extract_links_from_article(folder, lookup, slug_map))

    # Deterministic edge ordering
    edges.sort(key=lambda e: (e["source_folder"], e["target_folder"], e["matched_url"]))

    # Compute stats
    articles_with_outgoing = len(set(e["source_folder"] for e in edges))
    articles_with_incoming = len(set(e["target_folder"] for e in edges))

    graph = {
        "version": 1,
        "generated_from": "articles",
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "articles_with_outgoing": articles_with_outgoing,
            "articles_with_incoming": articles_with_incoming,
        },
    }
    return graph


def write_graph(graph, out_path):
    from _atomic_io import atomic_write_json
    atomic_write_json(out_path, graph)
    stats = graph["stats"]
    print(
        f"[citation-graph] nodes={stats['node_count']} edges={stats['edge_count']} "
        f"outgoing={stats['articles_with_outgoing']} incoming={stats['articles_with_incoming']} "
        f"out={out_path}"
    )


def main():
    parser = argparse.ArgumentParser(description="Build article citation graph")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output path")
    parser.add_argument("--check", action="store_true", help="Exit nonzero if existing graph would change")
    args = parser.parse_args()

    graph = build_graph()

    if args.check:
        if not args.out.exists():
            print(f"[citation-graph] --check failed: {args.out} does not exist", file=sys.stderr)
            sys.exit(1)
        existing = json.loads(args.out.read_text(encoding="utf-8"))
        if existing != graph:
            print("[citation-graph] --check failed: graph is stale", file=sys.stderr)
            sys.exit(1)
        print("[citation-graph] --check passed")
        return

    write_graph(graph, args.out)


if __name__ == "__main__":
    main()
