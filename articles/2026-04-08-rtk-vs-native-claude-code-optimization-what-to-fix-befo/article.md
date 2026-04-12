---
title: "RTK vs Native Claude Code Optimization: What to Fix Before Adding Another Hook"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/rtk-vs-native-claude-code-optimization-what-to-fix-before-adding-another-hook"
published_date: "2026-04-08"
license: "CC BY 4.0"
---
# RTK vs Native Claude Code Optimization: What to Fix Before Adding Another Hook

> **TL;DR:** Before adding RTK to Claude Code, fix context, model choice, MCP overhead, and workflow packaging first. A practical guide for technical leaders.

RTK is solving a real problem for serious Claude Code users: it can help burn fewer tokens on shell-heavy workflows. But before your team adds another hook to the stack, there is a simpler question to ask: have you already fixed the native cost and context problems Anthropic tells you to fix first?

Anthropic’s own guidance doesn't start with third-party proxies. It starts with first-party levers like context management, model choice, reduced MCP overhead, skills, and subagents. ([1](#references))

RTK’s core pitch is to reduce token consumption by rewriting common shell workflows into more compact forms, potentially cutting usage by 60% to 90% on common commands. However, it has an important limitation: Claude Code’s built-in tools like `Read`, `Grep`, and `Glob` don’t pass through the Bash hook, so they aren't automatically rewritten. ([2](#references))

The real decision isn’t “RTK or no RTK.” It is: how much efficiency can you unlock inside Claude Code itself before you introduce another hook layer with its own scope, behavior, and governance needs? For many teams, the answer is more than they think.

## Anthropic Already Gives You Native Cost Levers

