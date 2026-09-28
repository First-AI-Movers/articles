---
title: "CRA Reporting Readiness: The Platform Field Is Not the Gap"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/cra-article-14-reporting-readiness-2026"
published_date: "2026-09-27"
license: "CC BY 4.0"
---

> **TL;DR:** The CRA platform already records when you became aware. The readiness gap is internal: awareness evidence, named ownership and a clock you can defend.

If your company puts a product with digital elements on the European market, a reporting obligation has been running since **11 September 2026**. On that date the Cyber Resilience Act reporting duties under Article 14 became applicable, and the Single Reporting Platform operated by the European Union Agency for Cybersecurity went live to receive the filings.

The common reading of this is a tooling problem: a new portal, a form to learn, an integration to build. That reading gets the difficulty backwards. The platform is straightforward and it already records the thing that matters most, including a field for the date and time you became aware of the incident or the actively exploited vulnerability.

Why this matters: every deadline in Article 14 is measured from **your awareness**, not from the platform, not from a customer complaint, and not from the moment somebody senior finds out. So the readiness question is not whether you can use a portal under pressure. It is whether you can say, with evidence, when you became aware, prove it months later, and get a filing submitted within 24 hours by a named person who is not asleep. Most of that work sits inside your own organisation, and none of it can be bought.

This is a readiness diagnostic, not legal advice. It ends in one of four verdicts: **OUT_OF_SCOPE**, **READY**, **GAPS**, or **NOT\_READY**. For how the obligations should be interpreted for your specific products, the European Commission publishes implementation guidance, and where the stakes are high this is a question for your own counsel.

## What Article 14 actually obliges, and from when

The current published deadlines form a cascade, and each stage starts from awareness rather than from the previous filing:

- **Early warning**: without undue delay and in any case within **24 hours** of becoming aware of the actively exploited vulnerability or severe incident.
- **Notification**: without undue delay and in any case within **72 hours** of becoming aware, carrying general information and an initial assessment.
- **Final report**: for an actively exploited vulnerability, no later than **14 days** after a corrective or mitigating measure such as a patch becomes available. For a severe incident, within **1 month** after the 72-hour notification.

Filings go through the platform, where the submitter selects the relevant national computer security incident response team designated as coordinator. Not every field is required at every stage: some that are optional in the 24-hour early warning become required in the 72-hour notification or in the final report, which is a detail worth knowing before the clock is running rather than during.

One scope point is easy to miss. The reporting duty applies from 11 September 2026 to products with digital elements that fall within scope, including products that were already on the market, rather than only to things you ship from now on. Your installed base is in scope, which for most companies is the larger surface.

## The counter on the platform is not your legal clock

Here is the detail that most readiness checklists have not caught up with, and it is documented openly in the platform's own published answers.

In the current release, the 72-hour counter displays a due date and time **48 hours after you submit the 24-hour early warning**, rather than 72 hours after you became aware. The consequence is stated plainly: in some cases a notification may be displayed as **overdue before 72 hours have actually elapsed** since awareness. The operator has said this logic will be updated in a future release to calculate the deadline from the awareness field instead, for both actively exploited vulnerabilities and severe incidents. For actively exploited vulnerabilities, a final-report counter is not currently implemented at all.

Two practical consequences follow, and both are about your own discipline rather than the tool:

1. **Do not let a screen define your obligation.** Your legal deadline runs from awareness. Track it yourself, from your own recorded timestamp, and treat any on-screen counter as a convenience that may currently be conservative or absent.
2. **File the early warning early, not at hour 23.** Because the displayed 72-hour deadline is derived from when you submitted the early warning, a late first filing compresses the window the platform shows you for the second one. Submitting promptly costs nothing and removes an entirely self-inflicted squeeze.

Neither point is a criticism of the platform. It is a young system, its operator has documented the current behaviour and the intended change, and reading that documentation is part of being ready.

## Test 1: Are you in scope, and as what?

Scope and role come before every other question. Are you a manufacturer of a product with digital elements, or are you a distributor, an importer, or the steward of an open-source project, each of which carries a different position? A company that only uses software is in a different situation from one that ships it.

Write down each product you place on the market, including the ones you inherited through an acquisition or maintain for a single large customer, and state your role for each. If this list does not exist, it is the first thing to build, because you cannot report on an inventory you do not have. If nothing you do places a product with digital elements on the market, your verdict is **OUT_OF_SCOPE** and you can stop here with that written down and dated.

## Test 2: When exactly did you become aware, and who says so?

