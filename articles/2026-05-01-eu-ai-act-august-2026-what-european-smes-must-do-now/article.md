---
title: "EU AI Act: What European SMEs Must Do Before August 2, 2026"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/eu-ai-act-august-2026-what-european-smes-must-do-now"
published_date: "2026-05-01"
license: "CC BY 4.0"
---

> **TL;DR:** EU AI Act rules apply from August 2, 2026. European SMEs need a risk classification, compliance checklist, and practical next steps.

The EU AI Act's main application date is August 2, 2026. If your company uses AI in hiring decisions, credit assessments, employee performance scoring, or another Annex III category, you are now inside the compliance window, not looking at it from the outside. Why this matters now: founders, CTOs, operations leaders, and compliance owners need enough time to inventory systems, classify risk, request vendor evidence, and decide whether a tool must be paused before it becomes a regulatory problem.

The EU AI Act (Regulation 2024/1689) entered into force on August 1, 2024. The first enforcement wave, covering prohibited AI practices and AI literacy obligations, applied from February 2, 2025. General-purpose AI model obligations applied from August 2, 2025. The most operationally significant deadline for many small businesses is the one arriving now: **August 2, 2026**, when most remaining AI Act rules apply, including many obligations affecting Annex III high-risk AI systems. The European Commission notes that some high-risk systems embedded in regulated products follow the later August 2, 2027 date, and that Digital Omnibus negotiations may affect implementation timing.

Source basis: the European Commission's [AI Act implementation timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline) and [AI Act FAQ](https://ai-act-service-desk.ec.europa.eu/en/faq) are the reference points for the dates and scope used here.

This is not a theoretical future obligation. National market surveillance authorities will have enforcement power, and penalties for the most serious non-compliance categories can reach up to EUR 35 million or 7% of global annual turnover, whichever is higher.

---

## What Changes on August 2, 2026

Three things matter most for operators:

### 1. High-Risk AI System Requirements (Articles 8-15)

If your company deploys, develops, or procures an AI system that falls under Annex III's high-risk categories, the compliance file should address requirements covering:

- **Risk management**: a documented risk management system for the AI system's lifecycle
- **Data governance**: training data must be relevant, representative, and appropriately checked for bias
- **Technical documentation**: documentation of the system's purpose, capabilities, limitations, and intended use
- **Record-keeping**: logging that enables traceability of relevant operations
- **Transparency**: clear instructions and information for users and deployers
- **Human oversight**: human review capability designed into the system
- **Accuracy, robustness, and cybersecurity**: defined performance and resilience standards

### 2. National Market Surveillance Authorities Go Live

Every EU Member State must designate national competent authorities. These authorities are expected to supervise AI Act compliance and may have the power to:

- Request documentation from deployers and providers
- Conduct audits and inspections
- Order the withdrawal of non-compliant systems from the market
- Issue fines

### 3. Regulatory Sandboxes Must Be Established

Every Member State must establish at least one AI regulatory sandbox under the Act's rollout. These sandboxes are intended to let companies test AI systems under regulatory supervision before full deployment.

---

## Which AI Systems Are High-Risk? (Annex III Categories)

The most relevant Annex III categories for smaller European companies and mid-sized companies:

| Category | What It Covers | SME Example |
|---|---|---|
| **Employment and workers management** | AI used in recruitment, candidate filtering, interview evaluation, promotion decisions, task allocation, performance monitoring, termination decisions | Using AI to screen CVs, score interviews, or monitor employee productivity |
| **Creditworthiness assessment** | AI used to evaluate credit risk for natural persons | Using AI to assess customer payment risk or loan eligibility |
| **Access to essential services** | AI that determines access to or pricing of essential private or public services | Using AI to set insurance premiums or prioritise service requests |
| **Education and vocational training** | AI used to determine access to educational institutions or evaluate students | Using AI to score applications or assess learning outcomes |
| **Law enforcement** | AI used for risk assessment, polygraphing, evidence evaluation | Relevant for security companies or compliance service providers |
| **Safety components** | AI that is a safety component of a product covered by EU harmonisation legislation | AI in manufacturing safety systems, medical devices, machinery. Check the later 2027 timing for many Annex I product cases |

### The Classification Test

Ask these three questions about each AI system your company uses:

1. **Does the system make or materially influence decisions about natural persons?** (hiring, credit, access to services)
2. **Does the system fall under any Annex III category?** (check the table above)
3. **Is the system a component of a product already regulated by EU harmonisation legislation?** (Annex I: machinery, medical devices, toys, etc.)

If the answer to the first two questions is yes, the system may be high-risk under Annex III and should be assessed before the August 2, 2026 application date. If the third question is yes, check whether the later August 2, 2027 timing for regulated product safety components applies.

### What Is NOT High-Risk (Common Relief)

