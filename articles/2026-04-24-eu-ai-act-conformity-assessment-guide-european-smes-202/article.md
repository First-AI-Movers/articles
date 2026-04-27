---
title: "EU AI Act Conformity Assessment: A Practical Guide for European SMEs"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/eu-ai-act-conformity-assessment-guide-european-smes-2026"
published_date: "2026-04-24"
license: "CC BY 4.0"
---
> **TL;DR:** Step-by-step conformity assessment for EU SMEs deploying Annex III high-risk AI. Covers deployer vs provider split, documentation, and oversight.

Getting the EU AI Act conformity assessment right depends on one distinction: are you the organisation that built and placed the AI system on the market, or the organisation using it in your own operations? Why this matters: a 25-person Czech HR-tech firm that builds a CV screening tool and sells it to clients carries the full assessment burden. That means technical documentation, a quality management system, a Declaration of Conformity, and CE marking. A 40-person Dutch logistics company that licenses that same tool is a deployer with substantially lighter obligations. Getting that classification right determines whether your compliance project takes two weeks or six months.

This guide walks compliance officers, technical teams, and operations leaders at growing SaaS companies and mid-sized software companies through the four-step conformity procedure for deployers, the full documentation set required from providers, and the specific distinctions that determine which path applies to your organisation.

---

## When Conformity Assessment Is Required

Conformity assessment is only required for Annex III high-risk AI systems. Not every AI tool a professional services firm or growing SaaS company uses qualifies. The EU AI Act defines eight categories of high-risk systems in Annex III, covering areas including biometric identification, critical infrastructure management, education and training, employment decisions, essential services access, law enforcement, migration and border control, and justice administration.

If your AI system does not fall into one of those categories, conformity assessment is not required. You may still have transparency obligations under Article 50 and GDPR data governance obligations, but the full Annex III compliance stack does not apply.

If your system does fall into Annex III, the next question is whether you are a provider or a deployer. The regulation treats these roles differently.

**Provider:** an organisation that develops an AI system, or has one developed, and places it on the market under its own name or brand. Placing on the market means making the system available to other parties.

**Deployer:** an organisation that uses an AI system in the course of its professional activities. Deployers do not place the system on the market. They put it into service within their own organisation.

The conformity path for a provider is significantly more demanding than for a deployer.

---

## The Deployer Obligations: Article 25 in Practice

Most SMEs that use third-party AI tools for recruitment screening, credit assessment, or other Annex III use cases are deployers. The obligations under Article 25 are proportionate to that role.

As a deployer of a high-risk AI system, your compliance team is responsible for four things.

**Follow the provider's instructions for use.** The provider is required to supply technical documentation and instructions describing the intended purpose, the conditions under which the system may be safely deployed, and any human oversight requirements. Deploying outside the intended purpose transfers provider-level liability to you.

**Implement Article 14 human oversight.** Article 14 requires deployers to assign oversight to natural persons with the necessary competence, training, and authority to understand the system's output, identify anomalies, and intervene or override when needed. The oversight must be structurally possible: the system cannot be designed in a way that prevents human intervention.

**Monitor for substantial modifications.** If the system is updated in a way that changes its intended purpose or risk profile, the conformity assessment may need to be repeated. As a deployer, you are responsible for flagging material changes to your provider.

**Register in the EU database when required.** Deployers of certain high-risk systems, particularly in public authority contexts, must register their use in the EU's public AI database. For most private-sector SMEs, this obligation applies primarily to providers rather than deployers.

---

## The Provider Obligations: Article 17 and the Full Conformity Stack

If your organisation is building an AI system that will be placed on the market, or if your operations team has commissioned a bespoke system that will be commercialised, you are a provider and the full Annex III obligations apply.

The core requirement is a quality management system (QMS) under Article 17 that covers the entire lifecycle of the AI system. The QMS must document your risk management process, your data governance practices, your validation and testing methodology, your post-market monitoring plan, and your procedures for handling incidents and non-conformities.

Beyond the QMS, providers must produce a technical documentation set, conduct a conformity assessment (self-assessment is permitted for most Annex III categories; third-party assessment by a notified body is required for biometric identification and a small number of other categories), draw up an EU Declaration of Conformity, and affix CE marking to the system before placing it on the market.

For a mid-sized software company building in a regulated AI domain, this is a substantial undertaking. The conformity assessment alone typically requires input from legal, technical, and data teams, plus external review if you are targeting regulated sectors like financial services or healthcare.

---

## The Four-Step Deployer Conformity Procedure

For most SMEs, the relevant procedure is the deployer path. Here is a structured approach.