This is the test that decides most outcomes, and it is almost entirely an internal evidence question.

Awareness arrives through unglamorous channels: a support ticket, an alert, a security researcher's email, a customer telephone call, a post on a forum, a monitoring threshold. Ask what your timestamp would be if you had to defend it a year later. Which record is authoritative, what time zone is it in, and does it survive a ticket being reassigned, merged, or closed and reopened?

Then ask the harder version. If a support engineer received a credible report on Friday afternoon and it reached the security owner on Monday, when did the company become aware? Decide that rule in advance, write it down, and make the recording of it automatic rather than a matter of someone's memory. The platform gives you a field for this timestamp; what it cannot give you is a defensible basis for the value you type into it.

## Test 3: Who owns the 24-hour filing, at 02:00 on a Sunday?

Twenty-four hours is a real constraint for a company of twenty to fifty people, where the CTO, the COO and the founder are often three names on the same short escalation list. Name the accountable person and at least two deputies, and make sure each is registered on the platform and has actually logged in **before** an incident, not during one. An access problem discovered at hour 20 is an avoidable failure.

Rehearse one filing end to end against a fabricated scenario. You are looking for the boring obstacles: who can approve saying something publicly consequential, who reviews wording that admits active exploitation, what happens when the named owner is on holiday, and how the deputies find out they are now responsible. A rehearsal that takes an afternoon reliably finds two or three of these.

