---
title: "The Agent Is Not the Broken Part: Why Environment Readiness Now Decides AI Delivery"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/the-agent-is-not-the-broken-part-ai-delivery"
published_date: "2026-04-06"
license: "CC BY 4.0"
---
# The Agent Is Not the Broken Part: Why Environment Readiness Now Decides AI Delivery

> **TL;DR:** Why environment readiness now decides AI delivery. A practical guide for CTOs on engineering hygiene, review, docs, and governance before scaling agen

In 2026, the difference between an impressive demo and a working AI delivery system is rarely the agent. It is the environment the agent has to operate in.

A lot of teams are still diagnosing the wrong problem. The agent misses a step, writes weak code, fails a task, or gets stuck in a loop, and the immediate reaction is predictable: maybe the model is not strong enough, maybe the tool is overhyped, maybe we picked the wrong vendor.

Sometimes that is true. More often, it is not.

Factory’s Agent Readiness framing is blunt about this: teams often blame the model, switch agents, and get the same weak results because “the agent is not broken. The environment is.” Their framework measures repositories across technical pillars like style and validation, build systems, testing, documentation, dev environment, code quality, observability, and security and governance. That is a much more useful way to think about AI delivery in 2026. ([Factory.ai](https://factory.ai/news/agent-readiness))

## The market is quietly admitting that environment quality now decides outcomes

One of the clearest signals in 2026 is that vendors are shipping more controls around behavior, not just more intelligence.

OpenAI is not just selling “smarter code.” Codex is positioned as a command center for agents, with shared skills and parallel work. GitHub is not just selling generation. Copilot coding agent is built around reviewable pull requests and outcome measurement. Anthropic is not just selling a terminal agent. Claude Code now exposes a settings hierarchy with enterprise-managed policy, team-shared settings, user settings, and explicit allow, ask, and deny rules for tool use. That product direction tells you where the real battle is: not only model quality, but whether teams can create repeatable, governable environments for AI work. ([OpenAI](https://openai.com/index/introducing-the-codex-app/))

## Why great agents still fail in bad environments

A strong agent still performs poorly when the surrounding system is weak.

If build steps depend on tribal knowledge, the agent wastes cycles guessing. If tests are slow or missing, the feedback loop collapses. If docs are stale, the agent pulls the wrong assumptions into the task. If permissions are loose, the agent can do too much in the wrong place. If review is informal, weak output slips through or good output becomes expensive to validate.

Factory’s readiness model is useful precisely because it treats these as environment failures, not agent failures. It organizes readiness around practical pillars that determine whether autonomous or semi-autonomous work is even feasible. The point is not that agents are useless. The point is that environments can make useful agents look broken. ([Factory.ai](https://factory.ai/news/agent-readiness))

## Old engineering truths still decide agent performance

This is where the industry keeps overcomplicating the message.

AI delivery in 2026 still depends on old engineering fundamentals:

-   Measure before optimizing
-   Keep structures simple
-   Standardize what good looks like
-   Make the build reproducible
-   Keep review explicit
-   Make the runtime observable
-   Treat data and context structure as first-class

That is exactly why readiness frameworks feel so grounded. Factory’s maturity model moves from functional to documented to standardized to optimized to autonomous. In other words, autonomy does not arrive because you bought an agent. It arrives because the environment became legible enough to support it. ([Factory.ai](https://factory.ai/news/agent-readiness))

## What environment readiness actually means

For most teams, environment readiness has six concrete parts.

### 1. Fast feedback loops

Agents need tight feedback. Linters, type checkers, test suites, and pre-commit checks reduce wasted cycles and help the agent converge faster. Factory explicitly treats style and validation, build systems, and testing as foundational pillars because without them, agents keep failing on issues that should be caught in seconds. ([Factory.ai](https://factory.ai/news/agent-readiness))

### 2. Written instructions instead of hidden tribal knowledge

A readable environment beats a “smart” agent every time.

GitHub now supports repository-wide Copilot instructions and `AGENTS.md` for agent workflows. Claude Code uses `CLAUDE.md` and shared project settings. Factory also treats documentation as one of the core readiness pillars and publishes guidance for `AGENTS.md` structure. These are all variations of the same lesson: the environment gets stronger when expectations are encoded, not remembered. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

### 3. Explicit review design

A team is not environment-ready if AI review is still vague.

GitHub says Copilot-created pull requests should be reviewed thoroughly before merge. Copilot code review itself is configurable and can automatically review pull requests. OpenAI’s Codex app is built around reviewing diffs and supervising long-running work. Strong environments design the review path in advance. Weak environments hope someone catches issues later. ([GitHub Docs](https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent/reviewing-a-pull-request-created-by-copilot))

### 4. Permissions and boundaries

Claude Code’s settings make this especially clear. Teams can define allow, ask, and deny rules, block access to secrets and environment files, and enforce enterprise-managed policy that users cannot override. That is environment readiness in practice: the agent is powerful, but the environment sets the boundaries. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

### 5. Observability and measurement

This is where most teams still underinvest.

Factory treats observability as a core readiness pillar, and GitHub now includes guidance on measuring pull-request outcomes for coding-agent use. That matters because teams that do not measure rework, review burden, and exception rates often mistake output volume for progress. ([Factory Documentation](https://docs.factory.ai/web/autonomy-maturity/overview))

### 6. Security and governance

Readiness is not complete until the environment can prevent the wrong work from becoming normal work.

Factory includes security and governance as a core pillar. GitHub exposes org and enterprise controls for Copilot. Claude Code supports managed policy. The pattern is clear: agent performance is now inseparable from governance quality. ([Factory.ai](https://factory.ai/news/agent-readiness))

## The easiest mistake to make

The easiest mistake is to keep treating agent performance like an isolated tooling problem.

That produces the wrong behavior:

-   Switch the tool
-   Try another model
-   Buy another seat
-   Add another lane
-   Keep the environment the same

Then the team is surprised when the same class of problems returns.

That is one reason “tool sprawl” has become so expensive. If the environment remains weak, every new tool just introduces another surface for the same underlying failure. This is why your stack decision and your readiness decision are now tightly connected. A weak environment turns optionality into noise. A strong environment turns even modest agent capability into leverage. ([Factory.ai](https://factory.ai/news/agent-readiness))

## What CTOs should fix first

If I were advising a technical leader right now, I would focus on this order:

1.  **Build and test clarity:** Make sure the agent can actually build, validate, and check its own work.
2.  **Instruction quality:** Write down how the repo works, what standards matter, and what should never happen.
3.  **Review model:** Define what gets reviewed, by whom, and where the approval checkpoint lives.
4.  **Permission boundaries:** Constrain what the agent can read, run, and change.
5.  **Observability:** Measure whether the workflow is getting better or just getting busier.

That sequence is more valuable than chasing one more model upgrade because it improves the environment every future agent will inherit. Factory’s maturity framing supports this directly: most teams should aim at a “standardized” environment before dreaming about full autonomy. ([Factory.ai](https://factory.ai/news/agent-readiness))

## My take

The agent is not the broken part often enough that technical leaders should assume environment failure first.

That does not mean the model never matters. It means the faster commercial win usually comes from strengthening the environment: better validation, better docs, better review, better permissions, better observability, better shared instructions.

That is also why the consulting opportunity is changing. Teams do not just need recommendations on which tool to buy. They need help making their environments agent-ready. The teams that understand this early will get more value from the same generation of tools than teams that keep buying more capability into weak systems. ([Factory.ai](https://factory.ai/news/agent-readiness))

## Key takeaways

The most important shift in AI delivery is not just stronger agents. It is that environment quality now decides whether those agents can produce repeatable business value. Factory’s readiness model makes that explicit, and the current product direction across OpenAI, GitHub, and Anthropic supports it through shared skills, repository instructions, review workflows, managed settings, and permission boundaries. ([Factory.ai](https://factory.ai/news/agent-readiness))

That means the next question for technical leaders is not only “Which agent should we use?” It is “What kind of environment are we giving that agent to work in?” Teams that answer that well will outperform teams still trapped in vendor-switching mode. ([Factory.ai](https://factory.ai/news/agent-readiness))

## Further Reading

-   [AI Readiness for Engineering Teams: 15 Questions Before You Scale](https://radar.firstaimovers.com/ai-readiness-engineering-teams-15-questions)
-   [Why Most AI Coding Rollouts Fail Before the Model Does](https://radar.firstaimovers.com/why-ai-coding-rollouts-fail-1)
-   [Why the Best AI Dev Stack Starts With Review Design, Not Model Choice](https://radar.firstaimovers.com/best-ai-dev-stack-starts-with-review-design)
-   [What CTOs Should Standardize First in an AI Dev Stack](https://radar.firstaimovers.com/what-ctos-should-standardize-first-in-ai-dev-stack)

## From Readiness to Rollout

If your team needs a structured way to assess whether the environment is ready before you scale more agentic work, start with the [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment).

If the issue is already broader and you need help redesigning the operating model behind engineering workflows, review, permissions, and rollout, see our [AI Consulting](https://radar.firstaimovers.com/page/ai-consulting) services.

And if you want the broader framing behind why this is now an AI development operations problem rather than just a tooling question, start with [AI Development Operations](https://radar.firstaimovers.com/page/ai-development-operations).


---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/the-agent-is-not-the-broken-part-ai-delivery) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*