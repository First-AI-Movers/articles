---
title: "Claude Code Across Every Device: Remote Control, Dispatch, and Agent View Explained"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/claude-code-remote-control-dispatch-multi-device-guide-2026-v2"
published_date: "2026-05-24"
license: "CC BY 4.0"
---

Claude Code now runs across your terminal, desktop app, phone, and browser, and sessions stay in sync across all of them. If you have been managing multiple Claude Code sessions by switching terminal tabs and losing track of which agent is doing what, there are three features that change everything: **Remote Control** (continue any local session from your phone), **Dispatch** (start new tasks from your phone that run on your desktop), and **Agent View** (a single dashboard for every session at once). Most developers are using at most one of these. Using all three together is the workflow that makes parallel agent management sustainable.

This guide covers the practical setup, the differences between each feature, and the recommended workflow for engineering teams running multiple agents daily. For CTOs, engineering managers, and founders running 3+ parallel agents, the question is whether multi-device coordination becomes a sustainable operating model or a Friday-evening firefight.

---

## The Two Environments You Need to Understand

Before anything else, understand the distinction that explains why some sessions have full access and others do not.

**Cold / cloud environment**: Sessions running on Anthropic's servers (claude.ai/code or the mobile Code tab without Remote Control).
- Runs even when your laptop sleeps
- No access to your local files, git repos, MCP servers, or terminal tools
- Every session starts fresh; no persistent workspace

**Local / warm environment**: Sessions running on your machine (CLI, desktop app).
- Full filesystem access, git, MCP servers, terminal tools
- This is where real work happens
- Remote Control and Dispatch connect your phone to these sessions

The entire multi-device architecture exists to give you remote access to your local environment from anywhere, without moving your code to the cloud.

---

## Feature 1: Remote Control (continue any local session from your phone)

Remote Control turns your phone into a remote terminal for an already-running local Claude Code session. Your session stays local; the phone is just a window into it.

### Setup (One-Time)

**Requirements:** Claude Code v2.1.51 or later. Available on all plans. Research preview.

**Option A. Enable by default:**
```
# In any Claude Code session:

> **TL;DR:** How to run Claude Code sessions across mobile, desktop, and CLI. Remote Control, Dispatch, and Agent View explained with practical setup steps.

/config

# Or in settings:
# Desktop app → Settings → "Enable remote control by default"
```

**Option B. Per-session:**
```
# Start a new session with remote control:
claude --remote-control

# Or enable inside an existing session:
/remote-control

# Optionally name it for easy identification:
claude --remote-control --name "Refactoring auth module"
```

A URL and QR code appear. Press spacebar to toggle the QR code display.

### Continue on Mobile

1. Open the Claude app on your phone
2. Tap the **Code** tab at the bottom
3. Your Remote Control sessions appear in the list. Look for the computer icon with a green dot (= online)
4. Tap the session → you are now chatting directly into the same local session
5. Type prompts, approve file edits, run commands; everything stays in sync in real time

### Key Behaviors

- **Real-time sync.** Your mobile message appears instantly in the terminal (and in Agent View if open). Vice versa: terminal output streams to your phone.
- **Survives sleep.** If your laptop sleeps, the session reconnects when it wakes. The phone shows it as offline (grey dot) until reconnection.
- **Multiple sessions.** You can Remote Control multiple sessions simultaneously. Each appears as a separate entry in the mobile Code tab.
- **Device switching.** Switch between phone, browser (claude.ai/code), and terminal freely. All see the same session state.

---

## Feature 2: Dispatch (start tasks from your phone that run on your desktop)

Dispatch is different from Remote Control. Remote Control connects to an existing session. Dispatch lets you fire off entirely new tasks from your phone, and Claude spawns the right session on your desktop to handle them.

### Setup (One-Time)

1. Update the Claude Desktop app and mobile app to latest versions
2. On Desktop: Go to **Cowork tab → Dispatch setup** → scan QR code or follow pairing
3. Keep your computer awake (Dispatch needs the desktop app running)
4. On mobile: a new **Dispatch** option appears

### How It Works

1. On your phone, open the Dispatch chat
2. Type a task: "Fix the login bug in the auth module" or "Summarise last night's work"
3. Claude decides:
- Development task → spawns a **Code** session on your desktop
- Other tasks → spawns a **Cowork** session
1. You get push notifications when it finishes or needs input
2. Results appear in the desktop sidebar with a "Dispatch" badge

### When to Use Dispatch vs Remote Control

| Scenario | Use This |
|---|---|
| You started a task on your laptop, stepped away, want to continue from phone | **Remote Control** |
| You are away from your desk and want to start a completely new task | **Dispatch** |
| You want to monitor multiple running sessions from your phone | **Remote Control** (all sessions visible in Code tab) |
| You want to delegate a task and get notified when it is done | **Dispatch** (push notifications) |

**Simple rule:** Remote Control = continue. Dispatch = create.