Anthropic’s Claude Code cost documentation is surprisingly explicit. The company says token usage scales with context size and that Claude Code already reduces costs through prompt caching and auto-compaction. It then recommends several first-party strategies to reduce token usage, including proactive context management, choosing the right model, reducing MCP server overhead, moving instructions from `CLAUDE.md` to skills, adjusting extended thinking, and delegating verbose operations to subagents. ([1](#references))

That list matters because it changes the rollout order. Before you add RTK, you should tighten the native system you already have.

## Fix One: Get Context Under Control First

A lot of Claude Code waste is not caused by the absence of RTK. It is caused by messy sessions.

Anthropic recommends using `/cost` to inspect usage, `/clear` to start fresh when switching to unrelated work, and `/compact` instructions to control what survives summarization. Anthropic also documents that prompt caching and auto-compaction already reduce repeated prompt cost and long-session bloat. ([1](#references))

This is the first fix because RTK does not solve a sprawling session architecture. If your developers are carrying unrelated context across long conversations, a command-rewriting proxy will not rescue that operating habit.

### What to Do

-   Use `/cost` or a visible cost status line to make token usage legible. ([1](#references))
-   Clear sessions aggressively when work shifts. ([1](#references))
-   Add compact instructions so compaction preserves the right things instead of generic history. ([1](#references))

## Fix Two: Choose the Right Model Before Optimizing Shell Output

Anthropic’s guidance is clear here too. Its cost docs say Sonnet handles most coding tasks well and costs less than Opus, while Opus should be reserved for complex architectural decisions or multi-step reasoning. Anthropic also recommends using cheaper models such as Haiku for simple subagent tasks. ([1](#references))

This matters because a lot of teams jump to proxy optimization before they have basic model discipline. That is backwards. If your developers are using an expensive model for routine tasks that should be handled by Sonnet or a focused subagent, RTK is not your first optimization. Model routing is.

### What to Do

-   Default most coding work to Sonnet. ([1](#references))
-   Use Opus for architecture, ambiguity, or difficult multi-step reasoning only. ([1](#references))
-   Create lower-cost subagents for narrow tasks like code review, debugging, or data inspection. Anthropic says subagents run in their own context windows with their own prompts, permissions, and tool access, and can route work to cheaper models. ([3](#references))

## Fix Three: Reduce MCP Overhead Before You Add a Hook Proxy

This is one of the most underused native levers. Anthropic says MCP tool definitions are deferred by default so only tool names enter context until a tool is used. It also recommends disabling unused servers and, when possible, preferring CLI tools like `gh`, `aws`, `gcloud`, and `sentry-cli`, because CLI tools are more context-efficient than MCP servers and do not add per-tool listing overhead. ([1](#references))

That advice is strategically important. RTK is often discussed as if shell efficiency were the only frontier. It is not. For many teams, the bigger waste comes from an undisciplined MCP footprint.

### What to Do

-   Audit which MCP servers are actually enabled. ([1](#references))
-   Disable unused servers. ([1](#references))
-   Prefer direct CLI tools when they already do the job cleanly. Anthropic explicitly recommends this for context efficiency. ([1](#references))

## Fix Four: Move Repeatable Workflow Logic Out of `CLAUDE.md`

This is a subtle but important one. Anthropic’s cost guide explicitly recommends moving instructions from `CLAUDE.md` to skills. Anthropic’s overview and skills docs also describe `CLAUDE.md` as always-loaded project guidance, while skills and custom commands package repeatable workflows that can be shared and invoked when relevant. ([1](#references))

That distinction matters because an overloaded `CLAUDE.md` becomes a context tax on every session. If you keep stuffing every workflow, convention, and template into the startup file, you are paying for it over and over.

### What to Do

-   Keep `CLAUDE.md` for stable project guidance, not every workflow variant. Anthropic says it is read at the start of every session. ([4](#references))
-   Move reusable workflows into skills or custom commands. Anthropic explicitly supports shared custom commands like `/review-pr` or `/deploy-staging`. ([4](#references))
-   Use skills when you want repeatable behavior to load only when relevant. ([5](#references))

## Fix Five: Use Subagents Before You Optimize Everything Through the Main Thread

Anthropic’s subagent docs make the value proposition very direct. Subagents run in their own context windows with their own system prompts, tool access, and permissions. Anthropic says they help preserve context, isolate exploration from implementation, enforce constraints, and control costs by routing tasks to faster and cheaper models. ([3](#references))

This is a big deal operationally. If your main Claude Code session is bloated because it is trying to do research, debugging, validation, and implementation all in one context window, RTK is not your first fix. Better delegation is.

### What to Do

-   Create specialized subagents for high-volume repetitive work. Anthropic lists this as a common pattern. ([3](#references))
-   Keep the main thread focused on orchestration and decision-making, not every noisy task. ([3](#references))
-   Use lower-cost models for narrow delegated tasks where accuracy requirements permit. ([1](#references))

## So Where Does RTK Fit?

After those native levers are in place, RTK becomes much easier to judge.

RTK is strongest when:

-   The team is terminal-first
-   Claude Code usage is already mature
-   Raw Bash output is a major token sink
-   Developers are comfortable with hook-based workflows
-   The team understands that RTK only intercepts Bash tool calls, not built-in tools like `Read`, `Grep`, and `Glob` ([2](#references))

That last point is not a footnote. It is the operational boundary. If your developers spend most of their time inside Claude Code’s built-in tools, RTK will not produce the uniform optimization story some people expect. RTK’s own docs say so. ([2](#references))

## My Verdict

**Fix native Claude Code optimization first. Add RTK second.**

That is the practical order for most teams. Anthropic already gives you first-party levers for context, model selection, MCP overhead, workflow packaging, and delegated execution. Those are broader than RTK, easier to justify, and more aligned with the platform’s own cost model. ([1](#references))

RTK still has a place. But it should usually be treated as a second-layer optimization for teams that are already operating Claude Code with discipline, not as the first fix for chaotic agent usage.

## A Practical Decision Framework

### Optimize Claude Code natively first if:

-   Sessions are long and messy
-   Model choice is inconsistent
-   MCP usage is bloated
-   `CLAUDE.md` has become a dumping ground
-   The team is not yet using subagents or custom commands well

### Add RTK after that if:

-   The workflow is heavily shell-driven
-   Token burn from raw command output remains meaningful
-   The team is comfortable with hook governance
-   You accept that built-in tools still bypass the Bash hook path ([2](#references))

### Do not add RTK yet if:

-   Your team mainly relies on built-in Claude Code tools
-   The operating model is still immature
-   Nobody owns hooks, managed settings, or workflow standards
-   You are trying to solve workflow design problems with command rewriting

## Key Takeaways

-   Anthropic already provides multiple native ways to reduce Claude Code cost and context sprawl, including prompt caching, auto-compaction, context management, model choice, MCP reduction, skills, and subagents. ([1](#references))
-   RTK is useful, but it solves a narrower problem: shell-heavy token inefficiency.
-   RTK’s Bash hook does not intercept Claude Code built-in tools like `Read`, `Grep`, and `Glob`. ([2](#references))
-   Most teams should optimize native Claude Code behavior before introducing another hook-based layer.
-   The right rollout sequence is usually native controls first, RTK second.

## FAQ

### Does Claude Code already optimize token usage on its own?

Yes. Anthropic says Claude Code already uses prompt caching and auto-compaction, and recommends additional cost controls like proactive context management, model choice, reduced MCP overhead, skills, subagents, and preprocessing hooks. ([1](#references))

### What should I optimize first inside Claude Code?

Start with context hygiene, model selection, MCP discipline, and workflow packaging. Anthropic’s own cost guide points to those levers before anything third-party. ([1](#references))

### What is the strongest native alternative to stuffing more into `CLAUDE.md`?

Skills and custom commands. Anthropic recommends moving instructions from `CLAUDE.md` to skills and supports shared custom commands for repeatable workflows. ([1](#references))

### Why do subagents matter for optimization?

Anthropic says subagents run in their own context windows, can have their own tool access and permissions, and help control costs by routing narrow tasks to cheaper models. ([3](#references))

### When does RTK become worth it?

When your team is already disciplined with Claude Code and a meaningful share of token waste comes from shell-heavy workflows that flow through Bash. ([2](#references))

### What is the biggest RTK limitation in Claude Code?

RTK’s own documentation says its hook only runs on Bash tool calls, while Claude Code built-in tools like `Read`, `Grep`, and `Glob` are not auto-rewritten. ([2](#references))

## Further Reading

-   [Should You Standardize RTK for Claude Code Yet?](https://radar.firstaimovers.com/should-you-standardize-rtk-for-claude-code-yet)
-   [Claude Code Security in 2026: Hooks, Fake Installers, and What You Must Lock Down First](https://radar.firstaimovers.com/claude-code-security-2026-hooks-fake-installers-what-to-lock-down-first)
-   [What CTOs Should Standardize First in an AI Dev Stack](https://radar.firstaimovers.com/what-ctos-should-standardize-first-in-ai-dev-stack)
-   [Why Most AI Coding Rollouts Fail Before the Model Does](https://radar.firstaimovers.com/why-ai-coding-rollouts-fail)

---

If your team is trying to decide which Claude Code optimizations belong in the default stack, start with an [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment). If you already know the direction and need help designing the right operating model, hook boundaries, and rollout policy, explore [AI Consulting](https://radar.firstaimovers.com/page/ai-consulting).

## References

1.  [Manage costs effectively - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/costs)
2.  [GitHub - rtk-ai/rtk](https://github.com/rtk-ai/rtk)
3.  [Create custom subagents - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
4.  [Claude Code overview - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/overview)
5.  [Extend Claude with skills - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/skills)
6.  [How Claude remembers your project - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/memory)
7.  [Hooks reference - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/hooks)
8.  [Claude Code settings - Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/settings)

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/rtk-vs-native-claude-code-optimization-what-to-fix-before-adding-another-hook) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*