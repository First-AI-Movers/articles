# Security Policy

## Supported surfaces

This repository is a **public, open-access article archive**. The supported security surface is:

- The GitHub repository and its Actions workflows.
- The static HTML site deployed to GitHub Pages at `articles.firstaimovers.com`.
- The generated machine-readable artifacts (`index.json`, `feed.xml`, `sitemap.xml`, `llms-full.txt`, etc.).

We do **not** operate a backend API, database, or authenticated service. All content is static and publicly readable.

## Reporting a vulnerability

If you discover a security vulnerability in this repository or its deployment pipeline, please report it responsibly:

1. **Email:** info@firstaimovers.com
2. **Subject:** `[Security] First AI Movers Article Archive — vulnerability report`
3. **Include:**
   - A clear description of the vulnerability.
   - Steps to reproduce (if applicable).
   - Potential impact.
   - Suggested mitigation (optional).

We aim to acknowledge reports within 48 hours and provide a timeline for resolution within 7 days.

## No secrets policy

This repository must never contain:

- API keys, tokens, or passwords.
- Private environment files (`.env`).
- Unpublished drafts or confidential content.
- Personal data of subscribers or readers.

**IndexNow keys are an exception to the "no keys" rule in principle, but not in practice.**
IndexNow keys are *public verification tokens* (proof-of-host ownership), not private secrets.
However, for operational consistency, the repo sources them from Doppler/env variables
(`INDEXNOW_API_KEY_ARTICLES_FAIM`) rather than committing rotating key values.

All files under `articles/` are public. If you accidentally commit sensitive material, open a PR to remove it immediately and contact info@firstaimovers.com.

## Dependency and supply-chain security

- Python dependencies are pinned in `tools/requirements.txt`.
- GitHub Actions use pinned major versions (`@v4`, `@v5`).
- The CI workflow has minimal permissions:
  - `contents: write` — only to commit regenerated artifacts.
  - `pages: write` + `id-token: write` — only for GitHub Pages deployment.
- No external API calls are made during CI except standard GitHub Actions marketplace actions.

If you identify a vulnerable dependency, open an issue or PR with the upgrade and a link to the advisory.

## Public archive and canonical URL disclosure

This repository intentionally publishes:

- Full article text (`articles/*/article.md`).
- Structured metadata including `canonical_url` (primary publishing property).
- Author biographical data (`hernanicosta.json`, `ABOUT.md`).

This is by design — the archive is meant to be machine-readable and citable. Do not report the public availability of article text or metadata as a vulnerability.

## XSS and content-safety

The archive renders article Markdown to HTML using Jinja2 with autoescape enabled. A lightweight sanitizer strips `<script>`, `<iframe>`, event handlers, and `javascript:` URLs from rendered article bodies.

If you find a bypass in the sanitizer or template escaping that could lead to stored XSS on `articles.firstaimovers.com`, please report it using the process above.

## Security-related workflow

- Security fixes are treated as high-priority PRs.
- They follow the same branch → PR → review → merge workflow as all other changes.
- No direct pushes to `main`.
