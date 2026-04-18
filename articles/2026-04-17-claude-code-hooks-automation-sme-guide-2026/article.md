---
title: "Claude Code Hooks: Automate Dev Team Workflows in 2026"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/claude-code-hooks-automation-sme-guide-2026"
published_date: "2026-04-17"
license: "CC BY 4.0"
---
> **TL;DR:** Learn how Claude Code hooks work and 5 practical automation patterns for SME dev teams: linting, testing, Slack alerts, audit logs, and more.

Claude Code is already useful as an AI coding assistant, but most SME teams use it reactively. You type a prompt, Claude edits a file, you check the result. That is a fine start, but it leaves your team re-running the same manual steps after every AI-assisted change: running the linter, triggering tests, pasting a Slack update to the team. Claude Code hooks change this equation. They let you attach shell commands to specific lifecycle events so the routine work runs automatically, every time, without your team having to remember. For a 10-person dev team shipping fast, that difference adds up across hundreds of daily interactions.

This guide explains what hooks are, how to configure them in `settings.json`, and covers five concrete automation patterns you can adopt this week.

## What Are Claude Code Hooks

Hooks are user-defined shell commands that Claude Code executes at defined points in its lifecycle. They are not AI features. They are deterministic scripts. Claude Code fires them at the right moment; your script does the work.

The lifecycle events Claude Code exposes are:

- **PreToolUse**: runs before Claude uses any tool (file write, bash command, etc.)
- **PostToolUse**: runs after a tool call completes
- **Stop**: runs when Claude finishes a response or task
- **SessionStart**: runs when a new session opens
- **SessionEnd**: runs when a session closes

Each hook receives context about what just happened as a JSON payload over stdin. Your script can read that payload, take action, and optionally write output back to Claude. If a hook exits with a non-zero code, Claude Code treats it as a signal that something went wrong.

## How to Configure Hooks in settings.json

Hooks live in your Claude Code `settings.json` file. Depending on whether you want them per-project or across your whole machine, the file is at `.claude/settings.json` in your project root (project-level) or `~/.claude/settings.json` (global).

A minimal hook configuration looks like this:

```
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint"
          }
        ]
      }
    ]
  }
}
```

The `matcher` field filters which tool calls trigger the hook. You can match on tool names like `Write`, `Edit`, `Bash`, or use `"*"` to catch everything.

That is the full configuration model. No build step, no plugin registry. You edit JSON, save the file, and the next Claude Code session picks it up.

## Pattern 1: Auto-Lint Before Every File Write

The most common source of noise in AI-assisted coding is style drift. Claude writes valid code that fails your linter because it does not know your project's exact ESLint or Flake8 configuration. A PreToolUse hook solves this by running the linter on the target file before Claude commits the change.

```
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "eslint --fix \"$CLAUDE_TOOL_INPUT_PATH\" 2>&1 || true"
          }
        ]
      }
    ]
  }
}
```

The `|| true` prevents the hook from blocking Claude on auto-fixable warnings. For errors that cannot be auto-fixed, remove `|| true` and Claude Code will surface the failure before the write lands.

This pattern eliminates the round-trip where a developer reviews an AI change, runs lint, finds five style issues, and has to prompt Claude again to fix them.

## Pattern 2: Run Tests After Code Changes

Tests should run after every substantive edit. Most teams skip this in practice because manually triggering test suites mid-session breaks flow. A PostToolUse hook on `Edit` or `Write` events keeps tests running continuously without developer intervention.

```
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20"
          }
        ]
      }
    ]
  }
}
```

The `-x` flag stops pytest at the first failure so you get fast feedback. The `tail -20` keeps the output readable inside Claude Code's interface.

For a TypeScript project, swap in `npx jest --passWithNoTests --bail 2>&1 | tail -20`. The pattern is identical; only the test runner changes.

## Pattern 3: Slack Notifications When Claude Completes a Task

Claude Code hooks at the `Stop` event give you a clean signal that Claude has finished responding. For SME teams where developers work across time zones or where one developer kicks off a long AI-assisted refactor and steps away, a Slack notification on completion is genuinely useful.

```
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -X POST -H 'Content-type: application/json' --data '{\"text\":\"Claude Code task complete in project: '\"$CLAUDE_PROJECT_NAME\"'\"}' $SLACK_WEBHOOK_URL"
          }
        ]
      }
    ]
  }
}
```

Store `SLACK_WEBHOOK_URL` in your environment via Doppler or your existing secrets manager. Never hardcode it in `settings.json`.

You can make this smarter by reading the Claude session summary from the stdin payload and including the task description in the Slack message. That turns a simple ping into a lightweight async standup: the team sees what Claude worked on even if the developer is offline.

## Pattern 4: Audit Logging for Every Tool Call

This pattern has practical relevance beyond developer productivity. Under the EU AI Act's transparency requirements and general GDPR accountability principles, teams using AI tools in software development may need to demonstrate what actions the AI system took and when. A PostToolUse hook that appends a structured JSON log line to a file gives you that trail without any external service dependency.

```
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"{\\\"ts\\\": \\\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\", \\\"tool\\\": \\\"$CLAUDE_TOOL_NAME\\\", \\\"project\\\": \\\"$CLAUDE_PROJECT_NAME\\\", \\\"user\\\": \\\"$USER\\\"}\" >> ~/.claude/audit.log"
          }
        ]
      }
    ]
  }
}
```

Each tool call appends one JSON line. The log captures the timestamp, tool name, project, and local user. For a team of five developers, this produces a searchable record of every file Claude wrote, every bash command it ran, and every read operation it performed.

