---
title: "Choose the Reference That Tests the Decision"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/choose-the-reference-that-tests-the-decision"
published_date: "2026-09-27"
license: "CC BY 4.0"
---

> **TL;DR:** Five tests that decide whether a dataset, benchmark or prior deployment can carry the decision you have to make, before you build an evaluation on it.

Someone hands you a reference and expects it to end the argument. A public dataset, a benchmark score, a pilot at a company in your sector. It looks like evidence, it is cited with confidence, and it is usually offered at the moment a decision is about to cost money.

The question is never whether the reference is good. Published datasets and benchmarks are mostly careful work by people who documented exactly what they built. The question is whether that particular reference tests the particular decision in front of you. Most of the time it tests a neighbouring decision, and the gap between the two is where budget disappears.

Why this matters: an evaluation built on the wrong reference produces a number that is correct and useless. It will pass review, it will go in the deck, and it will not predict what happens when the system meets your data, your conditions and your users. Worse, it is hard to argue with afterwards, because nobody disputes the arithmetic. They dispute the fit, eighteen months late.

What follows is the five-test pass we run before accepting any reference as decision-grade, and the four verdicts it ends in: **ACCEPT**, **QUALIFY**, **SUBSTITUTE**, or **REJECT**.

## The reference is not the evidence. The fit is.

Write down the decision first, in one sentence, before you look at what you were given. Something like: can this model read our incoming supplier documents accurately enough that a person only checks the exceptions? Or: will this bearing monitoring approach warn us early enough on our own machines to change a maintenance window?