**Step 1: Classify the system.** Confirm that the AI system you are deploying genuinely falls within Annex III. Review the specific category it might fall under and check whether any of the Article 6 exclusions apply. An AI system used for a clearly ancillary function (generating internal reports, summarising meeting notes) is unlikely to qualify as high-risk even if it touches a regulated domain. Document your classification reasoning.

**Step 2: Obtain the provider's technical documentation and Declaration of Conformity.** Before deploying any Annex III system, request the provider's technical documentation package and their EU Declaration of Conformity. The DoC is the provider's formal statement that the system meets the requirements of the EU AI Act. If the provider cannot produce these documents, they are not in compliance with their own provider obligations, and you should not deploy their system in an Annex III context.

**Step 3: Implement Article 14 human oversight measures.** Based on the provider's instructions for use, design and document your human oversight process. Specify who in your operations team is responsible for oversight, what training they have received, how they can intervene in or override the system, and how decisions influenced by the AI are reviewed and recorded.

**Step 4: Document your operational procedures.** Produce a deployment record covering: the system classification, the provider's documentation obtained, your oversight process, any configuration decisions made, and your procedure for monitoring and reporting incidents. This document does not need to be elaborate for most SMEs, but it must exist and must be kept current as the system evolves.

---

## Technical Documentation: The Minimum Set

The minimum technical documentation set for an Annex III system covers six areas.

**System description.** What the system does, how it works at a functional level, and what its intended purpose is. This includes the AI approach used, the inputs and outputs, and the deployment context.

**Intended purpose statement.** A precise statement of the use case the system was designed and validated for. Deploying outside the intended purpose is a compliance risk for the deployer and a liability risk for the provider.

**Risk management process.** How the provider has identified, assessed, and mitigated risks associated with the system, including risks of error, bias, and misuse.

**Data governance documentation.** The datasets used to train and validate the system, the data quality measures applied, and any known limitations or biases in the training data.

**Accuracy, robustness, and cybersecurity metrics.** Quantitative performance benchmarks for the system, including accuracy on validation sets and the security measures protecting the system from manipulation.

**Post-market monitoring plan.** How the provider will monitor the system's performance after deployment, what metrics they track, and how they will communicate updates or identified issues to deployers.

As a deployer, you should receive all six components from your provider before going live.

---

## FAQ

**Does the EU AI Act conformity assessment apply to AI tools we use internally, not just products we sell?**
Yes, if the internal use falls within an Annex III category. Deploying a high-risk AI system internally, for example using an AI tool to evaluate employee performance, triggers deployer obligations under Article 25 even though you are not placing a product on the market.

**We are a growing SaaS company that offers an AI feature as part of a broader platform. Are we a provider?**
Almost certainly yes, for the AI feature component. If you are making that feature available to customers, you are placing an AI system on the market. If the feature performs an Annex III function for your customers, the full provider obligations apply to that feature regardless of whether it is embedded in a broader non-AI product.

**Can we rely on our vendor's CE marking as evidence of our own compliance?**
The CE marking demonstrates that the provider has completed the required conformity assessment. As a deployer, you can reference it as evidence that the system you are deploying has been assessed. However, it does not cover your deployer obligations. Your Article 14 human oversight implementation and your operational deployment documentation remain your responsibility.

**What happens if we modify a third-party high-risk AI system we have deployed?**
Substantial modification of a high-risk AI system can reclassify the organisation making the modification as the provider for that modified version. The EU AI Act defines substantial modification to include changes that affect the system's intended purpose, its performance metrics, or its risk profile. If your technical team makes changes of that scope to a licensed system, seek legal advice before deploying the modified version.

---

## Further Reading

- [EU AI Act High-Risk Systems: What EU SMEs Need to Assess](https://radar.firstaimovers.com/eu-ai-act-high-risk-systems-assessment-european-smes-2026)
- [EU AI Act General-Purpose AI Systems: August 2026 Compliance Checklist](https://radar.firstaimovers.com/eu-ai-act-gp-systems-august-2026-compliance-checklist)
- [AI Governance Framework for European SMEs](https://radar.firstaimovers.com/ai-governance-framework-european-sme-2026)

If you are working through Annex III classification and conformity planning for the first time, the [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) provides a structured baseline before you engage legal counsel or begin documentation.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "EU AI Act Conformity Assessment: A Practical Guide for European SMEs",
  "description": "Step-by-step conformity assessment for EU SMEs deploying Annex III high-risk AI. Covers deployer vs provider split, documentation, and oversight.",
  "datePublished": "2026-04-24T10:32:37.598341+00:00",
  "dateModified": "2026-04-24T10:32:37.598341+00:00",
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
    "@id": "https://radar.firstaimovers.com/eu-ai-act-conformity-assessment-guide-european-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=630&fit=crop&q=80",
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

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/eu-ai-act-conformity-assessment-guide-european-smes-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*