For stricter audit requirements, replace the local file write with a POST to an internal logging endpoint or a write to an append-only S3 bucket with object lock enabled.

## Pattern 5: Auto-Format After Every Edit

Code formatting is the task developers are most likely to skip under time pressure and most likely to argue about in code review. A PostToolUse hook on `Write` that runs Prettier, Black, or gofmt after every edit removes the decision entirely.

```
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$CLAUDE_TOOL_INPUT_PATH\" 2>/dev/null; black \"$CLAUDE_TOOL_INPUT_PATH\" 2>/dev/null; true"
          }
        ]
      }
    ]
  }
}
```

Running both Prettier and Black in the same command is safe: Prettier handles JS/TS/CSS/JSON; Black handles Python. Non-matching files are silently skipped. The trailing `; true` ensures the hook never blocks Claude regardless of formatter exit codes.

This pattern pairs well with Pattern 1. Lint catches logical issues; auto-format handles style. Both run without the developer doing anything.

## Combining Patterns: A Practical settings.json for SME Teams

In practice, you will combine several of these patterns in one file. A production-ready `settings.json` for a Python and TypeScript monorepo might include:

- PreToolUse lint on Write events
- PostToolUse test run on Edit events
- PostToolUse audit log on all events
- Stop notification on all events

The order matters when multiple hooks fire on the same event. Claude Code executes them in the order they appear in the array. Put your fastest, most critical hooks first so failures surface quickly.

## Getting Your Team Started

The practical path for a 10-to-50 person dev team is to start with two hooks: audit logging (always on, zero friction) and auto-format (saves the most time per developer per day). Commit the project-level `.claude/settings.json` to your repo so every developer gets the same hooks automatically when they clone the project.

For hooks that require secrets (Slack webhooks, internal API endpoints), use environment variable references rather than hardcoded values and inject them through your existing secrets manager. This keeps `settings.json` safe to commit.

Review your audit log after two weeks. The data will show you which tools Claude uses most frequently, which projects generate the most activity, and where manual follow-up steps still persist despite the hooks. That data is the input for the next round of automation.

Need help designing a Claude Code workflow that fits your team's security and compliance requirements? [Talk to First AI Movers.](https://radar.firstaimovers.com/page/ai-consulting)

## Frequently Asked Questions

### Do hooks run in every Claude Code session, including CI environments?

Yes, hooks defined in `.claude/settings.json` at the project level run in any Claude Code session opened in that project directory, including automated or headless sessions. If you run Claude Code in a CI pipeline, the same hooks fire. Make sure your hook commands are available in the CI environment and that any required environment variables (such as Slack webhook URLs) are injected through your CI secrets manager.

### Can hooks slow down Claude Code if the commands take too long?

Yes. A hook that runs a full test suite on every file write will noticeably slow down interactive sessions. Use scoped test runs rather than full suites. Pass the modified file path to the test runner and run only the tests covering that file. Claude Code does not currently impose a timeout on hook execution, so a long-running command will block until it completes.

### Is there a way to test hooks without affecting my main project?

The cleanest approach is to create a separate directory with a minimal `.claude/settings.json` and run Claude Code there first. You can also temporarily add `echo` statements at the start of hook commands to confirm they are firing and receiving the expected environment variables before wiring in the real logic.

## Further Reading

- [Claude Code Agent Skills and Plugins for European Teams](https://radar.firstaimovers.com/claude-code-agent-skills-plugins-european-teams-2026)
- [Claude Code vs GitHub Copilot: European SME Comparison 2026](https://radar.firstaimovers.com/claude-code-vs-github-copilot-european-sme-2026)
- [Should You Deploy Claude Code Across Your Entire Dev Team?](https://radar.firstaimovers.com/should-you-deploy-claude-code-entire-dev-team-2026)

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Claude Code Hooks: Automate Dev Team Workflows in 2026",
  "description": "Learn how Claude Code hooks work and 5 practical automation patterns for SME dev teams: linting, testing, Slack alerts, audit logs, and more.",
  "datePublished": "2026-04-17T22:16:40.374000+00:00",
  "dateModified": "2026-04-17T22:16:40.374000+00:00",
  "author": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://radar.firstaimovers.com/favicon.ico"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://radar.firstaimovers.com/claude-code-hooks-automation-sme-guide-2026"
  },
  "image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200&h=630&fit=crop&q=80"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Do hooks run in every Claude Code session, including CI environments?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, hooks defined in `.claude/settings.json` at the project level run in any Claude Code session opened in that project directory, including automated or headless sessions. If you run Claude Code in a CI pipeline, the same hooks fire. Make sure your hook commands are available in the CI environm..."
      }
    },
    {
      "@type": "Question",
      "name": "Can hooks slow down Claude Code if the commands take too long?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. A hook that runs a full test suite on every file write will noticeably slow down interactive sessions. Use scoped test runs rather than full suites. Pass the modified file path to the test runner and run only the tests covering that file. Claude Code does not currently impose a timeout on ho..."
      }
    },
    {
      "@type": "Question",
      "name": "Is there a way to test hooks without affecting my main project?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The cleanest approach is to create a separate directory with a minimal `.claude/settings.json` and run Claude Code there first. You can also temporarily add `echo` statements at the start of hook commands to confirm they are firing and receiving the expected environment variables before wiring in..."
      }
    }
  ]
}
</script>
-->

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/claude-code-hooks-automation-sme-guide-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*