- AI used internally for content generation (marketing copy, blog posts, reports): usually not high-risk
- AI coding assistants (GitHub Copilot, Claude Code): usually not high-risk unless they make decisions about people
- AI used for data analysis and reporting without automated decision-making: usually not high-risk
- AI chatbots for customer service: often limited-risk, with transparency obligations, rather than high-risk
- AI used for process optimisation (logistics, scheduling, inventory): generally not high-risk unless it affects workers' terms or access to essential services

---

## The 90-Day Compliance Checklist for European Companies

### Days 1-30: Assess and Classify

- [ ] **Inventory all AI systems** in use across the organisation, including shadow AI tools employees adopted without IT approval
- [ ] **Classify each system** against Annex III categories using the three-question test above
- [ ] **Identify your role** for each system: are you a provider (you built or trained it), a deployer (you use it in your operations), or a distributor?
- [ ] **Document your assessment**. Even if no systems are high-risk, the documented assessment itself is evidence of due diligence

### Days 30-60: Address High-Risk Systems

If you have high-risk AI systems:

- [ ] **Establish a risk management system**: document the risks, mitigation measures, and monitoring procedures for each high-risk system
- [ ] **Verify data governance**: confirm training data quality, representativeness, and bias assessment for systems you developed or fine-tuned
- [ ] **Prepare technical documentation**: system purpose, capabilities, limitations, intended use, prohibited use, and performance metrics
- [ ] **Implement logging**: ensure the system produces logs that enable traceability of relevant decisions
- [ ] **Design human oversight**: identify who reviews AI decisions, how they can override them, and under what conditions
- [ ] **Conduct a fundamental rights impact assessment**: Article 27 requires this for deployers of high-risk systems in specified cases

### Days 60-90: Operationalise and Verify

- [ ] **Assign a responsible person**: someone in the organisation must own AI Act compliance. This can be your DPO, a dedicated AI compliance officer, or an external advisor
- [ ] **Brief your team**: anyone using or overseeing a high-risk AI system must understand their obligations
- [ ] **Check database registration duties**: Article 49 creates EU database registration duties for certain high-risk AI systems, but the exact obligation depends on your role and system category
- [ ] **Establish an incident reporting procedure**: serious incidents involving high-risk AI systems must be reportable through an internal process
- [ ] **Review vendor contracts**: if you procure high-risk AI systems from vendors, verify that contracts include compliance obligations and documentation access

---

## What Happens If You Do Nothing

### Penalties

| Violation | Maximum Fine |
|---|---|
| Deploying a prohibited AI practice | €35M or 7% of global turnover |
| Non-compliance with high-risk requirements | €15M or 3% of global turnover |
| Providing incorrect information to authorities | €7.5M or 1.5% of global turnover |

For smaller companies and start-ups, the Act requires that administrative fines take account of the smaller undertaking's economic viability. That does not make non-compliance safe: even proportionate fines and remediation orders can be material for a 20-person company.

### Practical Risks Beyond Fines

- National authorities can order you to stop using the system
- Customers and employees can challenge AI-assisted decisions
- Insurance coverage for AI-related incidents may require compliance evidence
- B2B customers (especially enterprises and public sector) will increasingly require AI Act compliance as a procurement condition

---

## What Most Small Businesses Get Wrong

**Mistake 1: "We don't develop AI, so the Act doesn't apply to us."**
Wrong. The Act applies to **deployers** (organisations that use AI systems), not just providers (organisations that develop them). If you use an AI hiring tool from a vendor, you have deployer obligations.

**Mistake 2: "Our AI is just a chatbot, so it's not high-risk."**
Correct in most cases, but if that chatbot makes decisions that affect people's access to services, employment, or credit, it may cross the threshold. Classification is based on function, not technology.

**Mistake 3: "We'll wait and see how enforcement plays out."**
The first market surveillance authorities are being prepared. Waiting for the first enforcement action is waiting for the cautionary tale to be someone else. By then, retroactive compliance is more expensive than proactive compliance.

---

## The SME Advantage

Smaller European businesses actually have an advantage in AI Act compliance: smaller scale means simpler classification. Many founder-led companies and professional services firms will find that:

- They deploy 2-5 AI tools (not hundreds)
- Most of those tools are minimal-risk or limited-risk (transparency obligation only)
- Only 0-2 systems might be high-risk, and those are often vendor-provided tools where the vendor carries the provider obligations

The assessment takes a day. The documentation takes a week. The ongoing compliance monitoring takes an hour a month. This is not the multi-year enterprise programme that larger companies face.

---

## Frequently Asked Questions

### Does the EU AI Act apply to companies with fewer than 50 employees?

Yes. The Act does not have an SME exemption for high-risk system obligations. However, SMEs benefit from reduced fine ceilings, access to regulatory sandboxes, and simplified documentation requirements where proportionality applies.

### Do I need to classify AI tools I use but did not build?

Yes. As a deployer, you must assess whether the AI systems you use fall under high-risk categories and comply with deployer-specific obligations (human oversight, fundamental rights assessment, incident reporting).