Now hold the reference up against that sentence. A reference earns the word evidence only if a poor result on it would actually change your mind. If a bad score would leave you saying "that was a different setting anyway", the reference was decoration from the start. This is the same discipline as declaring what an unclear outcome means before you run the test, which our note on why [not evaluable is itself a result](https://radar.firstaimovers.com/not-evaluable-is-a-result) works through in a research setting.

## Test 1: Can you name exactly what you were shown?

Ask for the identity of the reference, not its nickname. "The bearing dataset" and "the standard NER benchmark" are not names. A name is a persistent identifier plus a version, and the good sources give you one without being asked.

Two public examples show what that looks like. The Zenodo record [run-to-failure data set of ball bearings subjected to time-varying load and speed conditions](https://zenodo.org/records/10868257) carries a digital object identifier, 10.5281/zenodo.10868257, and a deposit year of 2024. The [Reuters corpora distributed by the United States National Institute of Standards and Technology](https://trec.nist.gov/data/reuters/reuters.html) are specified to a level most vendors never reach: the English Volume 1 collection is dated 1996-08-20 to 1997-08-19, with a release date of 2000-11-03, format version 1 and correction level 0.

Correction level is the detail worth noticing. A corpus can be re-released with fixes, which means two people can both say "we used Volume 1" and have used different bytes. If your supplier cannot tell you the version and the correction state of what they measured, you do not have a reproducible reference, you have an anecdote with a number attached.

## Test 2: Was it collected under the conditions you operate in?

This is where most references fail, and they fail quietly, because the topic matches.

Consider the bearing example. A run-to-failure set recorded under **time-varying** load and speed is not interchangeable with an older fault corpus recorded at constant speed, even when both are bearings from the same laboratory family. The whole difficulty of the varying-condition case is that the signal shifts with the operating point, which is why the accompanying conference work, "Remaining Useful Lifetime Estimation of Bearings Operating under Time-Varying Conditions", treats it as its own problem rather than a harder version of the constant-speed one. A method validated on the constant-speed corpus has not been shown to work on your variable-duty equipment.

The language case is sharper still. A named-entity benchmark from the 2003 shared task published at the Conference on Computational Natural Language Learning, "Introduction to the CoNLL-2003 Shared Task: Language-Independent Named Entity Recognition", measures finding people, places and organisations in news wire text from the 1990s. It does not tell you how a system reads Dutch legal correspondence containing personal data, and a strong score on it is not a privacy control.

Note the trap in the near miss. The multilingual Reuters Volume 2 collection does contain Dutch, over 487,000 stories across thirteen languages, so a supplier can honestly say "Dutch is covered". Read one line further: those stories were written by local reporters and are explicitly not parallel translations of each other, and they are still news. Dutch news from the 1990s is not your contract archive. Domain, register, era and document structure all have to survive the comparison, not just the language label.

## Test 3: May you actually use it for this purpose?

Rights are a separate question from quality, and they are decided by whoever holds them, not by how easy the download is.

The two public examples sit at opposite ends. The Zenodo bearing deposit is published under a Creative Commons Attribution 4.0 licence, which is permissive and asks for credit. The Reuters corpora are not a download at all: the distributing institute requires a request and signed agreements before release. Same field, same apparent availability, completely different obligations.

Three rules keep this clean. Read the licence on the record itself rather than a summary in a slide. Establish who signs, because an agreement naming a university research group does not extend to your commercial deployment. And never let anyone, including an adviser, tell you that a dataset is cleared for your commercial use as a reassurance; that is a conclusion for whoever holds the rights and, where it matters, your own counsel. If the rights question is unresolved, the reference is not usable yet, however good it is.

## Test 4: Who decided what "correct" means?

Every score compares a system output against something treated as truth. Ask where that truth came from, because the answer sets the ceiling on what the number can mean.

The strongest form is an observed outcome. Run-to-failure data is valuable precisely because the component actually failed: the end of life is recorded, not estimated by a reviewer. The next form is independent annotation, where people other than the system builders labelled the data under a published scheme, which is what a shared task provides. The weakest form, and the most common one in vendor material, is truth produced by the same party that produced the system, or by another model.

When the builder both answers and marks the paper, the number tells you about internal consistency, not accuracy. That is not fraud, it is just a different measurement, and it should be labelled as one. Our piece on the distance between [benchmark results and delivered value](https://radar.firstaimovers.com/delivering-ai-value-vs-benchmarks-2026) covers what usually survives that translation.

## Test 5: Does the reported metric move the decision you have to make?

A reference can be correctly identified, well matched, properly licensed, independently labelled, and still report the wrong quantity.

Translate the metric into your operating consequence before you accept it. An entity-level score says nothing directly about how many documents reach a person for review, which is the number that decides whether the workflow saves anyone time. A remaining-life estimate is only useful if its error is small relative to the notice you need to move a maintenance window; being right on average while wrong by a week is not actionable if your window is three days. Ask what error rate you can absorb, and in which direction, then check whether the reference reports that at all. Often it does not, and the honest conclusion is that a further measurement is needed.

## Reading the verdict: ACCEPT, QUALIFY, SUBSTITUTE, REJECT

One reference, one verdict, written down where the decision is recorded.

**ACCEPT** when all five tests pass: named and versioned, collected under conditions close enough to yours, usable under rights you actually hold, independently grounded, and reporting a quantity that changes your decision. Proceed, and cite it by identifier.

**QUALIFY** when the reference is sound but narrower than the claim it is being used to support. Keep it, and write the limit next to it: this evidence covers constant-speed operation, or news-domain text, and the question of our own conditions remains open. Most good references end here, and that is a healthy outcome rather than a failure.

**SUBSTITUTE** when the question is right and the reference is wrong. The fix is not a better model, it is a fitting reference: a public source collected under your conditions, or a small, purpose-built evaluation set from your own data with your own accepted truth. Budget for building one; it is usually cheaper than the wrong build it prevents.

**REJECT** when the reference cannot inform this decision at all, when it is unnamed or unversioned, when the truth was produced by the party being evaluated, or when nobody can state the rights position. Rejecting a reference is not rejecting the project. It means the project does not yet have the evidence to justify the next commitment, which is a finding worth having before the invoice.

## What to ask for in writing

Send five requests, and treat a missing answer as an answer.

1. The persistent identifier and version of every dataset or benchmark behind the claim.
2. The collection conditions: when, where, in which language and register, under what operating regime.
3. The licence or agreement, and who the signing party is.
4. How the reference truth was established, and by whom, independently of the system.
5. The metric definition, and the operating consequence it maps to for us.

Suppliers who work this way answer in a day and often volunteer the limits themselves. That response is itself a strong signal, usually a better one than the score. The same before-you-commit posture applies to the workflow itself, which our companion piece on the [seven questions that decide whether to automate at all](https://radar.firstaimovers.com/before-you-automate-a-workflow-7-questions) sets out.

## Frequently Asked Questions

### Does this mean public benchmarks are not useful?

They are very useful, for the decisions they were built to inform. A public benchmark is a well-documented measurement of a specific setting, and its documentation is usually the most honest part of the whole conversation. The failure is not in the benchmark, it is in borrowing its authority for a different setting.

### We have no public reference that matches our conditions. What then?

That is a SUBSTITUTE verdict, and it is common outside consumer domains. Build a small evaluation set from your own data with an accepted definition of correct, sized to the decision rather than to research convention. A few hundred well-chosen, honestly labelled items usually decides a workflow question that no public benchmark can.

### A supplier showed us a deployment at a company like ours. Is that a reference?

It can be, and the same five tests apply. Name it precisely, establish which conditions matched and which did not, confirm what you are permitted to be told and repeat, ask who measured the result, and check that the reported outcome is the quantity you care about. An unnamed result at an unnamed company fails Test 1 before you reach the interesting questions.

### Who should own this pass internally?

Whoever will be accountable for the outcome, supported by someone who can read a data record. In a company of twenty to fifty people that is usually the CTO or engineering leader together with the COO or operations leader who owns the process, with the founder involved only where the rights position is unresolved. It is deliberately not delegated to the party proposing the build.

## Related reading

- [Not evaluable is a result](https://radar.firstaimovers.com/not-evaluable-is-a-result), on declaring in advance what an unclear outcome will mean.
- [Delivering value against benchmark results](https://radar.firstaimovers.com/delivering-ai-value-vs-benchmarks-2026), on what survives the move from score to operation.
- [Seven questions before you automate a workflow](https://radar.firstaimovers.com/before-you-automate-a-workflow-7-questions), the decision that comes before this one.

Have a reference you are being asked to trust?

Send the reference, the decision it is supposed to settle, and the conditions you actually operate in. We will tell you whether it should be ACCEPT, QUALIFY, SUBSTITUTE, or REJECT before you build an evaluation on top of it.

Write to [info@firstaimovers.com](mailto:info@firstaimovers.com?subject=Reference%20decision) or read how we work on [AI consulting](https://radar.firstaimovers.com/page/ai-consulting).

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Choose the Reference That Tests the Decision",
  "description": "Five tests that decide whether a dataset, benchmark or prior deployment can carry the decision you have to make, before you build an evaluation on it.",
  "datePublished": "2026-09-27T21:35:37.865736+00:00",
  "dateModified": "2026-09-27T21:35:37.865736+00:00",
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
    "@id": "https://radar.firstaimovers.com/choose-the-reference-that-tests-the-decision"
  },
  "image": "https://images.unsplash.com/photo-1551836022-4c4c79ecde51?w=1200&h=630&fit=crop&q=80",
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
      "name": "Does this mean public benchmarks are not useful?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "They are very useful, for the decisions they were built to inform. A public benchmark is a well-documented measurement of a specific setting, and its documentation is usually the most honest part of the whole conversation. The failure is not in the benchmark, it is in borrowing its authority for ..."
      }
    },
    {
      "@type": "Question",
      "name": "We have no public reference that matches our conditions. What then?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "That is a SUBSTITUTE verdict, and it is common outside consumer domains. Build a small evaluation set from your own data with an accepted definition of correct, sized to the decision rather than to research convention. A few hundred well-chosen, honestly labelled items usually decides a workflow ..."
      }
    },
    {
      "@type": "Question",
      "name": "A supplier showed us a deployment at a company like ours. Is that a reference?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "It can be, and the same five tests apply. Name it precisely, establish which conditions matched and which did not, confirm what you are permitted to be told and repeat, ask who measured the result, and check that the reported outcome is the quantity you care about. An unnamed result at an unnamed..."
      }
    },
    {
      "@type": "Question",
      "name": "Who should own this pass internally?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Whoever will be accountable for the outcome, supported by someone who can read a data record. In a company of twenty to fifty people that is usually the CTO or engineering leader together with the COO or operations leader who owns the process, with the founder involved only where the rights posit..."
      }
    }
  ]
}
</script>
-->