---

## Feature 3: Agent View (one dashboard for every session)

Agent View is the dashboard that makes parallel sessions manageable. Before Agent View (shipped May 11, 2026), running 4-5 parallel Claude Code sessions meant a tmux grid, constant tab-switching, and a mental ledger of which agent was doing what.

### How to Open It

```
# From any terminal:
claude agents

# Or from inside any Claude Code session:
# Press the left arrow key
```

### What You See

A TUI (terminal user interface) table showing every Claude Code session:

| Column | What It Shows |
|---|---|
| Session name | The task or file being worked on |
| Last response | Most recent Claude output (truncated) |
| Timestamp | When the last activity happened |
| Status | Whether the agent needs your input (waiting / working / done) |

### Key Commands Inside Agent View

| Action | How |
|---|---|
| Reply to a session | Select it → type your response → send without leaving the dashboard |
| Jump into a session | Select it → press Enter → full session view |
| Push current session to background | `/bg` inside any session |
| Start a new background session | `claude --bg "Write tests for auth module"` |
| Peek at a session without entering | Select it → the preview pane shows recent output |

### The Workflow That Scales

```
# Start 3 background tasks:
claude --bg "Refactor the database module"
claude --bg "Write integration tests for the API"
claude --bg "Review and fix lint warnings"

# Open the dashboard:
claude agents

# Monitor all 3 from one screen.
# Reply to whichever needs input.
# Jump in when one finishes for final review.
```

This is how you run 5-10 parallel agents without losing your mind. The dashboard tells you which ones need you, so you are not context-switching; you are triaging.

---

## The Full Connection Map

How every Claude Code surface connects to every other:

| Start Here | → Mobile | → Desktop App | → CLI / Agent View | → Web (claude.ai/code) |
|---|---|---|---|---|
| **CLI session** | Remote Control (Code tab) | `/desktop` command | Native (Agent View) | Remote Control |
| **Desktop app session** | Dispatch chat | Native sidebar | `/teleport` or Remote Control | Dispatch routes to it |
| **Cloud / cold session** | Default Code tab | "Continue in Desktop" | `claude --teleport` | Native |
| **Mobile Dispatch** | Same chat | Spawns Desktop session | Appears via Remote Control | Via web |

### Key Commands for Moving Sessions

| Command | What It Does |
|---|---|
| `/teleport` or `claude --teleport` | Pulls a cloud session onto your local machine |
| `/remote-control` | Turns any local session into a remotely accessible one |
| `/desktop` | Pulls a CLI session into the Desktop app |
| `/bg` | Pushes the current session to background (stays running) |
| `claude --bg "<task>"` | Starts a new background session |
| `claude agents` | Opens Agent View dashboard |

---

## Recommended Workflow for Engineering Teams

This is the workflow most power users converge on:

### Morning: Start Your Agents

```
# On your laptop, start background tasks for the day:
claude --bg --name "Morning: Review PRs" "Review all open PRs and summarise"
claude --bg --name "Refactor: Auth module" "Refactor the auth module per CLAUDE.md"
claude --bg --name "Tests: API coverage" "Write missing integration tests for /api/*"

# Enable remote control on all (or set as default in /config)

# Open Agent View to see everything:
claude agents
```

### Midday: Continue from Phone

```
# Walk away from your desk.
# Open Claude app → Code tab → see all 3 sessions with green dots.
# Tap "Morning: Review PRs" → it is finished → read the summary.
# Tap "Refactor: Auth module" → it is waiting for approval → approve the edit.
# Fire off a new task via Dispatch: "Deploy the staging branch"
```

### Afternoon: Back at Your Desk

```
# Open Agent View → see all sessions including the Dispatch one.
# The Dispatch task finished → review the result.
# Start new background sessions for afternoon work.
# Cycle continues.
```

Your MacBook is the brain (local files, tools, git). Your phone is the remote control. Agent View is the command centre. Sessions survive sleep, network drops, and app switches.

---

## Common Gotchas

**"My session shows as offline on mobile."**
Your laptop is asleep or the Claude Code process was killed. Wake it up or restart the session. Remote Control reconnects automatically.

**"Dispatch is not spawning sessions on my Desktop."**
The Desktop app must be running and paired. Re-do the QR code pairing in Cowork → Dispatch setup.

**"Agent View shows sessions I do not recognise."**
Background sessions persist until explicitly closed. Use Agent View to review and close stale ones.

**"Cloud sessions cannot access my local files."**
Correct: cloud/cold sessions run on Anthropic's servers. Use `/teleport` to pull a cloud session onto your local machine, or start locally and use Remote Control.

**"I hit rate limits faster with multiple sessions."**
Each session consumes tokens from the same plan pool. Running 5 parallel agents uses 5× the tokens of 1 sequential session. Monitor usage in Settings → Usage.

---

## Frequently Asked Questions

### Do I need the Desktop app for Remote Control?

