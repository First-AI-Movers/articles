---
title: "Keep Claude Native on Desktop and Experimental in the Terminal"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/claude-desktop-vs-terminal-config-guide"
published_date: "2026-03-23"
license: "CC BY 4.0"
---
# Keep Claude Native on Desktop and Experimental in the Terminal

## How do you keep the desktop experience on real Claude, while using the terminal for cheaper or experimental models?

For anyone using Claude Code seriously, this Claude Code configuration question shows up fast. Claude Code now runs across the terminal, IDEs, desktop, and browser. It also uses a real settings hierarchy: user settings in `~/.claude/settings.json`, project settings in `.claude/settings.json`, and personal project overrides in `.claude/settings.local.json`. On top of that, the `env` block in settings applies environment variables to every session, not just one shell window. 

That is why people accidentally wreck a clean setup.

They add OpenRouter globally, test one model in the CLI, and suddenly everything feels off. Their desktop sessions are no longer clearly native. Their auth path gets muddy. MCP behavior changes. Then they wonder whether Claude, OpenRouter, or their shell is the problem.

Here is the cleaner way to think about it.

## The Claude Code Configuration Mistake Most People Make

The common mistake is treating routing variables like a harmless convenience.

They are not.

In Claude Code, `ANTHROPIC_API_KEY` is especially powerful. When it is set, Claude Code uses that key instead of your Claude Pro, Max, Team, or Enterprise subscription. Anthropic also documents that `ANTHROPIC_BASE_URL` overrides the API endpoint, and when it points to a non-first-party host, MCP tool search is disabled by default unless you explicitly re-enable it. 

That means a global gateway setup is not just “one more option.” It changes the behavior of your overall Claude Code environment.

So the real goal is not “make OpenRouter work.”

The real goal is **contain the routing change to the exact sessions where you want it**.

## What the official docs actually support

Anthropic’s docs are clear on the baseline. Claude Code supports logging in with Claude.ai accounts, including Pro and Max, and it supports multiple surfaces, including terminal and desktop. If your account supports it, Opus 4.6 and Sonnet 4.6 can expose a **1M token context window**, with availability depending on plan and model selection. You can inspect the active model with `/status`, and the same command also shows account and connectivity information. 

OpenRouter’s Claude Code integration guide is also clear. Their recommended connection method is:

- `ANTHROPIC_BASE_URL="https://openrouter.ai/api"`
- `ANTHROPIC_AUTH_TOKEN="<your OpenRouter key>"`
- `ANTHROPIC_API_KEY=""`

They explicitly recommend checking the connection with `/status`. 

So yes, the routing pattern is real.

But there is an important caveat.

OpenRouter also states that **Claude Code with OpenRouter is only guaranteed to work with Anthropic first-party providers**, and that Claude Code is optimized for Anthropic models and may not work correctly with other providers. That is the part many people skip when they jump straight to `qwen/qwen3-coder:free` or another non-Anthropic model. 

That does not mean experimentation is impossible.

It means you should treat non-Anthropic models inside Claude Code as **experimental**, not as the baseline you build your daily workflow on.

## The clean split that actually works

If your goal is:

- **Desktop app:** real Anthropic login, premium Claude quality, clean native experience
- **Terminal:** cheap or experimental sessions on demand

then the most reliable pattern is this:

### 1. Keep your user-level Claude settings neutral

Do not hardwire gateway routing into `~/.claude/settings.json` unless you want it everywhere.

A minimal user file is enough:

```
{
  "env": {}
}
```

