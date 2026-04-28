---
title: "EU AI Act High-Risk Systems Assessment: A Self-Assessment Guide for European SMEs"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/eu-ai-act-high-risk-systems-assessment-european-smes-2026"
published_date: "2026-04-24"
license: "CC BY 4.0"
---
> **TL;DR:** EU AI Act Annex III self-assessment guide. Sector-by-sector high-risk checklist for European SMEs with 10 to 50 employees.

Why this matters: the EU AI Act enforcement calendar is moving faster than most SME compliance teams realise. General-purpose AI system obligations take effect in August 2026. Annex III high-risk system obligations under Article 16 are already in force for market-ready systems and will require active compliance documentation from deployers by August 2026. If your company uses AI in recruitment, credit assessment, employee monitoring, medical triage, or public service delivery, you may already be deploying a high-risk system under Annex III without having formally classified it.

This guide gives you a sector-by-sector self-assessment you can complete in an afternoon. It does not replace legal advice, but it will tell you whether you need it urgently.

---

## What Makes a System High-Risk Under Annex III

Annex III of the EU AI Act lists eight categories of high-risk AI systems. Two criteria must both be true for an obligation to apply: (1) the AI system falls within one of the eight categories, and (2) the system is a standalone AI system that makes or substantially contributes to a decision affecting an individual's legal rights, economic situation, or physical safety.

The eight Annex III categories are:

1. Biometric identification and categorisation of natural persons
2. Management and operation of critical infrastructure (energy, water, transport, digital)
3. Education and vocational training (access, assessment, evaluation)
4. Employment and workers management (recruitment, task allocation, performance monitoring, termination)
5. Access to essential private services and benefits (credit, housing, insurance)
6. Law enforcement (risk assessment, evidence evaluation, predictive policing)
7. Migration, asylum, and border control management
8. Administration of justice and democratic processes

For most European SMEs with 10 to 50 employees, categories 4, 5, and 3 are the most likely to apply.

---

## Sector-by-Sector Self-Assessment

**Professional Services and Tech SMEs (20 to 50 employees)**

The most common trigger in this sector is recruitment AI: ATS systems with AI scoring, CV screening tools, or interview analysis software. If your company uses any AI system to rank, score, or filter job candidates, you are likely operating a Category 4 Annex III system.

Questions to answer:
- Does your ATS or HR platform use AI to score or rank candidates? (Most modern platforms do, by default.)
- Does a human review every application individually, or does the AI filter determine which applications a human sees?
- Is the AI output used as a recommendation (human decides) or as a gate (AI determines eligibility for the next stage)?

If the AI determines eligibility for the next stage without mandatory individual human review, you are deploying a high-risk system. Category 4 obligations require a conformity assessment, an AI system risk management file, transparency to affected individuals, human oversight provisions, and incident logging.

**Fintech and Insurance SMEs**

Category 5 (access to essential private services) is the primary trigger. Credit scoring, insurance risk assessment, loan approval, and fraud detection systems that make or substantially influence decisions on individual access to financial services are Category 5 systems.

The distinction that matters for SMEs: "substantially influence" is a lower bar than "decides." If your AI output is the primary input to a credit officer's decision, the system may be classified as high-risk even if a human formally makes the final call.

Questions to answer:
- Does your system assign a risk score, creditworthiness rating, or insurance premium calculation to an individual?
- Is that score the primary basis for a decision about product access or pricing?
- Do individuals have any right to explanation or appeal of that score?

If the score drives the decision and affected individuals have no meaningful explanation right, you have a Category 5 high-risk obligation plus a GDPR Article 22 automated decision-making obligation running in parallel.

**Healthcare and MedTech SMEs**

Category 2 (critical infrastructure) may apply for health data infrastructure providers. More commonly, SMEs in this sector are deployers of AI systems that triage patients, flag clinical risk, or support diagnostic decisions. These may be Category 1 (biometric data use) or Category 3 (access to health services) depending on the specific function.

The Medical Device Regulation (MDR) classification interacts with the EU AI Act here: an AI system that qualifies as a medical device under MDR is subject to a conformity assessment under MDR, which the EU AI Act treats as satisfying the Annex III conformity assessment requirement if the MDR assessment already covered the AI-specific requirements. This exemption is narrow and requires confirmation that your MDR assessment specifically addressed the AI Act criteria.

Questions to answer:
- Is the AI system used to make or assist clinical decisions that affect individual patient care?
- Does the system process biometric data (images, voice, physiological signals) to identify or categorise individuals?
- Is the system classified as a medical device under MDR 2017/745?

**Education and Training SMEs**

Category 3 applies to AI systems used for student assessment, admission scoring, or evaluation of training programme outcomes. EdTech companies and corporate training providers using AI to assess learner performance or recommend progression paths are Category 3 deployers.

The key question: does the AI output affect an individual's access to educational progression or professional certification? If a learner can fail a module or be denied certification based on AI assessment without meaningful human review, this is a high-risk deployment.

---

## The Deployer Obligation Checklist (Annex III)

If your self-assessment identifies a high-risk system, these are the obligations your company carries as a deployer under Article 16:

1. **Conformity documentation**: Obtain the EU Declaration of Conformity from your AI provider. If the provider cannot supply it, you cannot legally deploy the system for high-risk use cases.
2. **Human oversight**: Implement documented oversight procedures. "Human in the loop" must be operationally real, not a checkbox.
3. **Transparency to affected individuals**: Inform individuals when AI is making or substantially contributing to a decision about them. The notice must be meaningful.
4. **Incident logging**: Log all incidents where the system performed unexpectedly or caused harm. Keep records for minimum 3 years.
5. **Fundamental rights impact assessment (FRIA)**: Required for public-authority deployers and private deployers of high-risk systems that affect access to essential services.
6. **Register in the EU database**: High-risk AI systems used by private entities in certain categories must be registered in the EU AI Act public database (timeline: phased by category from 2026).

---

## When to Escalate to Legal Counsel

This self-assessment identifies whether escalation is needed, not whether compliance is achieved. Escalate immediately if any of the following is true:

- You identified a Category 4, 5, or 3 system that is already in production
- Your AI provider cannot supply a Declaration of Conformity for a system you have classified as high-risk
- You are using AI from a provider that does not yet have a published EU AI Act compliance roadmap
- Your system processes special categories of data (health, biometric, religious belief, political opinion) in combination with AI decision-making

---

## FAQ

**We use an ATS with AI features. Does that automatically make us a high-risk deployer?**
Not automatically. The question is whether the AI output gates candidate progression (high-risk) or assists human decision-making without gatekeeping it (lower-risk). Most modern ATS platforms with AI scoring do gate progression in default configurations. Check your ATS settings explicitly rather than assuming the safe default.

**Our AI vendor says their system is compliant. Is that enough?**
Vendor compliance covers provider obligations under Article 13. Your obligations as a deployer under Article 16 are separate and cannot be delegated to your vendor. Vendor compliance is a necessary but not sufficient condition for your deployment to be compliant.

**What is the penalty for deploying an unregistered high-risk system?**
Penalties under the EU AI Act for prohibited AI violations reach EUR 35 million or 7 percent of global annual turnover (whichever is higher). Violations of Annex III obligations carry up to EUR 15 million or 3 percent of global annual turnover. National market surveillance authorities are responsible for enforcement; enforcement intensity will vary by member state.

**We are a small company with 12 employees. Do these rules really apply to us?**
Yes. The EU AI Act has no SME exemption for high-risk system deployment. SMEs that deploy high-risk AI systems carry the same legal obligations as large enterprises. The Act does include a recital encouraging national authorities to consider proportionality when applying penalties, but this is advisory guidance for enforcement, not an exemption from the rules.

---

## Further Reading

- [EU AI Act General-Purpose Systems August 2026 Compliance Checklist](https://radar.firstaimovers.com/eu-ai-act-gp-systems-august-2026-compliance-checklist)
- [EU AI Act August 2026 Deadline Action Plan for SMEs](https://radar.firstaimovers.com/eu-ai-act-august-2026-deadline-action-plan-smes)
- [Shadow AI Detection and Governance for European SMEs](https://radar.firstaimovers.com/shadow-ai-detection-governance-european-smes-2026)

Need help determining whether your AI systems trigger Annex III obligations? [Talk to an AI consultant](https://radar.firstaimovers.com/page/ai-consulting) who specialises in EU AI Act compliance for European SMEs.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "EU AI Act High-Risk Systems Assessment: A Self-Assessment Guide for European SMEs",
  "description": "EU AI Act Annex III self-assessment guide. Sector-by-sector high-risk checklist for European SMEs with 10 to 50 employees.",
  "datePublished": "2026-04-24T04:19:10.501361+00:00",
  "dateModified": "2026-04-24T04:19:10.501361+00:00",
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
    "@id": "https://radar.firstaimovers.com/eu-ai-act-high-risk-systems-assessment-european-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1573164713714-d95e436ab8d6?w=1200&h=630&fit=crop&q=80",
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
  "name": "EU AI Act High-Risk Systems Assessment: A Self-Assessment Guide for European SMEs",
  "description": "EU AI Act Annex III self-assessment guide. Sector-by-sector high-risk checklist for European SMEs with 10 to 50 employees.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Conformity documentation",
      "text": "Obtain the EU Declaration of Conformity from your AI provider. If the provider cannot supply it, you cannot legally deploy the system for high-risk use cases."
    },
    {
      "@type": "HowToStep",
      "name": "Human oversight",
      "text": "Implement documented oversight procedures. "Human in the loop" must be operationally real, not a checkbox."
    },
    {
      "@type": "HowToStep",
      "name": "Transparency to affected individuals",
      "text": "Inform individuals when AI is making or substantially contributing to a decision about them. The notice must be meaningful."
    },
    {
      "@type": "HowToStep",
      "name": "Incident logging",
      "text": "Log all incidents where the system performed unexpectedly or caused harm. Keep records for minimum 3 years."
    },
    {
      "@type": "HowToStep",
      "name": "Fundamental rights impact assessment (FRIA)",
      "text": "Required for public-authority deployers and private deployers of high-risk systems that affect access to essential services."
    },
    {
      "@type": "HowToStep",
      "name": "Register in the EU database",
      "text": "High-risk AI systems used by private entities in certain categories must be registered in the EU AI Act public database (timeline: phased by category from 2026)."
    }
  ]
}
</script>
-->

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/eu-ai-act-high-risk-systems-assessment-european-smes-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*