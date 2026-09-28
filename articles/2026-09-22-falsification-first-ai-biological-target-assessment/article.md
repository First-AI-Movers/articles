---
title: "Falsification-First AI for Biological Target Assessment: What Four Prospective Experiments Taught Us About Scientific Agents"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/falsification-first-ai-biological-target-assessment"
published_date: "2026-09-22"
license: "CC BY 4.0"
---

> **TL;DR:** A technical report on four prospective experiments: why scientific AI is more useful when it preserves negative evidence and stops when data runs out.

_Why autonomous scientific systems should be rewarded for killing weak hypotheses, not generating more of them._

**Technical report; not peer reviewed.** Version 1, September 2026. This report describes our prospectively frozen analysis of public data. It makes no clinical or therapeutic claim, and it does not claim validated drug discovery.

## Abstract

Generative AI can increase the speed of biological research without increasing the reliability of the resulting scientific decisions. We developed and prospectively tested a falsification-first workflow for AI-assisted biological target assessment in which evaluation criteria, source boundaries, lineage rules and stop conditions are fixed before decisive outcomes are read. Across four sequential experiments in pulmonary fibrosis and inflammatory bowel disease, the program repeatedly produced results that were less flattering but more decision-useful than the original hypotheses. A complex scientific-agent architecture did not justify its additional complexity against a strong agentic baseline; a smaller safeguard layer transferred while preserving useful coverage; a mechanistically plausible IBD hypothesis remained not evaluable when a required human-genetic mediation link could not be tested from lawful public data; and an unexpected T-cell colocalization signal with a discovery posterior near 0.992 failed to reproduce in independent public blood T-cell cohorts. These studies do not establish a therapeutic target or clinical mechanism. They instead support a narrower proposition: scientific AI becomes more useful when it is designed to preserve negative evidence, collapse non-independent evidence, resist post-result method changes and terminate explicitly when the available data cannot support the next causal claim.

### How to read this report

We keep five kinds of statement apart, and we label them where the difference matters:

- **Source fact:** what a cited public source reports.
- **Author claim:** what the authors of a source argue, which is not the same as what their data show.
- **Our result:** the outcome of our prospectively frozen analysis of public data.
- **Inference:** what we think a result implies, stated as our reading.
- **Hypothesis:** a claim that has not been tested yet.

## The problem: AI increases scientific throughput, not truth

AI research agents are good at producing plausible biology. They can read a large literature quickly, connect a genetic signal to a pathway, and write a coherent mechanism in minutes. That speed is real. What it does not do on its own is make the resulting decision more reliable.

The failure modes are familiar to anyone who has sat in a target review. Multiple papers that look like independent support share one cohort. A causal chain has one link nobody has actually measured. A striking statistic comes from a single dataset. A method gets quietly adjusted after the first results come in. More throughput makes each of these easier to produce and harder to notice.

So the question we set out to test was not "can an AI system generate good hypotheses?" It was narrower and, we think, more useful: **can an AI-assisted workflow be built so that it reliably tells you when a hypothesis has not earned the next expensive step?**

## Methods: how the workflow resists being fooled

Every experiment in this program shared five disciplines.

1. **Prospective freezes.** Evaluation criteria, source boundaries, lineage rules and stop conditions were written down and fixed before the decisive outcomes were read. We prospectively froze analysis rules before reading decisive outcomes, and a rule that changed after a result was treated as a new experiment, not a correction.
2. **Lineage independence.** We distinguish publications from independent cohorts and collapse shared lineages. Five papers drawing on one cohort count as one line of evidence, not five.
3. **Contradiction and null preservation.** We deliberately preserved negative, contradictory and not-evaluable results. A failed program, a null association or a contradicting cohort is kept in the record, not filtered out of the summary.
4. **Reproducibility.** Each decision rule, source boundary and terminal outcome was recorded before and after the decisive read, so the path from evidence to decision can be retraced.
5. **Synthetic adversarial review.** Independent AI reviewers were tasked with falsifying a candidate rather than improving it. Their challenges were then adjudicated against primary sources. A synthetic reviewer failing to break a claim was never treated as confirmation.

