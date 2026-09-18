---
title: "A Two-Person Team Out-Built 300 Rivals in 12 Hours, Because They Mapped First"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/map-before-you-build-ai-project-planning-sme-2026"
published_date: "2026-07-17"
license: "CC BY 4.0"
---

> **TL;DR:** Most failed AI pilots die from no plan, not bad tech. Learn the map-first AI project planning method that lets small European teams ship working AI.

The single biggest predictor of whether your AI pilot works is not the model you choose, the vendor you hire, or the budget you approve. It is whether someone wrote down, before any tool was opened, exactly which workflow the AI must fix, what _fixed_ looks like, and when to kill the project. The teams that plan win. The teams that start typing into an AI tool and _see where it goes_ burn cash and quietly abandon the pilot a quarter later.

That pattern showed up vividly at a recent Anthropic event, and it maps almost perfectly onto why most small-company AI projects stall.

## The hackathon that proved planning beats horsepower

On 13 June 2026, Anthropic ran a [Claude Opus 4.8 Build Day hackathon](https://claude.com/blog/meet-the-winners-of-our-claude-opus-4-8-build-day-hackathon) in San Francisco (S1). The numbers were stark: 310 builders selected from roughly 1,500 applicants, 12 hours on the clock, and $500 in model credits each (S1). Everyone had the same frontier model. Everyone had the same time. The constraint was identical for all 310 people in the room.

The winner, a project called **Tekton**, was built by just two people, designer Holly Tang and Austin Burgess, who had met a month earlier in line for coffee at a Code with Claude event (S1). Their project digitally reconstructed historic buildings, including Tang Dynasty architecture and the spire of Notre-Dame, across **339 incremental construction states**, with every single component traceable back to source evidence (S1). It was rigorous, deep, and finished. A two-person team beat a room of more than 300 competitors.

### What they did differently

They did not start building. They started by mapping.

Before writing code, the pair wrote a complete PRD, a product requirements document. As Austin Burgess put it, "We built an entire PRD and a Notion board with around 50 tickets, one for each specific task" (S1). Only then did they execute, running separate workflows in parallel because the spec told them exactly which pieces were independent and could move at the same time. Their lesson, distilled: _map the whole project before you build any of it._

The lesson is not that AI is powerful. Everyone in that room had the same powerful AI. The lesson is that the planning discipline, the spec written before the build, is what converts raw capability into a finished, defensible result under a hard deadline. The team with the clearest map shipped the most complete project.

## Why this matters more for a small company than a large enterprise

A large enterprise can afford a failed AI pilot. It has slack, budget lines, a spare quarter, a team that can absorb a write-off. A European SME with 10 to 50 employees has no such cushion. When a small company spends three months and a real budget on an AI tool that ends up doing _a bit of everything, badly_, that is not a learning experience. It is a hole in the year.

So the planning discipline that won a hackathon is not a nice-to-have for you. It is the difference between a working deployment and an expensive toy you stop opening.

### The real reason most AI pilots fail

It is rarely the technology. The models available in 2026 are more than capable for the operational workflows most SMEs need. The failure pattern is almost always upstream of the tool:

- **No spec.** Someone opened the AI tool and started prompting, with no written definition of what it had to accomplish.
- **No defined outcome.** _Improve our customer support_ is a wish, not a target. Nobody could say afterwards whether it worked.
- **No scope boundary.** The pilot drifted, first it answered emails, then it drafted quotes, then it tried to update the CRM, and did all of it half-well.
- **No kill criterion.** With no agreed line for _this isn't working, stop_, the pilot limped on, consuming time and goodwill until it was quietly dropped.

The build-first instinct feels productive. It is the most common way to waste an AI budget.

## The two paths: build-first and map-first

| Dimension | Build-first (no plan) | Map-first (spec-driven) |
|---|---|---|
| Starting move | Open the tool and prompt | Write the spec, then build |
| Scope | Expands as ideas appear | Fixed to one workflow up front |
| Outcome definition | Vague (_make support better_) | One measurable target |
| Parallel work | Accidental and conflicting | Deliberate, because the map shows what's independent |
| Failure mode | _Does a bit of everything badly_ | Fails fast on a clear criterion, or ships |
| Budget exposure | Open-ended; drifts until abandoned | Bounded by the spec and kill line |
| Typical end state | Quietly abandoned pilot | Working deployment or a clean, cheap no |

The Tekton team did not have more time or a better model than anyone else. They had a map. That is the entire edge, and it is fully available to a small operations team that has never run an AI project before.

## The minimum viable AI spec: a checklist a non-technical leader can run

You do not need a technical PRD with 50 tickets. You need five answers, written down and agreed before any tool is bought or any prompt is typed. If you cannot answer all five, you are not ready to build yet, and that is useful to know before you spend. This is the minimum viable AI spec, and it is the shortest honest answer to how to plan an AI project.

| Spec element | The question to answer |
|---|---|
| The one workflow | Which single, painful, repetitive task will this AI handle? Name it precisely. |
| The measurable outcome | What number proves it worked? (e.g. hours saved per week, turnaround time, error rate) |
| The data needed | What information must the AI see to do this, and do we already have it in a usable place? |
| The guardrails | What must it never do, and where does a human stay in the loop? |
| Success / kill criteria | At what result do we scale it, and at what result do we stop, by an agreed date? |

### How to use the checklist in practice

**Pick one painful workflow, not a category.** Not _automate operations_. Instead: _draft first-response replies to inbound support emails in our top three languages_. One workflow, clearly bounded. The boundary is the point, it is what stops the AI pilot scope creep that kills pilots.

**Attach a number before you start.** If today a task takes your team eight hours a week, the outcome is _cut this to under two hours a week within six weeks_. Now success is observable by anyone, not a matter of opinion. A pilot with no number cannot be judged, so it never ends cleanly.

**Check the data honestly.** Most SME AI pilots stall not on the model but on the inputs, the information is scattered across inboxes, spreadsheets, and someone's head. If the data is not reachable, that is your first project, and the spec just saved you from discovering it three weeks in.

**Write the guardrails as plainly as the goal.** Under the EU AI Act, whose prohibitions and general-purpose AI obligations are already in force, with high-risk obligations phasing in (S2), knowing exactly what your system does, what data it touches, and where a human reviews its output is not just good practice; it is part of staying on the right side of obligations that increasingly carry real weight. A spec that names the human-in-the-loop point is a compliance asset, not bureaucracy.

**Agree the kill line out loud.** The hardest discipline is deciding, in advance, the result that means stop. A pilot you are allowed to stop is cheap. A pilot nobody can stop is the one that drains the year.

## Plan first, then let the work run in parallel

Here is the part that the Tekton story makes concrete and that small teams routinely miss: planning first is what _enables_ speed, not what slows it down. Because the team had a complete map, they could see which pieces were independent and run separate workflows in parallel without tripping over each other. The spec is what made the parallelism safe.

For an SME, the equivalent is this: once the one workflow is specified, you often find it splits into a handful of independent steps, data preparation, the AI drafting step, the human review step, the hand-off to your existing system. With a map, two people can work those steps at once. Without a map, the same two people block each other, redo work, and produce something nobody can quite explain. The plan is not overhead. It is the thing that lets a small team move like a larger one, and it is the backbone of any spec-driven AI deployment.

## What we do, and why it comes before the budget

This is exactly the work First AI Movers runs for European SMEs. Before a euro goes to tooling, we run a spec-driven planning and readiness assessment: we sit with you, find the one workflow worth automating, define the measurable outcome, confirm the data is reachable, set the guardrails, and agree the success and kill criteria. You leave with a map, the small-company version of that winning PRD, and a clear, bounded first project instead of an open-ended experiment. It is an AI readiness assessment small business teams can actually act on.

The reader is the hero here; we are the guide that holds the pen on the spec so your team does not start typing into an AI tool with no destination.

## Frequently Asked Questions

### Why do most AI pilots in small companies fail?

In the large majority of cases, the technology is not the problem, modern models are more than capable of the operational workflows SMEs need. Pilots fail upstream: no written spec, no measurable outcome, no scope boundary, and no agreed point at which to stop. The team starts prompting and the project drifts until it is quietly abandoned. The fix is to map the project before building any of it.

### How long should AI project planning take for an SME?

Far less than the build. The minimum viable AI spec, one workflow, one measurable outcome, the data needed, the guardrails, and success/kill criteria, is usually a focused session or two, not weeks. The Tekton team wrote their whole plan inside a 12-hour hackathon. The goal is not a perfect document; it is a clear, agreed boundary before you spend.

### What is the difference between a spec and just describing what we want?

_We want better customer support_ is a wish. A spec names the single workflow, attaches a number that proves success, lists the data the AI must see, sets what it must never do, and states the result at which you scale or stop. The difference is testability: a spec can be judged true or false; a description cannot, which is why descriptions lead to abandoned pilots.

### Does spec-driven planning slow down getting AI live?

No, it usually speeds it up. Planning first is what let the hackathon winners run independent workflows in parallel safely. For an SME, a clear map turns one vague project into a few independent, parallelisable steps, so a small team can move faster and avoid the rework that comes from building without a destination.

## Further Reading

- Five AI use cases that pay for themselves in ninety days
- An honest guide to AI adoption fears for European SME leaders
- The AI developer's definition of done
- What three hackathon winners teach small companies about AI

## We Write the Spec Before You Spend the Budget

If your last AI experiment did _a bit of everything badly_, the missing piece was almost certainly the map. Start with our [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) to find the one workflow worth automating and define what success looks like before you commit a euro to tooling. When you are ready to build on that foundation, our [AI consulting](https://radar.firstaimovers.com/page/ai-consulting) turns the spec into a bounded, working deployment, not an expensive toy.

Follow First AI Movers on LinkedIn for practical AI frameworks and decision guides.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "A Two-Person Team Out-Built 300 Rivals in 12 Hours, Because They Mapped First",
  "description": "Most failed AI pilots die from no plan, not bad tech. Learn the map-first AI project planning method that lets small European teams ship working AI.",
  "datePublished": "2026-07-17T22:17:15.365700+00:00",
  "dateModified": "2026-07-17T22:17:15.365700+00:00",
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
    "@id": "https://radar.firstaimovers.com/map-before-you-build-ai-project-planning-sme-2026"
  },
  "image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&h=630&fit=crop&q=80",
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
      "name": "Why do most AI pilots in small companies fail?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "In the large majority of cases, the technology is not the problem, modern models are more than capable of the operational workflows SMEs need. Pilots fail upstream: no written spec, no measurable outcome, no scope boundary, and no agreed point at which to stop. The team starts prompting and the p..."
      }
    },
    {
      "@type": "Question",
      "name": "How long should AI project planning take for an SME?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Far less than the build. The minimum viable AI spec, one workflow, one measurable outcome, the data needed, the guardrails, and success/kill criteria, is usually a focused session or two, not weeks. The Tekton team wrote their whole plan inside a 12-hour hackathon. The goal is not a perfect docum..."
      }
    },
    {
      "@type": "Question",
      "name": "What is the difference between a spec and just describing what we want?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "_We want better customer support_ is a wish. A spec names the single workflow, attaches a number that proves success, lists the data the AI must see, sets what it must never do, and states the result at which you scale or stop. The difference is testability: a spec can be judged true or false; a ..."
      }
    },
    {
      "@type": "Question",
      "name": "Does spec-driven planning slow down getting AI live?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No, it usually speeds it up. Planning first is what let the hackathon winners run independent workflows in parallel safely. For an SME, a clear map turns one vague project into a few independent, parallelisable steps, so a small team can move faster and avoid the rework that comes from building w..."
      }
    }
  ]
}
</script>
-->