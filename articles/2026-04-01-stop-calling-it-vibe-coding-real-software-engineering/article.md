---
title: "Stop Calling It Vibe Coding"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/stop-calling-it-vibe-coding-real-software-engineering"
published_date: "2026-04-01"
license: "CC BY 4.0"
---
# Stop Calling It Vibe Coding

## Real software engineering starts when the model stops typing and your system starts proving

Large language models can generate code faster than most teams can responsibly review it. This shift is the foundation of modern **AI software engineering**. The real job is no longer typing more lines; it's building the system that decides what gets accepted, what gets tested, what gets rejected, and what gets promoted to production.

## The problem is not AI-generated code. The problem is lazy process.

The phrase “vibe coding” took off after Andrej Karpathy used it to describe a style of building where you mostly prompt, accept changes, and stop caring much about the code itself. Simon Willison later made the distinction sharper: if you review, test, and understand what the model produced, that is not vibe coding. That is just using a better tool. [read](https://x.com/karpathy/status/1886192184808149383)

That distinction matters.

Because a lot of people now use “vibe coding” as a lazy insult for any team using AI to write software faster.

That is wrong.

The issue is not whether AI wrote the code.

The issue is whether your organization has a repeatable process for turning machine-generated output into reliable software.

If the answer is no, then yes, you are gambling.

If the answer is yes, then you are engineering.

## Writing code is no longer the scarce skill

Here is the uncomfortable truth most teams have not fully absorbed yet:

Code generation is becoming abundant.

Judgment is not.

A junior engineer with a strong model can now produce more raw code in a day than multiple senior engineers could carefully review line by line. That changes the economics of the job immediately. The old mental model assumed that writing was expensive and review was manageable. The new reality is the opposite. Generation is cheap. Verification is expensive.

So the winning teams do not respond by demanding more manual review.

They respond by redesigning the system.

They ask better questions:

- What should be checked by AI before a human ever sees it?
- What should be tested automatically at unit, integration, and end-to-end level?
- What should be deployed into a preview environment before it is considered real?
- What should require approval gates before it touches production?

That is where the leverage is now.

## Real AI software engineering is not “read every line”

A lot of teams still act as if professionalism means every meaningful change must be personally read, line by line, by increasingly overloaded humans.

That is not a scalable philosophy anymore.

It is nostalgia disguised as rigor.

GitHub’s own documentation now makes clear that AI can review pull requests and provide suggested changes, but those reviews do not count as required approvals for merging. That is a useful design choice. It tells you exactly where AI review belongs: inside the process, not above it. AI review is one layer. Not the whole system. [read](https://docs.github.com/copilot/using-github-copilot/code-review/using-copilot-code-review)

So no, I do not think the answer is “let the model write code and hope for the best.”

I also do not think the answer is “humans must read everything forever.”

The answer is to build a review and release architecture—a core component of modern **AI Architecture**—where trust comes from the system, not from heroic attention.

## What the New Discipline of AI Software Engineering Looks Like

If you want to know whether a team is doing software engineering or just playing with AI, stop looking at how the code was written.

Look at the pipeline.

Professional teams build constellations of checks around change:

- multiple AI reviews
- repository-specific instructions
- unit tests
- integration tests
- end-to-end tests
- UI validation
- preview environments
- deployment protections
- staged promotion to production

That is not theory anymore.

GitHub supports repository-level instructions and path-specific instructions for AI review. Playwright is built specifically for end-to-end testing with assertions, isolation, parallelization, and CI support. GitHub environments support approval requirements and deployment protection rules. Vercel preview environments let teams test changes live without affecting production and create a preview deployment automatically for pull requests and non-production branches. [read](https://docs.github.com/copilot/using-github-copilot/code-review/using-copilot-code-review)

That stack is the point.

The software engineer of the next phase is not mainly a typist.

The software engineer is a designer of guardrails, evaluations, feedback loops, and release systems.

## The job is shifting from authorship to assurance

This is the part many people still resist emotionally.

They built their identity around writing code.

I get it.

For years, the visible output of engineering talent was the code itself. That is changing. The more capable the models get, the less valuable raw authorship becomes and the more valuable assurance becomes.

That means the best engineers will increasingly be the ones who can:

- define the architecture clearly
- express the constraints precisely
- create strong tests
- specify quality bars
- design the review pipeline
- create safe rollout paths
- and know when the system is lying

That is a higher bar, not a lower one.

It is also why a lot of the “AI will replace engineers” conversation misses the point. AI is not removing the need for engineering discipline. It is making weak engineering discipline impossible to hide.

## DORA had the right instinct before this wave even arrived

This shift also lines up with how strong engineering organizations have measured performance for years.

DORA’s software delivery metrics focus on whether teams can deliver software safely, quickly, and efficiently. The framework splits performance into throughput and instability, looking at factors like lead time, deployment frequency, failed deployment recovery time, failure rate, and reliability. That is a useful lens here because none of those outcomes care whether a human or a model typed the code. They care whether the system ships dependable software. [read](https://dora.dev/guides/dora-metrics/)

That is the right frame for leaders.

Not “How much code did we write?”

Not “Did a human type this function?”

But “Can we repeatedly move good changes into production with speed and control?”

That is the scoreboard.

## My take

Vibe coding has no place in production software engineering.

But that does not mean humans need to go back to manually writing everything.

It means professionals need to stop confusing authorship with accountability.

You can let the models generate enormous amounts of code.

You can let them propose fixes.

You can let them review PRs.

You can let them test interfaces.

You can let them accelerate everything.

What you cannot do is confuse speed with discipline.

The teams that win from here will not be the ones bragging that AI wrote the whole app.

They will be the ones who built the best machine for deciding what deserves to ship.

That is software engineering.

And yes, I believe those teams are going to produce better software than a shocking number of organizations still arguing about whether using AI is somehow less “real.”

## What leaders should do next

If you lead an engineering organization, this is the moment to redesign your workflow around one new reality:

**code generation is no longer the constraint. verification is.**

Start there.

Audit your current path from prompt to production. An **AI Readiness Assessment** can provide a structured approach to identifying these bottlenecks.

Look at where your process still assumes humans can manually absorb every meaningful change. Then replace that assumption with a layered quality system:

1. **AI review before human review**
   Use AI to catch obvious problems early, but do not pretend that AI review alone is approval. GitHub’s own system treats it as advisory, not decisive. [read](https://docs.github.com/copilot/using-github-copilot/code-review/using-copilot-code-review)

1. **More than unit tests**
   Unit coverage is not enough when AI-generated code can create UI drift, workflow regressions, and cross-system breakage. Playwright exists for exactly this kind of browser-level validation. [read](https://playwright.dev/)

1. **Preview every meaningful change**
   If a change matters, stand it up somewhere real before it touches production. Preview deployments and protected environments make this operational, not aspirational. [read](https://vercel.com/docs/deployments/environments)

1. **Promote, do not pray**
   Treat production as a promotion target, not a leap of faith. The highest-confidence change should be the one that gets promoted after surviving the system.

That is how you turn AI speed into engineering advantage.

## Further Reading

- [Why AI Coding Rollouts Fail](https://radar.firstaimovers.com/why-ai-coding-rollouts-fail)
- [Claude Code for Teams: An AI Delivery System](https://radar.firstaimovers.com/claude-code-teams-ai-delivery-system)
- [AI-Native Engineering Playbook for European SMEs](https://radar.firstaimovers.com/ai-native-engineering-playbook-european-smes)
- [GitHub Coding Agent for Product Teams](https://radar.firstaimovers.com/github-coding-agent-product-teams)

---

_Written by [Dr Hernani Costa](https://drhernanicosta.com), Founder and CEO of [First AI Movers](https://www.firstaimovers.com). Providing AI Strategy & Execution for Tech Leaders since 2016._

Subscribe to [First AI Movers](https://firstaimovers.com) for practical and measurable business strategies for Business Leaders. [First AI Movers](https://www.linkedin.com/company/first-ai-movers/) is part of [Core Ventures](https://coreventures.xyz).

**Ready to increase your business revenue?**
Book a [call](https://calendar.app.google/RJnKGg3b8ZRfhect5) today!

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/stop-calling-it-vibe-coding-real-software-engineering) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*