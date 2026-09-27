---
title: "Why We Built a Service That Tries to Kill Your Biological Target"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/why-we-built-a-service-that-tries-to-kill-your-target"
published_date: "2026-09-22"
license: "CC BY 4.0"
---

> **TL;DR:** Four prospective experiments taught us that scientific AI is most useful when it attacks a hypothesis. So we built a fixed-scope target diligence review.

Three of our four prospective experiments did not end the way we hoped, and that turned out to be the most useful thing they produced.

We spent the past months testing AI-assisted biological target assessment on ourselves, prospectively, using public data in pulmonary fibrosis and inflammatory bowel disease. We fixed our analysis rules before reading decisive outcomes and kept every negative result. The write-up is our technical report, [Falsification-First AI for Biological Target Assessment](https://radar.firstaimovers.com/falsification-first-ai-biological-target-assessment) (technical report; not peer reviewed). This article explains what we learned and what we are doing about it.

## What the experiments taught us

**Rigor has to earn its complexity.** A heavier scientific-agent architecture did not demonstrate more useful biological coverage than a strong agentic research workflow. It had useful safeguards, but more machinery did not mean more useful biology.

**A small trust layer beat a bigger autonomous scientist.** When we cut the safeguards down to a lean layer, it preserved the useful output, added decision-relevant annotations about provenance, independence and contradictions, and transferred to a new disease area without being tuned to the old one.

**Missing data is a result.** One candidate that survived initial adversarial review was later kept at `NOT_EVALUABLE`, because the causal bridge it depended on could not be measured from available lawful public data. It was not disproven. It just had not earned the next step. [The full case](https://radar.firstaimovers.com/not-evaluable-is-a-result).

**One impressive number is not replication.** We independently challenged an apparent PP4 ≈ 0.992 T-cell signal and did not reproduce it in independent public blood T-cell resources. The discovery cells were gut-resident and the independent cohorts were blood, so this does not prove the original effect false; it shows the signal was single-dataset-only. [The full case](https://radar.firstaimovers.com/pp4-0992-was-not-replication).

## The gap we think this fills

AI is making it cheap to assemble a convincing biological story. It is not making it cheaper to find out whether that story deserves money. If anything, the gap is widening: more plausible hypotheses, written more fluently, arriving faster than anyone can check them.

The people who feel this most are the ones about to commit to an expensive next step: a biotech team choosing which mechanism to take forward, or an investor deciding whether the biology behind an asset holds up. They do not need another literature summary. They need someone to try to break the case, count shared cohorts once, keep the contradicting results in view, and say plainly which causal claim has actually been earned.

## What we are offering

We have packaged the method as the **Biodius Target Challenge**. You send one target, pathway or mechanism, one indication, your current rationale and the decision you are facing. Over five business days we run a falsification-first review: provenance, human-genetics and causal-gene evidence where relevant, cohort independence, contradictions and failed programs, a causal-chain audit, a novelty attack and independent synthetic challenges adjudicated against primary sources. You get a concise decision memo, `ADVANCE`, `REWORK`, `STOP` or `NOT_EVALUABLE`, plus the cheapest evidence that would change it.

The founding pilot is EUR 4,950 excl. VAT, with 3 founding design-partner slots, fixed scope, subject to a decision-sufficient brief and final contracting route. Details are on the [Biodius Target Challenge page](https://radar.firstaimovers.com/biodius-scientific-diligence).

## What it is not

Biodius is experimental scientific diligence tooling. It does not discover drug targets, predict clinical success, provide clinical advice, validate safety or efficacy, perform wet-lab work, or replace qualified scientific, legal, patent or regulatory judgment. It has not been externally validated.

## An honest hypothesis

Our current commercial hypothesis is that this workflow is useful as scientific diligence before a costly downstream decision. We could be wrong about that, and the founding pilots exist to find out. We would rather test the hypothesis on real target decisions than keep generating new biology of our own.

If you have a target or mechanism you would value having independently stress-tested, **send us one target + indication + rationale** at [info@firstaimovers.com](mailto:info@firstaimovers.com?subject=Biodius%20Target%20Challenge). We will tell you whether it deserves the next expensive step. You can also read more [about First AI Movers](https://radar.firstaimovers.com/page/about).

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Why We Built a Service That Tries to Kill Your Biological Target",
  "description": "Four prospective experiments taught us that scientific AI is most useful when it attacks a hypothesis. So we built a fixed-scope target diligence review.",
  "datePublished": "2026-09-22T09:40:32.292381+00:00",
  "dateModified": "2026-09-22T09:40:32.292381+00:00",
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
    "@id": "https://radar.firstaimovers.com/why-we-built-a-service-that-tries-to-kill-your-target"
  },
  "image": "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=1200&h=630&fit=crop&q=80",
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