The method runs as one chain:

`claim or target thesis → source identity and provenance → human-genetics and causal-gene evidence where applicable → study and cohort lineage collapse → contradictions, nulls and failed programs → causal-chain audit → novelty and prior-art attack → independent synthetic expert challenge → primary-source adjudication → cheapest discriminating next evidence → ADVANCE | REWORK | STOP | NOT_EVALUABLE`

`NOT_EVALUABLE` is a first-class outcome. It means the available lawful public data cannot decide the question, and it is reported as such rather than rounded up to "promising" or down to "false".

## Experiment 1: a heavier architecture against a strong agentic baseline

**Our result.** In a prospective benchmark in idiopathic pulmonary fibrosis (IPF), a heavier scientific-agent architecture did not demonstrate superior useful biological coverage over a strong agentic research workflow.

The heavier system was not useless. It demonstrated useful safeguards around leakage, provenance, lineage and reproducibility. But its additional machinery did not buy additional useful biology.

**Inference.** The result argued against retaining complexity merely because it looked rigorous. The lesson we took forward: **rigor has to earn its complexity.**

## Experiment 2: a lean trust layer that transferred

We then reduced the safeguard stack, prospectively, to a small scientific trust layer and transfer-tested it on inflammatory bowel disease (IBD), a different disease area from the one it was designed in.

**Our result.**

- The lean layer preserved the agentic output rather than deleting coverage.
- It added measurable, decision-relevant annotations around provenance, independence, boundaries and contradiction handling.
- It transferred without IPF-specific, result-aware tuning.

**Inference.** The useful product was not a larger autonomous scientist. It was a small layer that made strong AI research harder to fool. This does not show that the layer produces better drug discovery; it shows that it adds decision-relevant scrutiny without removing useful coverage.

## Case study: a plausible mechanism that public human genetics could not decide

**Hypothesis.** A generated hypothesis linked an HNF4A-region ulcerative colitis (UC) genetic signal, SLC26A3-associated biology and a penetrable-mucus phenotype.

**Source facts.** The HNF4A region is an established UC susceptibility locus from genome-wide association analysis [5]. A penetrable inner colonic mucus layer has been described in patients with UC [6].

The hypothesis survived the initial frozen candidate bar and two independent synthetic falsifiers. Many research workflows would stop there and call it a lead.

**Our result.** A deeper, prospectively frozen adjudication using public human genetics then found:

- cell-type-resolved evidence did not support the HNF4A assignment strongly enough under the frozen tiering;
- the HNF4A→SLC26A3 mediation link was **not evaluable** from lawful public aggregate data, because no admitted public trans-eQTL or equivalent mediation surface could decide it;
- the SLC26A3 locus support weakened under state adjustment and dataset dependence;
- colon-versus-ileum specificity remained not evaluable.

**Decision.** The hypothesis was not promoted. The decisive causal bridge could not be established from public data.

