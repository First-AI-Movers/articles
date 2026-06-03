# Summary Review — How I Evaluate a 12‑Month AI Roadmap Answer

Article folder: 2026-03-09-evaluate-ai-roadmap-framework-2026
Canonical URL: https://radar.firstaimovers.com/evaluate-ai-roadmap-framework-2026
Generated at: 2026-06-03
Model: minimax (MiniMax-M2)

## 50-word summary

The article presents a framework for evaluating senior technical candidates on their 12-month AI roadmap. It scores them across three dimensions: phased outcomes (25 points), fit-for-context architecture with build-vs-buy decisions (35 points), and data governance with PII handling (40 points). The highest weight is on governance, emphasizing real-world constraints.

## 200-word summary

The article outlines a framework for assessing senior technical candidates (engineers, architects, or CTOs) on their ability to articulate a realistic 12-month AI roadmap. The evaluation is set in the context of a mid-size B2B SaaS company with a monolith, messy data, a small team, and a CEO demanding "AI copilots" within a year. Candidates are scored on three dimensions totaling 100 points. The first dimension (25 points) assesses a phased, outcome-driven roadmap progressing from de-risking data and shipping a prototype to delivering a copilot with measurable business impact, then formalizing governance. The second (35 points) evaluates fit-for-context architecture and build-vs-buy decisions, favoring candidates who respect the current stack, use managed LLMs early, and make explicit trade-offs. The third and highest-weighted dimension (40 points) covers data foundations, PII handling, and governance. Candidates must identify where PII resides, centralize and classify it, enforce data residency, involve legal early, and be opinionated about which AI use cases are off-limits due to governance risk. The framework rewards candidates who move comfortably across these axes while acknowledging resourcing limits and trade-offs, indicating readiness to lead a real AI roadmap.

## 500-word summary

The article, written by Dr. Hernani Costa of First AI Movers, presents a framework for evaluating senior technical candidates—such as senior engineers, architects, or CTOs—on their ability to articulate a realistic 12-month AI roadmap. The evaluation context is a mid-size B2B SaaS company with an existing monolith, messy data, a small team, and a CEO who wants "AI copilots" delivered within a year. The author emphasizes that grading is not based on fantasy architectures but on how candidates think under real-world constraints, including limited resources and legacy systems. The framework scores candidates across three weighted dimensions: a phased, outcome-driven AI roadmap (25 points), fit-for-context architecture and build-vs-buy decisions (35 points), and data foundations, PII handling, and governance (40 points). Governance receives the highest weight, reflecting the author's view that it is non-negotiable and a core component of professional AI governance and risk advisory.

For the roadmap dimension, the author looks for a clear sequence of phases over twelve months, with each phase tied to measurable business outcomes rather than mere activity. Strong answers describe phase one as de-risking data and shipping a prototype to "earn the right to build," phase two as delivering the first copilot with demonstrable business impact, and phase three as doubling down on effective strategies and formalizing governance processes. The architecture dimension tests whether candidates respect the current stack and team size by keeping the core on the existing cloud and introducing AI through sidecar services. Top candidates lean on managed LLMs and platforms early, only considering custom hosting or sovereign options when scale or regulation justifies it. They make explicit trade-offs—for example, choosing a managed service over building in-house because of specific factors like cost, speed, or expertise. The governance dimension requires candidates to demonstrate knowledge of where PII resides within the organization, propose steps to centralize and classify that data, enforce data residency requirements, and involve legal teams early in the process. The author awards bonus points for candidates who are opinionated about which AI use cases are off-limits in year one due to governance risk, and who explain how they will monitor and audit AI behavior in production.

The author concludes that a candidate who moves comfortably across these three axes—phasing, architecture, and governance—while acknowledging resourcing limits and trade-offs, is ready to lead a real AI roadmap, not just talk about one. The framework is offered as a tool that can be directly lifted into hiring processes. The article also includes links to further reading on topics such as AI architect vetting, strategic imperatives for AI roadmaps, build-vs-buy decision frameworks, and AI copilots playbooks. Dr. Hernani Costa is the Founder and CEO of First AI Movers, an organization providing AI strategy and execution for tech leaders since 2016. He holds a PhD in Computational Linguistics and has over 25 years of experience in technology. The article is published under CC BY 4.0 and originally appeared on First AI Movers.

## Review status

Status: approved
Reviewer:
Reviewed at:

## Notes

- Gate status: PASS
- Retries used: 2
- Corrective JSON retries used: 0
- Fallback attempts used: 1
- Fallback provider: deepseek/deepseek-v4-flash
- Termination: PASS_via_fallback
- Estimated cost (USD): 0.013923
- Word counts: short=49, medium=185, long=486

## Verification

Verification status: AUTO_APPROVE
Deterministic gate: PASS
Primary verifier: openai/gpt-5.4-mini — AUTO_APPROVE
Secondary verifier: anthropic/claude-haiku-4-5-20251001 — AUTO_APPROVE
Fallback verifier: not-used
Single verifier: false
Estimated verifier cost (USD): 0.003988
Verified at: 2026-06-03

### Verification notes

- Merge rationale: both verifiers AUTO_APPROVE
- openai/gpt-5.4-mini: Captures the three scoring dimensions accurately.
- openai/gpt-5.4-mini: Preserves the context and emphasis on real-world constraints.
- openai/gpt-5.4-mini: No invented sections or unsupported claims.
- anthropic/claude-haiku-4-5-20251001: All three summaries accurately reflect the source's three-dimension scoring framework (25/35/40 points) and core concepts.
- anthropic/claude-haiku-4-5-20251001: No volatile facts embedded; framework is structural and timeless, not dependent on market conditions or rankings.
- anthropic/claude-haiku-4-5-20251001: Author credentials and organizational context preserved accurately across all lengths.
