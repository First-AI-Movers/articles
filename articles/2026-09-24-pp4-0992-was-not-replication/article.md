---
title: "0.992 Was Not Replication: Why One Exciting Posterior Is Not a Causal Story"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/pp4-0992-was-not-replication"
published_date: "2026-09-24"
license: "CC BY 4.0"
---

> **TL;DR:** A T-cell signal reached PP4 near 0.992 in one dataset. Three independent public blood T-cell resources did not reproduce it.

PP4 ≈ 0.992 looked exciting. Three independent public blood T-cell resources did not reproduce it. This case study, from our prospectively frozen analysis of public data, shows what it takes to stop one striking number from quietly becoming a causal story.

It is part of our technical report, [Falsification-First AI for Biological Target Assessment](https://radar.firstaimovers.com/falsification-first-ai-biological-target-assessment). Technical report; not peer reviewed. Nothing here is a clinical or therapeutic claim.

## The setup

While testing a different ulcerative colitis (UC) hypothesis, our workflow surfaced an unexpected signal for the gene TTPAL at the UC 20q13 locus.

**Our result (discovery).** In the discovery resource, the signal reached an apparent colocalization posterior of approximately PP4 = 0.992 in three gut-resident T-cell groups.

**Source fact.** PP4 is the posterior probability, under a Bayesian colocalization test, that two association signals (here, the disease association and the gene-expression association) share a single causal variant [1]. A value near 0.992 is the kind of number that ends up on a slide.

## The safeguard

We treated that number as nomination evidence only, not as a finding. Before reading any independent outcome, we:

- sealed the discovery dataset, so it could not be reused to "confirm" itself;
- prospectively defined the independent confirmation: which public cohorts were admissible, in what order, at which locus and window, and what result would count as replication.

## What happened

**Our result (independent test).**

- **Primary independent cohort.** OneK1K is a peripheral-blood single-cell eQTL resource [2], with up to approximately 954 donors in the eligible cell classes used by our frozen study. TTPAL had no usable supporting signal at the frozen locus and window. The maximum PP4 across the evaluated T-cell classes was approximately 0.031.
- **Secondary independent resources.** CEDAR [3] did not support the nominated TTPAL effect. Kasela 2017 [4] had no usable confirming signal.
- **No alternative winner.** No other local gene clearly won the independent confirmation analysis.

## Decision

`SINGLE_DATASET_ONLY`. The exciting discovery signal remained single-dataset-only.

## The caveat that travels with this result

The discovery cells were gut-resident T cells. The admissible independent public cohorts were peripheral blood. That difference matters:

- This result does **not** prove that a tissue-resident TTPAL effect is false.
- It does **not** say the discovery result was wrong.
- It shows only that the discovery signal did not independently reproduce on the public data available for this test.

Keeping that caveat next to the result is part of the method. Dropping it would turn an honest "not replicated here" into a misleading "disproven".

## Why it matters

The purpose of scientific diligence is not to make an exciting number disappear. It is to prevent one exciting number from silently becoming a causal story. An impressive posterior in one dataset is not replication, and the time to find that out is before the next expensive step, not after it.

For the general version of this discipline, see [what makes an AI system trustworthy, as NIST describes it](https://radar.firstaimovers.com/what-makes-an-ai-system-trustworthy-the-characteristics-nist-names-sum). The companion case study, [Not Evaluable Is a Result](https://radar.firstaimovers.com/not-evaluable-is-a-result), shows the other outcome that matters: a causal bridge that public data simply cannot decide.

## Try it on your own target

We have packaged this method as the [Biodius Target Challenge](https://radar.firstaimovers.com/biodius-scientific-diligence): a fixed-scope, five-business-day adversarial review of one target or mechanism, ending in a decision memo. **Send us one target + indication + rationale.** We will tell you whether it deserves the next expensive step. You can reach us at [info@firstaimovers.com](mailto:info@firstaimovers.com?subject=Biodius%20Target%20Challenge), or learn more [about First AI Movers](https://radar.firstaimovers.com/page/about).

## References

1. Giambartolomei et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. _PLoS Genetics_ 10(5): e1004383 (2014). https://doi.org/10.1371/journal.pgen.1004383
2. Yazar et al. Single-cell eQTL mapping identifies cell type-specific genetic control of autoimmune disease. _Science_ 376(6589): eabf3041 (2022). https://doi.org/10.1126/science.abf3041
3. Momozawa et al. IBD risk loci are enriched in multigenic regulatory modules encompassing putative causative genes. _Nature Communications_ 9: 2427 (2018). https://doi.org/10.1038/s41467-018-04365-8
4. Kasela et al. Pathogenic implications for autoimmune mechanisms derived by comparative eQTL analysis of CD4+ versus CD8+ T cells. _PLoS Genetics_ 13(3): e1006643 (2017). https://doi.org/10.1371/journal.pgen.1006643

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "0.992 Was Not Replication: Why One Exciting Posterior Is Not a Causal Story",
  "description": "A T-cell signal reached PP4 near 0.992 in one dataset. Three independent public blood T-cell resources did not reproduce it.",
  "datePublished": "2026-09-24T11:44:03.655945+00:00",
  "dateModified": "2026-09-24T11:44:03.655945+00:00",
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
    "@id": "https://radar.firstaimovers.com/pp4-0992-was-not-replication"
  },
  "image": "https://images.unsplash.com/photo-1581093588401-fbb62a02f120?w=1200&h=630&fit=crop&q=80",
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