This is not a claim that the hypothesis is false. It was not disproven. Failure to falsify is not confirmation, and missing data is a result. The full case is written up in [Not Evaluable Is a Result](https://radar.firstaimovers.com/not-evaluable-is-a-result).

## Case study: an exciting posterior that did not replicate

**Our result (discovery).** During the analysis above, an unexpected TTPAL signal at the UC 20q13 locus reached a colocalization posterior of approximately PP4 = 0.992 in three gut-resident T-cell groups in the discovery resource. PP4 is the posterior probability, under a Bayesian colocalization test, that two association signals share a single causal variant [1].

We treated that number as nomination evidence only. We sealed the discovery dataset and prospectively defined an independent confirmation before reading any independent outcome.

**Our result (independent test).**

- **Primary independent cohort:** OneK1K, a peripheral-blood single-cell eQTL resource [2], with up to approximately 954 donors in the eligible cell classes used by the frozen study. TTPAL had no usable supporting signal at the frozen locus and window; the maximum PP4 in the evaluated T-cell classes was approximately 0.031.
- **Secondary independent resources:** CEDAR [3] did not support the nominated TTPAL effect, and Kasela 2017 [4] had no usable confirming signal.
- No local gene clearly won the independent confirmation analysis.

**Decision.** `SINGLE_DATASET_ONLY`. The exciting discovery signal remained single-dataset-only.

**The caveat that has to travel with this result.** The discovery cells were gut-resident T cells; the admissible independent public cohorts were peripheral blood. So this result does not prove that a tissue-resident TTPAL effect is false, and it does not say the discovery result was wrong. It shows only that the discovery signal did not independently reproduce on the public data available for this test. An impressive posterior in one dataset is not replication. The full case is written up in [0.992 Was Not Replication](https://radar.firstaimovers.com/pp4-0992-was-not-replication).

## What failed: the negative results in one place

We are listing these together because a report that only shows its successes would contradict its own method.

| Experiment | What we hoped | What happened |
|---|---|---|
| Heavier architecture | More useful biology from more machinery | No demonstrated gain in useful coverage over a strong agentic baseline |
| Lean trust layer | Keep the safeguards, lose the weight | Worked; preserved coverage and transferred to a new disease area |
| Mucus hypothesis | A promotable causal chain | Not promoted: the decisive mediation link was not evaluable from public data |
| T-cell signal | Independent replication of PP4 ≈ 0.992 | Not reproduced in the independent public blood cohorts |

Three of the four outcomes are, by the standard of a pitch deck, disappointing. By the standard of a decision, each of them is useful: they tell you what not to fund yet, and why.

## Limitations

- **Four experiments, two disease areas.** This is a small program. It supports a narrow claim about workflow design, not a general claim about AI in biology.
- **Public data only.** Every adjudication used lawful public aggregate data. Our `NOT_EVALUABLE` outcome reflects what public data cannot answer, not what a well-designed private study could.
- **Tissue mismatch in replication.** The independent T-cell cohorts were peripheral blood, while the discovery signal came from gut-resident cells.
- **Synthetic reviewers are not experts.** AI falsifiers were used to generate challenges, not to replace qualified scientific judgment. Every challenge was adjudicated against primary sources.
- **No external validation.** These are our own prospective experiments. They have not been independently replicated or peer reviewed.
- **No wet-lab work.** Nothing here was tested experimentally.

## Implications for target assessment and scientific diligence

**Inference.** If AI makes it cheap to produce convincing biology, the scarce thing becomes the discipline to decide which convincing stories have actually earned money. That points to a specific job for scientific AI: not generating more hypotheses, but attacking the one you are about to fund.

In practice that means asking, before the next expensive step:

- Which pieces of evidence are genuinely independent, once shared cohorts are collapsed?
- Which link in the causal chain has actually been measured, and which has only been assumed?
- What contradicting results and failed programs exist, and were they looked for?
- Is the striking statistic replicated, or is it one dataset?
- What is the cheapest piece of evidence that would change the decision?

Our current commercial hypothesis is that this workflow is useful as scientific diligence before a costly downstream decision. We have packaged it as the [Biodius Target Challenge](https://radar.firstaimovers.com/biodius-scientific-diligence) to test that hypothesis with real target decisions. For how this fits a broader view of checking AI output before acting on it, see our guide to [verifier agents and trustworthy AI output](https://radar.firstaimovers.com/verifier-agents-trustworthy-ai-output-sme-2026).

## Reproducibility and provenance

For each experiment, the decision rules, source boundaries, stop conditions and terminal outcomes were recorded in a version-controlled record before and after the decisive read. Public inputs are identified in this report by their public publications. The internal records are retained so that each decision can be retraced; this report does not publish them.

For more about the team behind this work, see [About First AI Movers](https://radar.firstaimovers.com/page/about).

## No clinical or therapeutic claim

This report does not establish a therapeutic target, a clinical mechanism, or the safety or efficacy of any intervention. It does not claim validated drug discovery. Nothing in it is medical advice, and none of it substitutes for qualified scientific, clinical, legal, patent or regulatory review.

## References

1. Giambartolomei et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. _PLoS Genetics_ 10(5): e1004383 (2014). https://doi.org/10.1371/journal.pgen.1004383
2. Yazar et al. Single-cell eQTL mapping identifies cell type-specific genetic control of autoimmune disease. _Science_ 376(6589): eabf3041 (2022). https://doi.org/10.1126/science.abf3041
3. Momozawa et al. IBD risk loci are enriched in multigenic regulatory modules encompassing putative causative genes. _Nature Communications_ 9: 2427 (2018). https://doi.org/10.1038/s41467-018-04365-8
4. Kasela et al. Pathogenic implications for autoimmune mechanisms derived by comparative eQTL analysis of CD4+ versus CD8+ T cells. _PLoS Genetics_ 13(3): e1006643 (2017). https://doi.org/10.1371/journal.pgen.1006643
5. UK IBD Genetics Consortium. Genome-wide association study of ulcerative colitis identifies three new susceptibility loci, including the HNF4A region. _Nature Genetics_ 41(12): 1330-1334 (2009). https://doi.org/10.1038/ng.483
6. Johansson et al. Bacteria penetrate the normally impenetrable inner colon mucus layer in both murine colitis models and patients with ulcerative colitis. _Gut_ 63(2): 281-291 (2014). https://doi.org/10.1136/gutjnl-2012-303207

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Falsification-First AI for Biological Target Assessment: What Four Prospective Experiments Taught Us About Scientific Agents",
  "description": "A technical report on four prospective experiments: why scientific AI is more useful when it preserves negative evidence and stops when data runs out.",
  "datePublished": "2026-09-22T09:32:18.195262+00:00",
  "dateModified": "2026-09-22T09:32:18.195262+00:00",
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
    "@id": "https://radar.firstaimovers.com/falsification-first-ai-biological-target-assessment"
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
  "@type": "HowTo",
  "name": "Falsification-First AI for Biological Target Assessment: What Four Prospective Experiments Taught Us About Scientific Agents",
  "description": "A technical report on four prospective experiments: why scientific AI is more useful when it preserves negative evidence and stops when data runs out.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Prospective freezes.",
      "text": "Evaluation criteria, source boundaries, lineage rules and stop conditions were written down and fixed before the decisive outcomes were read. We prospectively froze analysis rules before reading decisive outcomes, and a rule that changed after a result was treated as a new experiment, not a correction."
    },
    {
      "@type": "HowToStep",
      "name": "Lineage independence.",
      "text": "We distinguish publications from independent cohorts and collapse shared lineages. Five papers drawing on one cohort count as one line of evidence, not five."
    },
    {
      "@type": "HowToStep",
      "name": "Contradiction and null preservation.",
      "text": "We deliberately preserved negative, contradictory and not-evaluable results. A failed program, a null association or a contradicting cohort is kept in the record, not filtered out of the summary."
    },
    {
      "@type": "HowToStep",
      "name": "Reproducibility.",
      "text": "Each decision rule, source boundary and terminal outcome was recorded before and after the decisive read, so the path from evidence to decision can be retraced."
    },
    {
      "@type": "HowToStep",
      "name": "Synthetic adversarial review.",
      "text": "Independent AI reviewers were tasked with falsifying a candidate rather than improving it. Their challenges were then adjudicated against primary sources. A synthetic reviewer failing to break a claim was never treated as confirmation."
    }
  ]
}
</script>
-->