---
title: "Not Evaluable Is a Result: When Public Human Genetics Cannot Decide the Causal Bridge"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/not-evaluable-is-a-result"
published_date: "2026-09-22"
license: "CC BY 4.0"
---

> **TL;DR:** A plausible mechanism survived AI review. Public human genetics still could not decide the causal bridge, so the hypothesis was not promoted.

A plausible mechanism survived AI review. Public human genetics still could not decide the causal bridge. This case study, from our prospectively frozen analysis of public data, shows why "not yet disproven" is a different thing from "ready for the next expensive step".

It is part of our technical report, [Falsification-First AI for Biological Target Assessment](https://radar.firstaimovers.com/falsification-first-ai-biological-target-assessment). Technical report; not peer reviewed. Nothing here is a clinical or therapeutic claim.

## The setup

**Hypothesis.** An AI research workflow generated a biologically coherent ulcerative colitis (UC) hypothesis. It linked a genetic signal in the HNF4A region, biology associated with SLC26A3, and a penetrable-mucus phenotype.

**Source facts.** The pieces were individually reasonable. The HNF4A region is an established UC susceptibility locus from genome-wide association analysis [1], and a penetrable inner colonic mucus layer has been described in patients with UC [2].

The hypothesis survived an initial frozen evidence bar and two independent synthetic falsifiers: AI reviewers tasked with breaking it rather than improving it. At that point, a conventional research summary would call it a lead.

## The challenge

We did not accept "survived review" as confirmation. We froze a genotype-resolved causal adjudication before inspecting the decisive outcomes. The rules, the admissible public data sources and the conditions for each possible verdict were fixed in advance, so the result could not quietly shape the method.

The question the adjudication had to answer was specific: does public human-genetic data support each link in the chain, from the genetic signal, to the gene, to the downstream biology?

## What happened

**Our result.** Link by link:

- **The gene assignment weakened.** Cell-type-resolved evidence did not support assigning the signal to HNF4A strongly enough under the frozen tiering.
- **The decisive bridge was not evaluable.** The HNF4A→SLC26A3 mediation step could not be evaluated from the lawful public aggregate data available, because no admitted public trans-eQTL or equivalent mediation surface could decide it.
- **Locus support softened.** Support at the SLC26A3 locus weakened under cell-state adjustment and turned out to depend on the dataset.
- **Tissue specificity stayed open.** Whether the effect is specific to the colon rather than the ileum remained not evaluable.

## Decision

The hypothesis was not promoted. The decisive causal bridge could not be established from public data.

To be precise about what that means: the hypothesis was **not disproven**. Its outcome is `NOT_EVALUABLE`: the available lawful public data cannot decide the step the whole mechanism depends on. Failure to falsify is not confirmation, and missing data is a result.

## Why it matters

A conventional research summary can easily turn "plausible and not yet disproven" into confidence. Two reviewers tried and failed to break it; the pieces each have literature behind them; the story reads well. The diligence question is different: **what causal statement has actually earned the next expensive step?**

Here, the honest answer was "not this one, not yet". That is useful to know before committing budget, and it points at the exact evidence that would change the answer: a way to measure the mediation link directly.

The same pattern shows up well beyond biology. Our guide on [why agentic AI autonomy is not ready to run unchecked](https://radar.firstaimovers.com/agentic-ai-reality-check-autonomy-not-ready) makes the business version of the argument. A companion case study, [0.992 Was Not Replication](https://radar.firstaimovers.com/pp4-0992-was-not-replication), shows the other common trap: one impressive number from one dataset.

## Try it on your own target

We have packaged this method as the [Biodius Target Challenge](https://radar.firstaimovers.com/biodius-scientific-diligence): a fixed-scope, five-business-day adversarial review of one target or mechanism, ending in a decision memo. **Send us one target + indication + rationale.** We will tell you whether it deserves the next expensive step. You can reach us at [info@firstaimovers.com](mailto:info@firstaimovers.com?subject=Biodius%20Target%20Challenge), or learn more [about First AI Movers](https://radar.firstaimovers.com/page/about).

## References

1. UK IBD Genetics Consortium. Genome-wide association study of ulcerative colitis identifies three new susceptibility loci, including the HNF4A region. _Nature Genetics_ 41(12): 1330-1334 (2009). https://doi.org/10.1038/ng.483
2. Johansson et al. Bacteria penetrate the normally impenetrable inner colon mucus layer in both murine colitis models and patients with ulcerative colitis. _Gut_ 63(2): 281-291 (2014). https://doi.org/10.1136/gutjnl-2012-303207

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Not Evaluable Is a Result: When Public Human Genetics Cannot Decide the Causal Bridge",
  "description": "A plausible mechanism survived AI review. Public human genetics still could not decide the causal bridge, so the hypothesis was not promoted.",
  "datePublished": "2026-09-22T09:34:22.183942+00:00",
  "dateModified": "2026-09-22T09:34:22.183942+00:00",
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
    "@id": "https://radar.firstaimovers.com/not-evaluable-is-a-result"
  },
  "image": "https://images.unsplash.com/photo-1551434678-e076c223a692?w=1200&h=630&fit=crop&q=80",
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
-->