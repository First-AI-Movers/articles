---
title: "RTK Preflight Checklist: What to Inspect Before `rtk init -g`"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/rtk-preflight-checklist-claude-code-2026"
published_date: "2026-03-23"
license: "CC BY 4.0"
---
# RTK Preflight Checklist: What to Inspect Before `rtk init -g`

## RTK is interesting for one reason: it goes after a real pain point.

Claude Code can burn context on noisy Bash output, and RTK’s model is straightforward. It uses a `PreToolUse` hook to rewrite commands like `git status` into `rtk git status`, then feeds Claude Code a compressed version of the output instead of the raw terminal dump. RTK’s own install flow also makes clear that a global setup can patch `~/.claude/settings.json`, add a hook under `~/.claude/hooks/rtk-rewrite.sh`, and uninstall cleanly later if needed. 

That makes RTK promising.

It also makes RTK something you should inspect like infrastructure, not install like a theme.

Claude Code’s official hooks docs are blunt: command hooks run with your user’s full permissions, execute shell commands automatically, and can modify, delete, or access anything your account can access. Anthropic explicitly tells users to review and test hook commands before adding them to configuration. On top of that, user settings in `~/.claude/settings.json` apply across all projects unless you deliberately scope changes to project or local settings. 

So before you run `rtk init -g`, use this RTK preflight checklist.

## 1. Confirm what problem you are actually trying to solve

RTK mainly helps when the waste comes from **Bash output**. That is an important distinction.

Claude Code hooks fire on lifecycle events like `PreToolUse`, and RTK’s architecture docs describe the rewrite path specifically around Bash commands. If your token bloat is coming from giant MCP responses, bloated project instructions, or constant file reads, RTK will only solve part of the problem. Anthropic also exposes `MAX_MCP_OUTPUT_TOKENS`, which directly caps MCP tool response size, so if MCP chatter is the issue, start there first. 

**Ask before install:**
- Is my waste mostly `pytest`, `git`, `docker logs`, `psql`, or `aws` output?
- Or is my waste mostly MCP, giant prompts, or long-lived sessions?

If the second answer is true, RTK is not your first lever.

## 2. Verify you are installing the real RTK, not a fake flow

This is not paranoia. It is 2026 hygiene.

Check Point disclosed patched Claude Code vulnerabilities in February 2026 involving malicious project configurations through hooks, MCP servers, and environment variables. Separate March 2026 reporting from Malwarebytes and Bitdefender documented fake Claude Code install pages and sponsored-search traps that pushed malicious one-liners to users through cloned documentation pages. 

**Before you install anything:**
- Navigate from the official RTK repo or official RTK site, not from a sponsored result.
- Do not trust a `curl ... | bash` one-liner just because the page looks real.
- Confirm the repo, maintainer, and install instructions match.

This sounds basic until it ruins a machine.

## 3. Check whether RTK is already installed

RTK’s own install docs make this a required step. They explicitly tell users to verify whether RTK is already present and to distinguish the correct RTK from other binaries with the same name. The docs recommend checking `rtk --version`, `rtk gain`, and `which rtk` before reinstalling. 

**Do this first:**

```
rtk --version
rtk gain
which rtk
```

If `rtk gain` already works, stop there and inspect the current installation before changing anything.

## 4. Decide your scope before you touch config

This is where most people get sloppy.

