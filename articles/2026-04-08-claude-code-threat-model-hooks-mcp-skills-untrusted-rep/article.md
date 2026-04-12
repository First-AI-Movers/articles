---
title: "The Claude Code Threat Model: Hooks, MCP, Skills, and Untrusted Repos"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/claude-code-threat-model-hooks-mcp-skills-untrusted-repos"
published_date: "2026-04-08"
license: "CC BY 4.0"
---
# The Claude Code Threat Model: Hooks, MCP, Skills, and Untrusted Repos

> **TL;DR:** Claude Code security now needs a real threat model. Start with hooks, MCP, skills, plugins, and untrusted repositories before rollout complexity grows

## Claude Code now sits at the intersection of code execution, reusable workflow logic, external tool access, and repository-level configuration. That means teams need a threat model, not just a setup guide.

Most teams still secure Claude Code like it is a chat interface.

That is already the wrong model.

Anthropic describes Claude Code as an **agentic coding tool** that reads your codebase, edits files, runs commands, and integrates with development tools across terminal, IDE, desktop app, and browser. Once a tool can do all of that, the security question stops being “is the model accurate?” and becomes “what can influence the model, what can it reach, and what can it do if it gets steered the wrong way?” ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/overview))

A practical Claude Code threat model starts with four facts.

First, Anthropic’s secure deployment guidance says Claude Code can be influenced by the files, webpages, and user input it processes, including prompt injection from repository content such as a README. Second, Claude Code now supports multiple configuration and automation layers, including hooks, MCP servers, permissions, and managed settings. Third, Skills are available in beta for Claude Code users and extend Claude with specialized knowledge and workflows. Fourth, Anthropic now documents plugins as bundles that can include skills, hooks, subagents, and MCP servers, which means the extension surface is widening rather than shrinking. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

That is why a modern Claude Code threat model needs to cover more than code generation mistakes.

It needs to cover **how behavior is shaped**.

## Start with the real trust boundary

Anthropic’s secure deployment guide gives the clearest starting point. It says Claude Code and the Agent SDK are powerful because they can execute code, access files, and interact with external services, but that this flexibility also means their behavior can be influenced dynamically by the content they process. Anthropic recommends the same principles you would use for semi-trusted code: isolation, least privilege, and defense in depth. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

That should immediately change how you think about rollout.

The trust boundary is not just the model provider.

The trust boundary also includes:

-   the repository you opened
-   the hooks you allow to run
-   the MCP servers you connect
-   the skills and plugins you install
-   the permissions and settings sources you trust

If you do not model those inputs, you are not really securing Claude Code.

## Threat surface one: untrusted repositories

This is still the most important surface.

Check Point Research said in February 2026 that malicious project configurations in Claude Code could abuse hooks, MCP integrations, and environment variables to trigger shell execution and exfiltrate API credentials when users cloned and opened untrusted repositories. Check Point also said Anthropic remediated the disclosed issues before publication, but the strategic lesson remains: **repository configuration now sits much closer to execution than many teams assume**. ([Check Point Research](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/))

Anthropic’s own secure deployment guide supports that same lesson from the product side. It explicitly warns that repository content can influence agent behavior and gives a README example to show how prompt injection can shape actions in ways the operator did not expect. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

That means an untrusted repository should no longer be treated as “just code.”

It should be treated as:

-   code
-   instructions
-   configuration
-   possible workflow logic
-   possible policy input

That is a different class of trust problem.

## Threat surface two: hooks

Hooks are useful because they let teams customize behavior at the right moments in the workflow.

Hooks are risky for exactly the same reason.

Anthropic documents user, project, plugin, and managed hook behavior, and its settings docs include `allowManagedHooksOnly`, which blocks user, project, and plugin hooks while allowing only managed hooks and SDK hooks. Anthropic also documents `allowedHttpHookUrls`, which allowlists where HTTP hooks may send requests, and blocks non-matching targets when that list is defined. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

Those settings are not minor implementation details.

They are a sign that Anthropic now treats hooks as a policy surface.

The practical takeaway is simple:

If your team is using hooks without deciding who can define them, which scopes are allowed, and where they are allowed to send data, you are already behind.

## Threat surface three: MCP servers

