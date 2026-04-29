#!/usr/bin/env python3
"""Dry-run / sandbox-capable per-article DOI minting via Zenodo.

Usage:
    python3 tools/mint_dois.py --dry-run              # preview payloads, no network
    python3 tools/mint_dois.py --dry-run --slug XYZ   # preview one article
    python3 tools/mint_dois.py --sandbox --write --slug XYZ  # sandbox deposit
    python3 tools/mint_dois.py --write --yes-i-understand-production-dois-are-permanent --slug XYZ  # production
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
INDEX_PATH = REPO_ROOT / "index.json"

ZENODO_PROD = "https://zenodo.org/api"
ZENODO_SANDBOX = "https://sandbox.zenodo.org/api"

# Safety: default limit in write mode to prevent accidental bulk runs.
DEFAULT_WRITE_LIMIT = 1


def _mask_token(token: str) -> str:
    if not token:
        return "<not-set>"
    if len(token) <= 12:
        return "***"
    return token[:4] + "..." + token[-4:]


def _build_argparser():
    parser = argparse.ArgumentParser(description="Mint per-article DOIs via Zenodo.")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview payloads without network calls (default).")
    parser.add_argument("--write", action="store_true",
                        help="Enable network calls and metadata writes.")
    parser.add_argument("--sandbox", action="store_true",
                        help="Use Zenodo Sandbox instead of production.")
    parser.add_argument("--slug", type=str, default=None,
                        help="Target a single article by slug.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N articles.")
    parser.add_argument("--no-publish", action="store_true",
                        help="Create deposition but do not publish. DOI is not written to metadata.")
    parser.add_argument("--yes-i-understand-production-dois-are-permanent", action="store_true",
                        dest="production_confirmed",
                        help="Required for production write mode.")
    return parser


def _load_index():
    if not INDEX_PATH.exists():
        print(f"[mint] index.json not found at {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _article_snapshot_content(article):
    """Generate a deterministic article snapshot for Zenodo deposit."""
    header = (
        f"# {article['title']}\n\n"
        f"- **Author:** {article.get('author', 'Dr. Hernani Costa')}\n"
        f"- **Publication date:** {article['published_date']}\n"
        f"- **Canonical URL:** {article['canonical_url']}\n"
        f"- **Local archive URL:** https://articles.firstaimovers.com{article.get('local_path', '')}\n"
        f"- **License:** {article.get('license', 'CC BY 4.0')}\n"
        f"\n---\n\n"
    )
    folder = article.get("folder", "")
    md_path = ARTICLES_DIR / folder / "article.md"
    if md_path.exists():
        body = md_path.read_text(encoding="utf-8", errors="replace")
    else:
        body = ""
    return header + body


def _build_zenodo_payload(article):
    """Build Zenodo deposition metadata payload."""
    title = article["title"]
    published_date = article["published_date"]
    canonical_url = article["canonical_url"]
    local_path = article.get("local_path", "")
    local_url = f"https://articles.firstaimovers.com{local_path}" if local_path else ""
    summary = article.get("summary", "")
    tldr = article.get("tldr", "")
    description = tldr or summary or title
    topics = article.get("topics", []) or article.get("tags", [])
    keywords = [t for t in topics[:10] if t]

    payload = {
        "metadata": {
            "title": title,
            "upload_type": "publication",
            "publication_type": "article",
            "publication_date": published_date,
            "creators": [
                {
                    "name": "Costa, Hernani",
                    "orcid": "0000-0002-6813-4641",
                }
            ],
            "description": description,
            "license": "cc-by-4.0",
            "keywords": keywords,
            "related_identifiers": [
                {
                    "identifier": canonical_url,
                    "relation": "isIdenticalTo",
                    "resource_type": "publication-article",
                },
            ],
        }
    }
    if local_url:
        payload["metadata"]["related_identifiers"].append({
            "identifier": local_url,
            "relation": "isArchivedBy",
            "resource_type": "publication-article",
        })
    return payload


def _get_token(args):
    if args.sandbox:
        token = os.environ.get("ZENODO_SANDBOX_API_TOKEN", "").strip()
        if args.write and not token:
            print("[mint] ERROR: ZENODO_SANDBOX_API_TOKEN is required for sandbox write mode.", file=sys.stderr)
            sys.exit(1)
        return token
    token = os.environ.get("ZENODO_API_TOKEN", "").strip()
    if args.write and not token:
        print("[mint] ERROR: ZENODO_API_TOKEN is required for production write mode.", file=sys.stderr)
        sys.exit(1)
    return token


def _api_call(method, url, token, **kwargs):
    """Make an HTTP request to Zenodo. Returns (status_code, response_json_or_text, headers)."""
    import requests
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))
    resp = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return resp.status_code, data, resp.headers


def _deposit_article(article, args, token, base_url):
    """Create a Zenodo deposition for a single article.

    Returns a dict with keys:
        - success: bool
        - doi: str or None (only set on successful publish)
        - pre_reserved_doi: str or None (set on draft creation)
        - message: str
        - deposition_id: str or None
    """
    slug = article.get("slug", article.get("folder", ""))
    payload = _build_zenodo_payload(article)
    snapshot = _article_snapshot_content(article)
    filename = f"first-ai-movers-article-{slug}.md"

    print(f"[mint] Article: {slug}")
    print(f"[mint] Title: {article['title']}")
    print(f"[mint] Filename: {filename}")

    if args.dry_run and not args.write:
        print(f"[mint] Payload preview: {json.dumps(payload, indent=2)}")
        print(f"[mint] Snapshot size: {len(snapshot.encode('utf-8'))} bytes")
        print("[mint] Dry-run complete. No network calls made.")
        return {"success": True, "doi": None, "pre_reserved_doi": None, "message": "dry-run", "deposition_id": None}

    # Step 1: Create empty deposition
    create_url = f"{base_url}/deposit/depositions"
    status, data, _ = _api_call("POST", create_url, token, json={})
    if status not in (200, 201):
        return {
            "success": False,
            "doi": None,
            "pre_reserved_doi": None,
            "message": f"Failed to create deposition: HTTP {status} — {data}",
            "deposition_id": None,
        }
    dep_id = data.get("id")
    pre_reserved_doi = data.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    bucket_url = data.get("links", {}).get("bucket")

    if not dep_id:
        return {
            "success": False,
            "doi": None,
            "pre_reserved_doi": None,
            "message": "Deposition created but no ID returned.",
            "deposition_id": None,
        }

    print(f"[mint] Created deposition {dep_id}")
    if pre_reserved_doi:
        print(f"[mint] Pre-reserved DOI: {pre_reserved_doi} (not final until published)")

    # Step 2: Upload file to bucket
    if bucket_url:
        upload_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        }
        import requests
        upload_resp = requests.put(
            f"{bucket_url}/{filename}",
            headers=upload_headers,
            data=snapshot.encode("utf-8"),
            timeout=120,
        )
        if upload_resp.status_code not in (200, 201):
            return {
                "success": False,
                "doi": None,
                "pre_reserved_doi": pre_reserved_doi,
                "message": f"File upload failed: HTTP {upload_resp.status_code} — {upload_resp.text}",
                "deposition_id": dep_id,
            }
        print(f"[mint] Uploaded {filename} to bucket")
    else:
        return {
            "success": False,
            "doi": None,
            "pre_reserved_doi": pre_reserved_doi,
            "message": "No bucket URL in deposition response.",
            "deposition_id": dep_id,
        }

    # Step 3: Update metadata
    meta_url = f"{base_url}/deposit/depositions/{dep_id}"
    status, data, _ = _api_call("PUT", meta_url, token, json=payload)
    if status not in (200, 202):
        return {
            "success": False,
            "doi": None,
            "pre_reserved_doi": pre_reserved_doi,
            "message": f"Metadata update failed: HTTP {status} — {data}",
            "deposition_id": dep_id,
        }
    print(f"[mint] Metadata updated")

    if args.no_publish:
        print(f"[mint] --no-publish: deposition {dep_id} is a draft. Pre-reserved DOI: {pre_reserved_doi}")
        return {
            "success": True,
            "doi": None,
            "pre_reserved_doi": pre_reserved_doi,
            "message": f"Draft created (not published). Pre-reserved DOI: {pre_reserved_doi}",
            "deposition_id": dep_id,
        }

    # Step 4: Publish
    publish_url = f"{base_url}/deposit/depositions/{dep_id}/actions/publish"
    status, data, _ = _api_call("POST", publish_url, token)
    if status not in (200, 202):
        return {
            "success": False,
            "doi": None,
            "pre_reserved_doi": pre_reserved_doi,
            "message": f"Publish failed: HTTP {status} — {data}",
            "deposition_id": dep_id,
        }

    final_doi = data.get("doi") or data.get("metadata", {}).get("doi")
    if not final_doi:
        final_doi = pre_reserved_doi

    print(f"[mint] Published deposition {dep_id} with DOI: {final_doi}")
    return {
        "success": True,
        "doi": final_doi,
        "pre_reserved_doi": pre_reserved_doi,
        "message": f"Published with DOI {final_doi}",
        "deposition_id": dep_id,
    }


def _write_doi_to_metadata(folder, doi):
    """Atomically write DOI back to articles/{folder}/metadata.json."""
    meta_path = ARTICLES_DIR / folder / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json not found: {meta_path}")
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    if data.get("doi"):
        raise ValueError(f"DOI already exists for {folder}: {data['doi']}")
    data["doi"] = doi
    from _atomic_io import atomic_write_json
    atomic_write_json(meta_path, data)
    print(f"[mint] Wrote DOI to {meta_path}")


def main(argv=None):
    parser = _build_argparser()
    args = parser.parse_args(argv)

    if args.write:
        args.dry_run = False

    # Production safety check
    if args.write and not args.sandbox and not args.production_confirmed:
        print(
            "[mint] ERROR: Production write mode requires the flag "
            "--yes-i-understand-production-dois-are-permanent",
            file=sys.stderr,
        )
        sys.exit(1)

    base_url = ZENODO_SANDBOX if args.sandbox else ZENODO_PROD
    token = _get_token(args)

    print(f"[mint] Base URL: {base_url}")
    print(f"[mint] Token: {_mask_token(token)}")
    print(f"[mint] Mode: {'dry-run' if args.dry_run else 'write'}")
    if args.write:
        print(f"[mint] Publish: {'no' if args.no_publish else 'yes'}")

    index = _load_index()
    articles = index.get("articles", [])

    # Filter candidates
    candidates = []
    for a in articles:
        if a.get("doi"):
            continue
        if args.slug:
            if a.get("slug") == args.slug or a.get("folder") == args.slug:
                candidates.append(a)
                break
        else:
            candidates.append(a)

    if not candidates:
        print("[mint] No candidate articles found.")
        return 0

    limit = args.limit
    if args.write and limit is None:
        limit = DEFAULT_WRITE_LIMIT
    if limit is not None:
        candidates = candidates[:limit]

    print(f"[mint] Candidates: {len(candidates)}")

    results = []
    for article in candidates:
        result = _deposit_article(article, args, token, base_url)
        results.append({"slug": article.get("slug", article.get("folder", "")), **result})

        if result["success"] and result["doi"] and args.write:
            try:
                _write_doi_to_metadata(article.get("folder", ""), result["doi"])
            except Exception as e:
                print(f"[mint] ERROR writing DOI to metadata: {e}", file=sys.stderr)
                result["success"] = False
                result["message"] += f" (metadata write failed: {e})"

        if args.write:
            time.sleep(1)

    # Report
    print("\n[mint] Results:")
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        print(f"  {status} {r['slug']}: {r['message']}")

    return 0 if all(r["success"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