That keeps your global user scope clean and avoids pushing routing variables into every Claude Code session. The reason this matters is simple: the `env` block in settings is applied to every session. [read](https://code.claude.com/docs/en/settings)

### 2. Use shell-scoped launch functions for the terminal

This is the part most people should copy.

Put this in `~/.zshrc` or `~/.bashrc`:

```
# Native Claude session in the terminal
claude_native() {
  env -u ANTHROPIC_BASE_URL \
      -u ANTHROPIC_AUTH_TOKEN \
      -u ANTHROPIC_API_KEY \
      -u ANTHROPIC_MODEL \
      claude "$@"
}

# Experimental OpenRouter session in the terminal
claude_free() {
  ANTHROPIC_BASE_URL="https://openrouter.ai/api" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_API_KEY="" \
  ANTHROPIC_MODEL="qwen/qwen3-coder:free" \
  claude "$@"
}
```

Then reload your shell:

```
source ~/.zshrc
```

Now your split is intentional:

```
claude_native
claude_free
```

This works because the routing change is no longer global. It only exists for the shell session that launches `claude_free`. Anthropic documents that `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and `ANTHROPIC_MODEL` control routing and model behavior, while OpenRouter documents the exact base URL and auth pattern Claude Code expects. [read](https://code.claude.com/docs/en/env-vars)

### 3. Use project-local settings only for project experiments

Claude Code supports `.claude/settings.local.json` as a personal, gitignored, repo-specific override. That is useful if you want one repository to behave differently from the rest of your machine. [read](https://docs.anthropic.com/de/docs/claude-code/settings)

Example:

```
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
    "ANTHROPIC_AUTH_TOKEN": "${OPENROUTER_API_KEY}",
    "ANTHROPIC_API_KEY": "",
    "ANTHROPIC_MODEL": "qwen/qwen3-coder:free"
  }
}
```

But here is the practical truth: **project-local settings are good for per-repo experiments, not for a clean desktop-versus-terminal split**.

If your goal is surface separation, shell-scoped launch functions are cleaner.

## The caveat nobody should ignore

If you want the CLI to run through OpenRouter **and** stay highly reliable inside Claude Code, the safer move is to route **Anthropic models through OpenRouter**, not Qwen or DeepSeek first.

OpenRouter’s own docs say Claude Code compatibility is only guaranteed with Anthropic first-party providers, and they even show the recommended model overrides using Anthropic model IDs like `anthropic/claude-opus-4.6` and `anthropic/claude-sonnet-4.6`. Anthropic also supports custom model entries and explicit model environment variables for gateway deployments, which is useful if you want controlled routing without losing the normal Claude model picker behavior. [read](https://openrouter.ai/docs/guides/guides/coding-agents/claude-code-integration)

So the mature version of this stack looks like this:

-   **Desktop:** native Claude login
-   **Terminal default:** native Claude
-   **Terminal experimental:** OpenRouter with a non-Anthropic model only when you are explicitly testing
-   **Terminal routed but stable:** OpenRouter with Anthropic models when you want budget controls, failover, or usage visibility without leaving the Claude family

That is a much better operational model than turning your whole machine into a permanent gateway experiment.

## How to verify your setup in 30 seconds

Once you launch either mode, check it.

Run:

```
/status
```

Anthropic documents `/status` as the place to see version, model, account, and connectivity. OpenRouter’s Claude Code guide specifically shows `/status` reflecting the OpenRouter base URL and auth token when the routing is active. [read](https://code.claude.com/docs/en/commands)

If you are using premium Claude and want long-context work, check your model selection too. Anthropic documents that supported accounts can use 1M context variants like `opus[1m]` and `sonnet[1m]`. [read](https://code.claude.com/docs/en/model-config)

## My take

This approach aligns with professional **AI Tool Integration** principles: keep your best workflow boring and your experimental workflow isolated.

That means:

-   keep user-level config clean
-   route the terminal per session
-   treat non-Anthropic models in Claude Code as experiments
-   use `/status` every time you change routing
-   keep native Claude available at all times

If you do that, you get exactly what most serious builders want:

**real Claude when quality matters, experimental models when cost or curiosity matters, and far less configuration chaos in between.**

## Further Reading

- [Claude Code vs Cowork macOS Playbook](https://radar.firstaimovers.com/claude-code-vs-cowork-macos-playbook)
- [Claude Desktop MCP Servers Guide 2026](https://radar.firstaimovers.com/claude-desktop-mcp-servers-guide-2026)
- [EdenAI vs OpenRouter 2025: Complete Guide](https://www.linkedin.com/pulse/edenai-vs-openrouter-2025-complete-guide-dr-hernani-costa-0lgse)
- [Claude Browser Agent SEO Workflows 2026](https://radar.firstaimovers.com/claude-browser-agent-seo-workflows-2026)

---

_Written by [Dr Hernani Costa](https://drhernanicosta.com), Founder and CEO of [First AI Movers](https://www.firstaimovers.com). Providing AI Strategy & Execution for Tech Leaders since 2016._

Subscribe to [First AI Movers](https://firstaimovers.com) for practical and measurable business strategies for Business Leaders. [First AI Movers](https://www.linkedin.com/company/first-ai-movers/) is part of [Core Ventures](https://coreventures.xyz).

**Ready to increase your business revenue?**
Book a [call](https://calendar.app.google/RJnKGg3b8ZRfhect5) today!

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/claude-desktop-vs-terminal-config-guide) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*