No. Remote Control works with the CLI alone. The Desktop app adds a graphical sidebar and Dispatch, but the CLI + mobile Code tab is sufficient for Remote Control.

### Can I use Remote Control with VS Code?

Yes. The Claude Code VS Code extension supports Remote Control. Sessions started in VS Code appear in the mobile Code tab the same way CLI sessions do.

### Is my code sent to Anthropic's servers with Remote Control?

Your code stays local. Remote Control routes your messages through Anthropic's relay (encrypted), but the actual file access, git operations, and tool execution happen on your machine. The relay handles the chat messages, not your codebase.

### How many parallel sessions can I run?

There is no hard limit on the number of sessions, but each session consumes tokens from your plan's usage pool. Practically, 3-5 parallel sessions is sustainable on the Max plan. More than that and you hit rate limits frequently.

### What is the difference between Agent Teams and Agent View?

Agent Teams (experimental) creates multiple agents that collaborate on a single task with peer-to-peer communication. Agent View is a dashboard that shows all your independent sessions in one place. Agent Teams is for coordinated work; Agent View is for monitoring parallel independent work.

---

## Further Reading

- [Every AI Coding Agent CLI in April 2026 Compared](https://radar.firstaimovers.com/ai-coding-agent-cli-comparison-april-2026)
- [We Built the Engine But Not the Chassis: AI Team Velocity](https://radar.firstaimovers.com/ai-accelerated-teams-velocity-stabilization-2026)
- [OpenCode + MiniMax M2.5: The Claude Code Alternative at 1/15th Cost](https://radar.firstaimovers.com/opencode-minimax-m25-claude-code-alternative-2026)

---

## Start Using Multi-Device Today

The multi-device workflow is not a nice-to-have. If you are running 3+ parallel agents (and most power users are), the combination of Agent View + Remote Control + Dispatch is the difference between manageable and chaotic.

Set up Remote Control by default (`/config`), open Agent View as your home screen (`claude agents`), and use Dispatch for tasks you think of away from your desk. Your laptop becomes the always-on brain; your phone becomes the always-available command centre.

If your team needs help structuring agent workflows, building CLAUDE.md governance files, or designing a sustainable multi-agent operating model, start with an [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) or explore [AI Consulting](https://radar.firstaimovers.com/page/ai-consulting).

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Claude Code Across Every Device: Remote Control, Dispatch, and Agent View Explained",
  "description": "How to run Claude Code sessions across mobile, desktop, and CLI. Remote Control, Dispatch, and Agent View explained with practical setup steps.",
  "datePublished": "2026-05-24T17:14:27.965853+00:00",
  "dateModified": "2026-05-24T17:14:27.965853+00:00",
  "author": {
    "@type": "Person",
    "@id": "https://radar.firstaimovers.com/page/dr-hernani-costa#dr-hernani-costa",
    "name": "Dr. Hernani Costa",
    "url": "https://radar.firstaimovers.com/page/dr-hernani-costa"
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
    "@id": "https://radar.firstaimovers.com/claude-code-remote-control-dispatch-multi-device-guide-2026-v2"
  },
  "image": "https://images.unsplash.com/photo-1591453089816-0fbb971b454c?w=1200&h=630&fit=crop&q=80",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [
      ".article-body > p:first-of-type",
      ".article-body > p:nth-of-type(2)"
    ],
    "xpath": [
      "/html/body//article//p[1]",
      "/html/body//article//p[2]"
    ]
  }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Do I need the Desktop app for Remote Control?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Remote Control works with the CLI alone. The Desktop app adds a graphical sidebar and Dispatch, but the CLI + mobile Code tab is sufficient for Remote Control."
      }
    },
    {
      "@type": "Question",
      "name": "Can I use Remote Control with VS Code?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The Claude Code VS Code extension supports Remote Control. Sessions started in VS Code appear in the mobile Code tab the same way CLI sessions do."
      }
    },
    {
      "@type": "Question",
      "name": "Is my code sent to Anthropic's servers with Remote Control?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Your code stays local. Remote Control routes your messages through Anthropic's relay (encrypted), but the actual file access, git operations, and tool execution happen on your machine. The relay handles the chat messages, not your codebase."
      }
    },
    {
      "@type": "Question",
      "name": "How many parallel sessions can I run?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "There is no hard limit on the number of sessions, but each session consumes tokens from your plan's usage pool. Practically, 3-5 parallel sessions is sustainable on the Max plan. More than that and you hit rate limits frequently."
      }
    },
    {
      "@type": "Question",
      "name": "What is the difference between Agent Teams and Agent View?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Agent Teams (experimental) creates multiple agents that collaborate on a single task with peer-to-peer communication. Agent View is a dashboard that shows all your independent sessions in one place. Agent Teams is for coordinated work; Agent View is for monitoring parallel independent work. ---"
      }
    }
  ]
}
</script>
-->