### What if my vendor says their AI tool is compliant?

Vendor claims are a starting point, not a compliance strategy. As a deployer, you have independent obligations. Request the vendor's conformity assessment documentation, technical documentation, and EU declaration of conformity. If they cannot provide these for a high-risk system, that is a red flag.

### Can I use the regulatory sandbox to test compliance?

Yes. Regulatory sandboxes are designed for exactly this purpose. Contact your national AI authority to apply. Sandboxes provide a supervised environment to test AI systems against regulatory requirements before full deployment.

### What is the cheapest way for a smaller company to comply?

Start with the inventory and classification (Day 1 of the checklist above). Many companies discover they have zero high-risk systems; in that case, the documented classification itself becomes your compliance evidence. If you do have high-risk systems, prioritise the deployer obligations: human oversight, logging, and incident reporting. An AI readiness assessment can identify gaps in under an hour.

---

## Further Reading

- [The Agentic AI Adoption Framework European SMEs Need in 2026](https://radar.firstaimovers.com/agentic-ai-adoption-framework-european-smes-2026)
- [How to Run an Internal AI Pilot Without Creating Governance Debt](https://radar.firstaimovers.com/how-to-run-internal-ai-pilot-without-governance-debt)
- [What Your AI Acceptable Use Policy Should Actually Cover](https://radar.firstaimovers.com/ai-acceptable-use-policy-engineering-teams)
- [Shadow AI in Engineering Teams: How to Detect It and Decide What to Do](https://radar.firstaimovers.com/shadow-ai-engineering-teams-detect-measure-decide)

---

## Start Your Compliance Assessment Today

If you are unsure whether your AI systems are high-risk, start with our [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment). The governance dimension specifically evaluates your EU AI Act awareness, AI use policy maturity, and incident response readiness.

If you need structured support for classification, documentation, and compliance planning, explore our [Fractional CAIO retainer](https://radar.firstaimovers.com/page/ai-consulting): ongoing governance advisory that includes monthly EU AI Act compliance monitoring.

The remaining window is enough time to classify systems, request vendor evidence, and close obvious gaps. It is not enough time to procrastinate and then comply.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "EU AI Act: What European SMEs Must Do Before August 2, 2026",
  "description": "EU AI Act rules apply from August 2, 2026. European SMEs need a risk classification, compliance checklist, and practical next steps.",
  "datePublished": "2026-05-01T20:21:19.891532+00:00",
  "dateModified": "2026-05-01T20:21:19.891532+00:00",
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
    "@id": "https://radar.firstaimovers.com/eu-ai-act-august-2026-what-european-smes-must-do-now"
  },
  "image": "https://images.unsplash.com/photo-1519677100203-a0e668c92439?w=1200&h=630&fit=crop&q=80",
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
      "name": "Does the EU AI Act apply to companies with fewer than 50 employees?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The Act does not have an SME exemption for high-risk system obligations. However, SMEs benefit from reduced fine ceilings, access to regulatory sandboxes, and simplified documentation requirements where proportionality applies."
      }
    },
    {
      "@type": "Question",
      "name": "Do I need to classify AI tools I use but did not build?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. As a deployer, you must assess whether the AI systems you use fall under high-risk categories and comply with deployer-specific obligations (human oversight, fundamental rights assessment, incident reporting)."
      }
    },
    {
      "@type": "Question",
      "name": "What if my vendor says their AI tool is compliant?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Vendor claims are a starting point, not a compliance strategy. As a deployer, you have independent obligations. Request the vendor's conformity assessment documentation, technical documentation, and EU declaration of conformity. If they cannot provide these for a high-risk system, that is a red f..."
      }
    },
    {
      "@type": "Question",
      "name": "Can I use the regulatory sandbox to test compliance?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Regulatory sandboxes are designed for exactly this purpose. Contact your national AI authority to apply. Sandboxes provide a supervised environment to test AI systems against regulatory requirements before full deployment."
      }
    },
    {
      "@type": "Question",
      "name": "What is the cheapest way for a smaller company to comply?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Start with the inventory and classification (Day 1 of the checklist above). Many companies discover they have zero high-risk systems; in that case, the documented classification itself becomes your compliance evidence. If you do have high-risk systems, prioritise the deployer obligations: human o..."
      }
    }
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "EU AI Act: What European SMEs Must Do Before August 2, 2026",
  "description": "EU AI Act rules apply from August 2, 2026. European SMEs need a risk classification, compliance checklist, and practical next steps.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Does the system make or materially influence decisions about natural persons?",
      "text": "(hiring, credit, access to services)"
    },
    {
      "@type": "HowToStep",
      "name": "Does the system fall under any Annex III category?",
      "text": "(check the table above)"
    },
    {
      "@type": "HowToStep",
      "name": "Is the system a component of a product already regulated by EU harmonisation legislation?",
      "text": "(Annex I: machinery, medical devices, toys, etc.)"
    }
  ]
}
</script>
-->