MCP makes Claude Code much more useful.

It also expands the attack surface fast.

Anthropic says Claude Code can connect to hundreds of external tools and data sources through MCP, including issue trackers, GitHub, databases, Slack, Gmail, and webhook-style channels. The same docs also warn that third-party MCP servers should be used at your own risk and say teams should be especially careful with servers that can fetch untrusted content because they can expose users to prompt injection risk. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/mcp))

This is one of the clearest places where teams confuse utility with trust.

A server that provides more context is not automatically safe context.

A server that reaches more systems is not automatically a safe workflow.

Anthropic’s settings docs reflect this by including `allowedMcpServers` and `allowManagedMcpServersOnly`, which let organizations shift MCP access into managed policy instead of leaving it to ad hoc local setup. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

That is exactly how technical leaders should think about MCP: as a governed integration layer, not a convenience toggle.

## Threat surface four: skills and reusable instruction layers

Skills are not just a productivity feature anymore.

Anthropic says Skills extend Claude with specialized knowledge and workflows, and that they are available in beta for Claude Code users. That means reusable instruction layers can now affect how the agent behaves across tasks, not just inside a single conversation. ([Claude Help Center](https://support.claude.com/en/articles/12512180-use-skills-in-claude))

On their own, skills are not “dangerous.”

But from a threat-model perspective, they matter because they are a **behavior-shaping layer**.

If you combine that with Anthropic’s plugin direction, the picture gets bigger. Anthropic’s Claude Code best-practices page says plugins bundle skills, hooks, subagents, and MCP servers into a single installable unit from the community and Anthropic. The changelog also shows Anthropic has released a formal plugin system with marketplace commands and repository-level marketplace configuration. ([Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices))

That means your threat model should not treat hooks, MCP, and skills as isolated features.

In practice, they can arrive together.

## Threat surface five: permissions and policy drift

Anthropic’s permissions system is more mature than a lot of teams realize.

Anthropic says Claude Code supports allow, ask, and deny rules through `/permissions`, and its settings docs include `allowManagedPermissionRulesOnly`, which prevents user and project settings from defining their own permission rules so only managed rules apply. Anthropic also exposes marketplace restriction controls like `blockedMarketplaces`, which can block plugin sources before they touch the filesystem. ([Claude](https://code.claude.com/docs/en/permissions))

This is where many organizations will either look mature or exposed. If policy lives mostly in local preference, repo improvisation, and social convention, [rollout risk increases quickly](/why-ai-coding-rollouts-fail).

If policy lives in managed settings, allowlists, and explicit restrictions, Claude Code becomes much easier to reason about.

## A practical threat model for technical leaders

If I were building a minimum viable Claude Code threat model for a team, it would cover these five questions:

### 1. What can shape behavior?

Repository files, project settings, hooks, skills, plugins, and external content sources can all influence how the agent behaves. Anthropic’s own docs and Check Point’s research both support this framing. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

### 2. What can the agent reach?

Files, shell commands, MCP-connected tools, databases, APIs, and remote destinations are all part of the reachable surface. Anthropic’s MCP and secure deployment docs make that explicit. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/mcp))

### 3. Which layers are user-defined versus managed?

Anthropic’s settings model distinguishes managed settings from user, project, local, and plugin scopes. Your risk posture changes dramatically depending on where critical controls are actually enforced. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

### 4. What can leave the environment?

HTTP hooks, MCP servers, proxies, outbound API calls, and credential-bearing requests all matter. Anthropic’s secure deployment guide explicitly recommends network controls and proxy patterns for hardened environments. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

### 5. What is trusted by default that should not be?

This is the question teams skip. Untrusted repos, community plugins, and third-party MCP servers often get treated as if they are neutral until proven malicious. That is backwards. Anthropic’s own MCP docs say to use third-party servers at your own risk and be especially careful when they can fetch untrusted content. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/mcp))

## What to lock down first

If your organization is still early, start with the highest-leverage controls.

### Move critical policy into managed settings

Use managed controls for hooks, MCP servers, and permission rules where the environment justifies it. Anthropic documents `allowManagedHooksOnly`, `allowManagedMcpServersOnly`, and `allowManagedPermissionRulesOnly` for exactly this reason. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

