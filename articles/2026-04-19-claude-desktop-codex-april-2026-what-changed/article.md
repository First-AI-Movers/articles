---
title: "Claude Desktop Redesign and Codex April 2026: What Actually Changed and What It Means for Your Engineering Workflow"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/claude-desktop-codex-april-2026-what-changed"
published_date: "2026-04-19"
license: "CC BY 4.0"
---
> **TL;DR:** What shipped in the April 2026 Claude Desktop redesign and Codex update, Routines, computer use, parallel agents, and what it means for your team.

Two platform-defining releases landed in the same week. On April 14, Anthropic [redesigned the Claude Desktop app for parallel agents](https://claude.com/blog/claude-code-desktop-redesign) and launched Routines, scheduled cloud agents that run without your laptop. Three days later, OpenAI [updated Codex](https://openai.com/index/codex-for-almost-everything/) with computer use, an in-app browser, persistent memory, and over 90 new plugins.

Both moves signal the same shift: AI coding tools are becoming operating systems, not editors. Here is what actually shipped, what is still in preview, and what it changes for engineering teams.

---

## What Anthropic Shipped (April 14)

### Claude Desktop Redesign

The desktop app was rebuilt from the ground up to support parallel agent sessions. The key changes:

- **Multi-session sidebar.** Every active and recent session in one place. Filter by status, project, or environment. Group by project. Resume any session instantly.
- **Drag-and-drop workspace.** Arrange panes for terminal, file editor, diff viewer, and HTML/PDF preview side by side. The layout adapts to how you work, not the other way around.
- **Integrated terminal and file editor.** Edit files and run commands inside the app. No more switching between Claude and your terminal.
- **Side-chat shortcut (Cmd + ;).** Branch a quick question off a running task without losing context.
- **Three view modes.** Verbose (full tool-call transparency), Normal (balanced), and Summary (just the results).

The redesign is not cosmetic. It reflects a shift in how Anthropic expects developers to use Claude Code: not one conversation at a time, but [multiple agents running in parallel](https://radar.firstaimovers.com/one-coding-agent-or-two-lane-stack-2026) with the developer in the orchestrator seat.

### Routines (Research Preview)

Routines are the bigger strategic move. A Routine is a saved cloud agent configuration, a prompt, one or more repositories, environment settings, and connectors, with triggers that start runs automatically.

**Three trigger types:**

| Trigger | How it works | Example use |
|---|---|---|
| **Scheduled** | Hourly, daily, nightly, weekdays, or weekly | Nightly triage of open issues, weekly dependency audit |
| **API** | HTTP POST to a per-routine endpoint with a bearer token | Trigger from CI pipeline, Slack bot, or internal tool |
| **GitHub** | pull_request.opened, push, issues, releases, check_run | Auto-review PRs, label issues, generate release notes |

A single Routine can combine all three trigger types simultaneously.

**Daily run limits by plan:**

| Plan | Daily runs |
|---|---|
| Pro | 5 |
| Max | 15 |
| Team | 25 |
| Enterprise | 25+ (extra usage available) |

Routines execute on Anthropic's cloud infrastructure, not your laptop. A nightly bug triage or a scheduled test report runs at 2:00 AM without your machine being open.

## What OpenAI Shipped (April 17)

### Computer Use (macOS)

Codex can now operate your desktop, seeing your screen, clicking, and typing with its own cursor while running in the background. This is not screen sharing. It is autonomous desktop control.

Initial availability is macOS only. EU and UK users will get access later.

**What this means practically:** Codex can interact with apps that have no API. Paste data between applications. Click through multi-step workflows in tools like Figma, Excel, or internal admin panels. The use cases extend well beyond code.

### In-App Browser

The Codex app now includes an early browser that can open local or public pages. You can comment directly on the rendered page and ask Codex to address page-level feedback.

### Memory and Multi-Day Persistence

Codex can now schedule future work for itself and resume long-running tasks across days or weeks. Thread reuse preserves context previously built up, so a task started on Monday can continue on Wednesday with full awareness of what happened before.

### 90+ New Plugins

The plugin ecosystem expanded significantly: Atlassian Rovo (JIRA), CircleCI, CodeRabbit, GitLab Issues, Microsoft Suite, Neon by Databricks, Remotion, Render, and dozens more. Combined with computer use, Codex is positioning itself as a universal translator for enterprise software.

## What This Changes for Engineering Teams

### 1. The approval surface just expanded

Both platforms now execute work autonomously, Routines on Anthropic's cloud, Codex automations locally with desktop control. For engineering leaders managing [AI security posture](https://radar.firstaimovers.com/ai-security-posture-engineering-organisation), this is a new governance surface. Agents that run on schedules or respond to GitHub events need the same approval rigour as production deployments.

### 2. Shadow AI gets easier

Routines are trivial to set up. A developer can create a Routine that monitors a repository, triages issues, or generates reports, all without the CTO knowing. Teams that have not yet addressed [shadow AI detection](https://radar.firstaimovers.com/shadow-ai-engineering-teams-detect-measure-decide) will find the problem accelerating.

### 3. The orchestrator role is real

Both apps are designed for developers managing multiple parallel agents. The sidebar, the workspace panes, the trigger configurations, these are orchestration UIs, not chat interfaces. The developer who learns to orchestrate well will outperform the one who talks to one agent at a time.

### 4. Platform lock-in is forming

Routines are Claude-only. Computer use is Codex-only. Memory and thread persistence are Codex-only. The plugin ecosystems are different. Teams that invest deeply in one platform's automation layer will find switching costly. This is the early stage of the lock-in cycle that both Anthropic and OpenAI are designing for.

## What Is Still Missing

- **Routines are research preview.** Expect breaking changes, quota adjustments, and feature gaps.
- **Computer use has no detailed permission model.** Enterprise adoption requires guardrails that OpenAI has not yet published.
- **Neither platform has cross-platform interop.** You cannot trigger a Claude Routine from a Codex automation or vice versa.
- **Pricing is consumption-based.** Both platforms meter Routine/automation runs against subscription limits. At scale, costs are unpredictable.

## Frequently Asked Questions

### Are Claude Routines the same as GitHub Actions?

No. GitHub Actions runs shell scripts and containers triggered by repository events. Claude Routines runs an AI agent with full Claude Code capabilities, it can read code, write changes, create PRs, and make judgment calls. Routines are closer to "a senior developer on call" than "a CI pipeline step."

### Can Codex computer use access my passwords and private data?

Codex processes screen content locally where possible and triggers human-in-the-loop verification for actions that affect system stability or data privacy. However, the detailed permission model is not yet published. Until it is, treat computer use as a capability that requires explicit organisational approval before enabling.

### Which platform should my team choose?

Neither has won. Claude leads on code quality and agent reasoning. Codex leads on ecosystem breadth and desktop integration. If your team uses Claude Code today, Routines are the natural next step. If your team uses Codex/ChatGPT, the computer use and plugin expansion are the draw. Both platforms will continue to leapfrog each other.

### Do Routines use my subscription tokens?

Yes. Routines draw from the same usage pool as interactive sessions. When a Routine runs at 2:00 AM, it consumes the same capacity as if you were chatting with Claude at your desk. Plan accordingly.

## Further Reading

- [How to Build an AI Security Posture for Your Engineering Organisation](https://radar.firstaimovers.com/ai-security-posture-engineering-organisation)
- [Shadow AI in Engineering Teams: How to Detect It, Measure It, and Decide](https://radar.firstaimovers.com/shadow-ai-engineering-teams-detect-measure-decide)
- [One Coding Agent or Two-Lane Stack? How Technical Leaders Should Decide](https://radar.firstaimovers.com/one-coding-agent-or-two-lane-stack-2026)
- [How Technical Leaders Should Choose an AI Coding Agent in 2026](https://radar.firstaimovers.com/how-technical-leaders-should-choose-an-ai-coding-agent-2026)

## Understand What These Changes Mean for Your Team

If your engineering team is using Claude Code or Codex and you are not sure how Routines, computer use, or autonomous agents change your governance requirements, the first step is a structured assessment.

Our [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) evaluates your current AI tool posture, what is in use, what controls exist, and what gaps these new capabilities create.

If you need help designing the operating model for scheduled agents and autonomous desktop control, our [AI Consulting](https://radar.firstaimovers.com/page/ai-consulting) services can help you build a framework that scales with the platform evolution.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Claude Desktop Redesign and Codex April 2026: What Actually Changed and What It Means for Your Engineering Workflow",
  "description": "What shipped in the April 2026 Claude Desktop redesign and Codex update, Routines, computer use, parallel agents, and what it means for your team.",
  "datePublished": "2026-04-19T16:34:40.401638+00:00",
  "dateModified": "2026-04-19T16:34:40.401638+00:00",
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
    "@id": "https://radar.firstaimovers.com/claude-desktop-codex-april-2026-what-changed"
  },
  "image": "https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=1200&h=630&fit=crop&q=80"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Are Claude Routines the same as GitHub Actions?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. GitHub Actions runs shell scripts and containers triggered by repository events. Claude Routines runs an AI agent with full Claude Code capabilities, it can read code, write changes, create PRs, and make judgment calls. Routines are closer to "a senior developer on call" than "a CI pipeline s..."
      }
    },
    {
      "@type": "Question",
      "name": "Can Codex computer use access my passwords and private data?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Codex processes screen content locally where possible and triggers human-in-the-loop verification for actions that affect system stability or data privacy. However, the detailed permission model is not yet published. Until it is, treat computer use as a capability that requires explicit organisat..."
      }
    },
    {
      "@type": "Question",
      "name": "Which platform should my team choose?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Neither has won. Claude leads on code quality and agent reasoning. Codex leads on ecosystem breadth and desktop integration. If your team uses Claude Code today, Routines are the natural next step. If your team uses Codex/ChatGPT, the computer use and plugin expansion are the draw. Both platforms..."
      }
    },
    {
      "@type": "Question",
      "name": "Do Routines use my subscription tokens?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Routines draw from the same usage pool as interactive sessions. When a Routine runs at 2:00 AM, it consumes the same capacity as if you were chatting with Claude at your desk. Plan accordingly."
      }
    }
  ]
}
</script>
-->

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/claude-desktop-codex-april-2026-what-changed) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*