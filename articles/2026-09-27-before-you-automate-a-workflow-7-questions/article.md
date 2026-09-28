---
title: "Before You Automate a Workflow: 7 Questions That Decide BUILD, REPAIR_FIRST, DEFER, or STOP"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/before-you-automate-a-workflow-7-questions"
published_date: "2026-09-27"
license: "CC BY 4.0"
---

> **TL;DR:** Seven questions that decide whether one workflow should be automated now, repaired first, deferred, or left alone before you commit budget to an AI build.

The useful first deliverable of an automation project is not a list of AI ideas. It is enough evidence to decide whether one specific workflow should be automated now, repaired first, deferred, or deliberately left alone. Most teams skip that decision. They pick the workflow that annoys them most, ask a vendor or an internal engineer for a demo, and discover the real constraints after the budget is committed.

Why this matters: a workflow that is not decision-ready cannot be automated well, only faster. If the process produces noise, automation produces noise at scale. If the process depends on a fact nobody can access lawfully, the agent will guess. If nobody can define what "good enough" means, the build never leaves pilot. The seven questions below are the diagnostic we use before any implementation conversation. Each one ends in a fact you can write down, and the last one ends in exactly one verdict: **BUILD**, **REPAIR\_FIRST**, **DEFER**, or **STOP**.

They are written for the people who own the budget and the risk: the CTO or technical leader who will be asked to build it, the COO or Head of Operations who lives with the workflow today, and the founder of a 20-person company who is being told that "AI automation" is the obvious next step.

## 1. What decision or outcome does the workflow exist to produce?

Start with the output, not the steps. Every workflow exists to produce something a person acts on: an approved invoice, a quote a customer can accept, a ticket routed to the right engineer, a compliance record an auditor will trust. Write that outcome down in one sentence, and name who consumes it.

If the answer is vague, stop here for a moment. A workflow whose output is not decision-useful, one that generates reports nobody reads or updates a spreadsheet nobody trusts, is a candidate for removal, not for automation. Automating the steps only accelerates the noise. Some of the best outcomes of this question are workflows that get deleted.

If the output is clearly useful, you now have the acceptance target that every later question refers back to.

## 2. Where is time or failure actually concentrated?

Capture a current baseline in a directly observable unit before anyone estimates savings: manual minutes per item, rework count, wait time between handoffs, exception rate, or how often the same item is touched twice. Measure it for a week or two, or pull it from the systems you already have. Do not invent the number, and do not let a vendor invent it for you.

Two things happen when you do this. First, you often find that the expensive part is not the part people complain about. The complaint is usually about tedium; the cost is usually in exceptions, waiting, and rework. Second, you get the only baseline that can later tell you whether the automation worked. Without it, every later claim of improvement is a story.

If you cannot measure the workflow at all, that is a finding in itself. It usually points to REPAIR\_FIRST, because a process nobody can observe is not one you can safely hand to software.

## 3. What is the strongest non-AI alternative?

For every candidate workflow, name the best alternative that involves no model at all. The honest list is usually short and often better than a bespoke agent: remove the step entirely, change a configuration in a system you already pay for, connect two systems with a plain integration, write a deterministic rule, or buy an existing product that already does this well.

The reason to be strict here is cost of ownership, not fashion. A rule-based check or a native integration is cheaper to test, cheaper to explain to an auditor, and cheaper to keep running when the underlying system changes. An AI component earns its place only where the input is genuinely unstructured or the judgement is genuinely fuzzy, and even then it should be the smallest possible part of the pipeline.