### Treat plugins as supply-chain surface

Because plugins can bundle skills, hooks, subagents, and MCP servers, they should be reviewed like installable workflow infrastructure, not like harmless add-ons. Anthropic’s plugin docs and changelog make the bundle model explicit. ([Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices))

### Limit outbound destinations

Use HTTP hook allowlists and managed MCP restrictions so the agent cannot quietly expand its network footprint. Anthropic documents both control surfaces. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

### Raise the bar for repo trust

Do not let “it came from GitHub” count as a trust model. Check Point’s findings are enough to kill that habit. ([Check Point Research](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/))

### Separate experimentation from standards

This is the operational lesson behind the whole cluster. A toolchain that works for a power user is not automatically safe or governable as a team default. This is one of the key questions to address when deciding [what to standardize first in an AI dev stack](/what-ctos-should-standardize-first-in-ai-dev-stack).

## My verdict

The right Claude Code threat model is not “watch out for bad code suggestions.”

It is:

**watch how behavior is shaped, watch what the agent can reach, and watch which settings layer actually controls the system.**

That is the practical shift from assistant thinking to infrastructure thinking.

Claude Code is already powerful enough that technical leaders should treat hooks, MCP, skills, plugins, and repository trust as one connected operating surface, not five unrelated features. Anthropic’s own documentation now supports that view, and the 2026 security research makes ignoring it much harder. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

## FAQ

### What is the biggest Claude Code security mistake teams make?

Treating Claude Code like a chat interface instead of an agentic tool that can execute code, access files, and interact with external services. Anthropic’s own secure deployment guide explicitly frames it as a system that needs isolation, least privilege, and defense in depth. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

### Why do untrusted repositories matter so much?

Because repository content and configuration can shape agent behavior. Anthropic warns about prompt injection from repository files, and Check Point showed how malicious project configuration could abuse hooks, MCP, and environment variables. ([Claude](https://platform.claude.com/docs/en/agent-sdk/secure-deployment))

### Are hooks the main risk?

Hooks are a major risk surface because they can change behavior and trigger actions, but they are part of a larger picture that also includes MCP, skills, plugins, permissions, and repository trust. Anthropic’s settings model reflects that. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/settings))

### Are third-party MCP servers safe?

Not by default. Anthropic explicitly says third-party MCP servers are used at your own risk and warns that servers fetching untrusted content can expose you to prompt injection. ([Claude API Docs](https://docs.anthropic.com/en/docs/claude-code/mcp))

### Do skills belong in the threat model too?

Yes. Skills shape behavior through reusable workflows, and Anthropic says they extend Claude with specialized knowledge and workflows. In beta for Claude Code, they are part of the behavior layer even if they are not the same thing as hooks or MCP. ([Claude Help Center](https://support.claude.com/en/articles/12512180-use-skills-in-claude))

### Why mention plugins here?

Because Anthropic says plugins can bundle skills, hooks, subagents, and MCP servers into one installable unit. That makes plugins a supply-chain and governance surface, not just a convenience layer. ([Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices))

## From Threat Model to Operating Model

Understanding the Claude Code threat surface is the first step. The next is building an operating model that gives your team guardrails without killing momentum. If you need to move from scattered experimentation to a governed, scalable AI development practice, we can help.

Our **[AI Readiness Assessment](/page/ai-readiness-assessment)** is the fastest way to get a clear, actionable picture of your current state, risks, and opportunities. For deeper implementation and architecture design, explore our **[AI Consulting](/page/ai-consulting)** services.

## Further Reading

-   [Claude Code Security in 2026: Hooks, Fake Installers, and What You Must Lock Down First](/claude-code-security-2026-hooks-fake-installers-what-to-lock-down-first)
-   [What CTOs Should Standardize First in an AI Dev Stack](/what-ctos-should-standardize-first-in-ai-dev-stack)
-   [AI Readiness for Engineering Teams: 15 Questions to Ask](/ai-readiness-engineering-teams-15-questions)
-   [Why Most AI Coding Rollouts Fail Before the Model Does](/why-ai-coding-rollouts-fail)


---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/claude-code-threat-model-hooks-mcp-skills-untrusted-repos) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*