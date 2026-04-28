# Comments

This document describes the optional comments layer for the First AI Movers Article Archive.

## Overview

Comments are powered by [Giscus](https://giscus.app), a free, open-source, ad-free, no-tracking comments system that stores discussions in GitHub Discussions. Giscus maps article pages to discussions by URL pathname and can auto-create a discussion when someone first comments.

## Current status

**Disabled by default.** The archive ships with the Giscus integration scaffold, but comments are not rendered until explicitly enabled. This is because the required GitHub Discussions setup and Giscus app configuration are user-side steps that must be completed first.

## Requirements

1. **GitHub Discussions enabled** on the `First-AI-Movers/articles` repository.
2. **Giscus app installed** on the repository ([github.com/apps/giscus](https://github.com/apps/giscus)).
3. **A Discussion category** created (e.g., "Comments") and its ID retrieved from [giscus.app](https://giscus.app).
4. **Repository ID** retrieved from [giscus.app](https://giscus.app).

## Enabling comments

1. Enable Discussions on the repository:
   - Go to **Settings → General → Discussions** and check "Enable discussions".
2. Install the Giscus app:
   - Visit [github.com/apps/giscus](https://github.com/apps/giscus) and install it for `First-AI-Movers/articles`.
3. Get your IDs from [giscus.app](https://giscus.app):
   - Enter the repository: `First-AI-Movers/articles`.
   - Select the discussion category (e.g., "Comments").
   - Copy the generated `data-repo-id` and `data-category-id` values.
4. Update `tools/comments_config.json`:
   ```json
   {
     "enabled": true,
     "provider": "giscus",
     "repo": "First-AI-Movers/articles",
     "repo_id": "R_kgDO...",
     "category": "Comments",
     "category_id": "DIC_kwDO...",
     "mapping": "pathname",
     "strict": "0",
     "reactions_enabled": "1",
     "emit_metadata": "0",
     "input_position": "bottom",
     "theme": "preferred_color_scheme",
     "lang": "en"
   }
   ```
5. Run `python3 tools/rebuild_local.py`.
6. Commit and deploy.

## Disabling comments

Set `"enabled": false` in `tools/comments_config.json`, rebuild, and deploy. No discussion data is lost — existing comments remain in GitHub Discussions.

## Privacy and security

- **No comments database in this repository.** All comment data lives in GitHub Discussions.
- **No ad-tech or tracking added by our code.** Giscus itself is ad-free and does not track readers.
- **GitHub login required** to comment. Commenters authenticate through GitHub's OAuth flow.
- **Comments are public.** Anything posted is visible on GitHub Discussions.
- **Moderation** happens through the GitHub Discussions UI — lock, hide, or delete discussions as needed.

## Rollback

1. Set `"enabled": false` in `tools/comments_config.json`.
2. Run `python3 tools/rebuild_local.py`.
3. Commit and deploy.

## Relationship to other systems

- **Analytics (E24):** Comments do not trigger analytics events. The Giscus script is independent of GoatCounter.
- **Article metadata:** No per-article metadata changes are required. Comments are controlled at the repository level via `tools/comments_config.json`.

## What is not included

- Per-article comment enable/disable flags (possible future enhancement).
- Comment migration from other platforms.
- Self-hosted Giscus instance.
- Comment event tracking or moderation bots.