Our guide to the [four-level automation maturity ladder](https://radar.firstaimovers.com/ai-workflow-automation-maturity-ladder-smes) covers where deterministic automation stops and where model-based steps start to make sense.

## 4. Which systems and data must be touched?

Name the integration boundary explicitly: every system the workflow reads from, every system it writes to, and every fact it needs that lives in someone's head, inbox, or personal spreadsheet. Then classify each input. Is it available through a supported interface? Is it private, regulated, or subject to a contract? Is it operationally fragile, meaning it changes shape without notice?

This question is where many "quick wins" quietly become platform projects. A workflow that needs three facts from a system with no supported interface, one fact that is personal data with no lawful basis for the new use, and one fact that only exists in a manager's memory is not ready. Naming the boundary also tells you who has to be in the room: the data owner, the system owner, and whoever answers for privacy.

If the boundary is clean, note it and move on. If it is not, the verdict is almost always REPAIR\_FIRST or DEFER, and you now know exactly which dependency to fix.

## 5. What can fail, and who notices?

Define the failure modes before building around a demo. For each one, decide three things: whether a human is in the loop before the effect lands, how the effect is rolled back, and what audit trail exists afterwards. Then write down the one thing that must never fail silently. In a quoting workflow that is a wrong price reaching a customer; in a payroll workflow it is a wrong amount reaching a bank.

Silent failure is the specific risk that separates automation from delegation. A person who is unsure asks; software that is unsure proceeds. If the workflow would fall under the EU AI Act's high-risk categories, human oversight is a design requirement under [Article 14 of the regulation](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng), not a preference. Even outside those categories, the operational question is the same: who sees the failure, how quickly, and with what means to undo it.

The public account of [why pure automation failed at a large fintech and had to be partially reversed](https://radar.firstaimovers.com/klarna-ai-reality-check-automation-failed) is a useful reminder that the failure that matters is often the one nobody was watching for.

## 6. What does "good enough" mean before production?

Specify the evaluation and the acceptance threshold before anyone builds. That means a reference set of real past items with known correct outcomes, an agreed measure (accuracy on the reference, exception rate, time to resolution), and a threshold below which the automation stays out of production. The reference should be assembled by the people who own the workflow, not by the people who want to build the automation.

This is the question a demo is designed to skip. A demo shows the happy path on chosen examples; a reference tests the decision on the examples that actually arrive. If you cannot assemble a reference from your own history, you have learned that the workflow is not yet observable enough, which is again REPAIR\_FIRST territory.

Write the threshold down with the baseline from question 2. Together they are the whole contract: here is where we are, here is the number at which we switch this on, here is the number at which we switch it off.

## 7. What is the decision today?

Pick exactly one verdict and record the evidence behind it. Do not leave the workshop with a "maybe".

- **BUILD.** The outcome is decision-useful, the baseline is measured, no non-AI alternative dominates, the integration boundary is clean, failure modes have owners and rollbacks, and a reference with a threshold exists. Proceed to the smallest implementation that can be tested against that reference.
- **REPAIR\_FIRST.** The workflow is worth automating but is not ready: the process is unobservable, the data boundary is broken, or the output is inconsistent. Fix the named dependency first. This is the most common honest verdict.
- **DEFER.** Automation is plausible but the expected value does not beat the current cost, or a dependency is changing (a system migration, a regulatory clarification). Set the condition that reopens the decision and a date to re-check it.
- **STOP.** The workflow should not be automated: the output is not useful, a non-AI alternative removes the need, or the failure modes cannot be made acceptable. Retire the idea explicitly so it does not come back as someone else's project.

A single-page record with the seven answers and the verdict is the deliverable. It is more valuable than a roadmap of twenty automation ideas, because it is the one document that lets the technical leader, the operations leader, and the budget owner say the same thing about the same workflow.

## How this fits with a wider AI plan

This diagnostic is deliberately narrow: one workflow, one verdict. If you are earlier in the process and do not yet know which workflows to examine, our [map-first method for planning an AI project](https://radar.firstaimovers.com/map-before-you-build-ai-project-planning-sme-2026) is the step before this one. Run the map, pick the one workflow that matters most, then run the seven questions on it before anyone writes code.

Teams that do this in order tend to find that their first automation is smaller and more boring than they expected, and that it ships.

## Get a decision on one workflow

Have one workflow you are unsure is worth automating? Send the workflow, the systems it touches, and the current manual pain. We will tell you whether the next step should be BUILD, REPAIR\_FIRST, DEFER, or STOP before you commit to an implementation. Write to [info@firstaimovers.com](mailto:info@firstaimovers.com?subject=Workflow%20decision), or read how we work with European SME leaders on [AI consulting](https://radar.firstaimovers.com/page/ai-consulting).

## Frequently Asked Questions

### Q: Can we run the seven questions ourselves?

Yes. The questions are designed to be answered by the people who own the workflow, and the deliverable is a one-page record. Outside help is useful when the team cannot agree on the baseline, cannot access the systems involved, or wants an independent view on the non-AI alternatives.

### Q: What if the answer to most workflows is REPAIR\_FIRST?

That is the normal result in a growing company, and it is good news: it means you have found the specific process and data problems that would otherwise have surfaced halfway through an implementation. Fix the one that unblocks the most valuable workflow first.

### Q: How long should the diagnostic take?

For one workflow with cooperative owners, a few working days: one to gather the baseline and the system list, one for the workshop, and time to write the record. If it takes much longer, the workflow is probably not observable enough yet, which is itself a finding.

### Q: Does a STOP verdict mean we were wrong to consider automation?

No. STOP is a legitimate outcome and often a cheap one. The cost of a STOP verdict is a few days of attention; the cost of discovering the same thing after a build is months.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Before You Automate a Workflow: 7 Questions That Decide BUILD, REPAIR\_FIRST, DEFER, or STOP",
  "description": "Seven questions that decide whether one workflow should be automated now, repaired first, deferred, or left alone before you commit budget to an AI build.",
  "datePublished": "2026-09-27T12:09:32.121077+00:00",
  "dateModified": "2026-09-27T12:09:32.121077+00:00",
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
    "@id": "https://radar.firstaimovers.com/before-you-automate-a-workflow-7-questions"
  },
  "image": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=1200&h=630&fit=crop&q=80",
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
      "name": "Q: Can we run the seven questions ourselves?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The questions are designed to be answered by the people who own the workflow, and the deliverable is a one-page record. Outside help is useful when the team cannot agree on the baseline, cannot access the systems involved, or wants an independent view on the non-AI alternatives."
      }
    },
    {
      "@type": "Question",
      "name": "Q: What if the answer to most workflows is REPAIR\_FIRST?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "That is the normal result in a growing company, and it is good news: it means you have found the specific process and data problems that would otherwise have surfaced halfway through an implementation. Fix the one that unblocks the most valuable workflow first."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How long should the diagnostic take?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For one workflow with cooperative owners, a few working days: one to gather the baseline and the system list, one for the workshop, and time to write the record. If it takes much longer, the workflow is probably not observable enough yet, which is itself a finding."
      }
    },
    {
      "@type": "Question",
      "name": "Q: Does a STOP verdict mean we were wrong to consider automation?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. STOP is a legitimate outcome and often a cheap one. The cost of a STOP verdict is a few days of attention; the cost of discovering the same thing after a build is months."
      }
    }
  ]
}
</script>
-->