Anthropic’s settings model is hierarchical. User settings in `~/.claude/settings.json` apply to all projects. Project settings in `.claude/settings.json` are shared with collaborators. Local settings in `.claude/settings.local.json` stay personal to that repo and override broader scopes. More specific scopes win. [read](https://code.claude.com/docs/en/settings)

RTK’s install docs make the tradeoff explicit:

- `rtk init -g` installs globally
- `rtk init -g --hook-only` installs the hook globally without adding RTK context text
- `rtk init` keeps it local to one project [read](https://github.com/rtk-ai/rtk/blob/master/INSTALL.md)

**Rule of thumb:**

- Use **local** if you are evaluating.
- Use **global** only after you trust the behavior.
- Use **hook-only** if you want less context overhead and you already understand what the hook is doing.

## 5. Inspect exactly what RTK will write

Do not skip this.

RTK’s install docs say the conservative path is `rtk init -g --no-patch`, which prints the JSON snippet without patching your config. They also document that the normal setup can patch `settings.json`, create backups automatically, and install the hook registration entry. [read](https://github.com/rtk-ai/rtk/blob/master/INSTALL.md)

**Preflight move:**

```
rtk init -g --no-patch
```

Then inspect:

- the JSON snippet it wants to add
- whether it targets `PreToolUse`
- whether it points to `~/.claude/hooks/rtk-rewrite.sh`
- whether you are comfortable with that script being called inside your agent loop

If you do not want automatic patching, keep it manual.

## 6. Read the hook script like you would read CI or infra code

Anthropic’s docs are crystal clear here: hook commands execute with your full user permissions. Review and test them before adding them. [read](https://code.claude.com/docs/en/hooks)

That means the generated or installed hook is not “just part of the tool.” It is executable code in a trusted position. A thorough review, similar to what's performed in an AI Audit, ensures the tool aligns with your security and operational standards.

**Your hook review should answer:**

- What command gets rewritten?
- What gets passed through untouched?
- What happens on parser failure?
- Could the filter suppress useful debugging detail?
- Does it ever touch environment variables, temp files, or sensitive paths?
- Is there integrity checking?

RTK’s March 2026 changelog is a positive sign here. It added SHA-256 hook integrity verification and expanded support for AWS CLI and `psql`, with regression tests for command categories and rewrite behavior. That is good engineering. It is not a substitute for your own review. [read](https://github.com/rtk-ai/rtk/blob/master/CHANGELOG.md)

## 7. Pilot the commands that matter to your workflow

Do not evaluate RTK on toy examples.

Test the real commands that usually flood Claude Code in your environment:

- `pytest`
- `git status`
- `docker compose logs`
- `psql`
- `aws`

That list is not random. RTK’s changelog shows recent work specifically around AWS CLI and `psql`, which tells you both where it is improving and where behavior may still be evolving. [read](https://github.com/rtk-ai/rtk/blob/master/CHANGELOG.md)

**What you are measuring:**

- token reduction
- whether Claude still gets the right signal
- whether useful edge-case detail disappears
- whether debugging gets faster or worse

If it saves tokens but slows diagnosis, that is not a win.

## 8. Keep the rollback path ready before the install

A safe trial has an exit.

RTK documents automatic backups, uninstall support, and manual restore from `~/.claude/settings.json.bak`. Claude Code itself also keeps timestamped backups of configuration files and retains recent backups to prevent data loss. [read](https://github.com/rtk-ai/rtk/blob/master/INSTALL.md)

**That means your install plan should already include:**

```
rtk init -g --uninstall
cp ~/.claude/settings.json.bak ~/.claude/settings.json
```

If you do not know how you will remove it, you are not ready to add it.

## Bottom line

RTK deserves attention because it targets a real problem and appears to be shipping quickly with serious command coverage. But the thing you are really installing is not “token savings.” You are installing a hook-based rewrite layer into Claude Code’s execution path. Anthropic’s own docs say hooks run with full user permissions, user settings can apply globally, and command automation must be reviewed before trust. Recent Claude Code security disclosures and fake installer campaigns only make that more relevant. [read](https://code.claude.com/docs/en/hooks)

So the right move is simple:

**Audit first. Pilot second. Standardize last.**

That is how you evaluate RTK like an operator, not a tourist. This operator-first mindset is a core principle of effective AI Strategy Consulting, ensuring that new tools genuinely enhance your Workflow Automation Design rather than just adding complexity.

## Further Reading

- [Claude Desktop vs Terminal Config Guide](https://radar.firstaimovers.com/claude-desktop-vs-terminal-config-guide)
- [Claude Code vs Cowork macOS Playbook](https://radar.firstaimovers.com/claude-code-vs-cowork-macos-playbook)
- [Claude Desktop MCP Servers Guide 2026](https://radar.firstaimovers.com/claude-desktop-mcp-servers-guide-2026)
- [Agentic AI Systems vs Scripts 2026](https://radar.firstaimovers.com/agentic-ai-systems-vs-scripts-2026)

---

_Written by [Dr Hernani Costa](https://drhernanicosta.com), Founder and CEO of [First AI Movers](https://www.firstaimovers.com). Providing AI Strategy & Execution for Tech Leaders since 2016._

Subscribe to [First AI Movers](https://firstaimovers.com) for practical and measurable business strategies for Business Leaders. [First AI Movers](https://www.linkedin.com/company/first-ai-movers/) is part of [Core Ventures](https://coreventures.xyz).

**Ready to increase your business revenue?**
Book a [call](https://calendar.app.google/RJnKGg3b8ZRfhect5) today!

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/rtk-preflight-checklist-claude-code-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*