Our [incident response playbook for European SMEs](https://radar.firstaimovers.com/ai-incident-response-playbook-european-smes-2026) covers the internal escalation mechanics this depends on, and the [NIS2 compliance guide](https://radar.firstaimovers.com/nis2-cybersecurity-compliance-guide-european-smes-2026) covers the adjacent regime, which is a different duty: NIS2 reporting attaches to you as an operating entity, while Article 14 here attaches to you as the maker of a product. A company can easily owe both, through different channels, for the same bad weekend.

## Test 4: Can you produce the 72-hour assessment without an API?

At the initial release, the platform provides **no application programming interface**, so notifications are submitted through its interface, and automated bulk submission is not available. Interface support may be considered in a future phase. What you may do, explicitly, is automate your own internal workflows and integrate the reporting requirements into your own systems and records.

That is the correct division of effort. Do not build towards an integration that does not exist yet. Instead make sure that, within 72 hours, you can assemble an initial assessment from evidence you already hold: what is affected and in which versions, what the likely root cause or triggering threat is, what mitigations are applied or under way, and what the severity and impact look like on current information. If producing that means three engineers reading chat history for a day, you have found a real gap, and it is an internal one.

Keep the wording cautious and conditional where the facts are still moving. An initial assessment is explicitly initial, and a final report follows later.

## Test 5: What happens after the notification?

Readiness does not end at hour 72. For an actively exploited vulnerability the final report is due no later than 14 days after a corrective or mitigating measure becomes available, which ties your reporting deadline to your **release** process. If your patch pipeline takes six weeks for a supported older version, that interacts with this obligation in a way worth understanding before it happens.

For a severe incident the final report is due within a month of the 72-hour notification. Note also that a counter is not currently implemented for the actively-exploited-vulnerability final report, so that one is yours to track without help from the screen.

## Reading the verdict: OUT_OF_SCOPE, READY, GAPS, NOT\_READY

One verdict, dated and written down where decisions are recorded, with the evidence beside it.

**OUT_OF_SCOPE** when you do not place products with digital elements on the European market in a role that carries the duty. Record the reasoning and the date, and revisit it when you ship something new or acquire a product line.

**READY** when you have a product inventory with roles, a written awareness rule, an automatic and durable awareness timestamp, a named owner plus registered deputies who have logged in, a rehearsed filing, and the ability to assemble an initial assessment inside 72 hours from evidence you already keep.

**GAPS** when the obligation is understood and most of the structure exists, but one or two specific things are missing, most commonly the awareness rule or the deputy registration. Name each gap with an owner and a date. This is where most prepared companies honestly sit.

**NOT\_READY** when awareness cannot be timestamped defensibly, or no individual owns a 24-hour filing, or nobody has logged in to the platform. This is not a reason for alarm, but it is a reason to spend the next fortnight on it rather than on something more interesting, because the duty is already live and the first hours of a real event are the worst possible time to discover any of it.

## What to put in place this month

Five items, in order, none of which needs new software:

1. The product inventory, with your role for each product and the supported versions.
2. The written awareness rule, including the multi-channel and weekend cases, and where the authoritative timestamp lives.
3. The named owner and two registered deputies, each having logged in to the platform at least once.
4. One rehearsed filing against a fabricated scenario, with the obstacles written down and assigned.
5. An evidence checklist for the 72-hour initial assessment, mapped to systems you already run.

For the current published answers on registration, deadlines, fields and platform behaviour, read the operator's own [frequently asked questions for the reporting platform](https://www.enisa.europa.eu/topics/product-security/vulnerability-services/eu-incident-response-and-cyber-crisis-management/single-reporting-platform-srp/frequently-asked-questions), which is updated as the system is implemented. Check it again before you rely on any specific behaviour described here, including the counter detail above, because the operator has said that part is due to change.

## Frequently Asked Questions

### Does the platform record when we became aware, or not?

It does. There is a field for the date and time you became aware of the incident or actively exploited vulnerability, so any advice built on the idea that awareness time goes unrecorded is out of date. What is currently true is narrower: the 72-hour counter shown on screen is presently derived from when you submitted the 24-hour early warning, and the operator has said it will be changed to use the awareness field.

### We are a small team. Is a 24-hour filing realistic?

It is, but only if the decision structure is settled in advance. The 24-hour early warning is a warning, not a full analysis, and not every field is required at that stage. What makes small teams miss it is not analysis time, it is an unregistered account, an absent approver, or nobody being sure whose job it is.

### Do we need to build an integration?

No, and at the initial release you cannot: no interface for automated submission is provided, and filings go through the platform directly. Automate your own internal capture and evidence instead, which is where the work pays off regardless of what the platform later supports.

### Is this the same as our NIS2 reporting?

No. They are different duties with different triggers and channels, and they can both apply to the same organisation. Treat them as two obligations that may share evidence, never as one filing.

## Related reading

- [Incident response playbook for European SMEs](https://radar.firstaimovers.com/ai-incident-response-playbook-european-smes-2026), on the internal escalation this depends on.
- [NIS2 compliance guide](https://radar.firstaimovers.com/nis2-cybersecurity-compliance-guide-european-smes-2026), on the adjacent entity-level regime.
- [Compliance monitoring checklist](https://radar.firstaimovers.com/ai-compliance-monitoring-checklist-european-smes-2026), on keeping obligations observable rather than remembered.

Not sure whether your products are in scope, or whether your awareness timestamp would hold up?

Send the product list, how a report reaches you today, and who would file inside 24 hours. We will tell you whether your position is OUT_OF_SCOPE, READY, GAPS, or NOT\_READY, and what the shortest path to READY looks like.

Start with the [readiness assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) or write to [info@firstaimovers.com](mailto:info@firstaimovers.com?subject=CRA%20reporting%20readiness).

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "CRA Reporting Readiness: The Platform Field Is Not the Gap",
  "description": "The CRA platform already records when you became aware. The readiness gap is internal: awareness evidence, named ownership and a clock you can defend.",
  "datePublished": "2026-09-27T21:37:41.208818+00:00",
  "dateModified": "2026-09-27T21:37:41.208818+00:00",
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
    "@id": "https://radar.firstaimovers.com/cra-article-14-reporting-readiness-2026"
  },
  "image": "https://images.unsplash.com/photo-1556761175-4b46a572b786?w=1200&h=630&fit=crop&q=80",
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
      "name": "Does the platform record when we became aware, or not?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "It does. There is a field for the date and time you became aware of the incident or actively exploited vulnerability, so any advice built on the idea that awareness time goes unrecorded is out of date. What is currently true is narrower: the 72-hour counter shown on screen is presently derived fr..."
      }
    },
    {
      "@type": "Question",
      "name": "We are a small team. Is a 24-hour filing realistic?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "It is, but only if the decision structure is settled in advance. The 24-hour early warning is a warning, not a full analysis, and not every field is required at that stage. What makes small teams miss it is not analysis time, it is an unregistered account, an absent approver, or nobody being sure..."
      }
    },
    {
      "@type": "Question",
      "name": "Do we need to build an integration?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No, and at the initial release you cannot: no interface for automated submission is provided, and filings go through the platform directly. Automate your own internal capture and evidence instead, which is where the work pays off regardless of what the platform later supports."
      }
    },
    {
      "@type": "Question",
      "name": "Is this the same as our NIS2 reporting?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. They are different duties with different triggers and channels, and they can both apply to the same organisation. Treat them as two obligations that may share evidence, never as one filing."
      }
    }
  ]
}
</script>
-->