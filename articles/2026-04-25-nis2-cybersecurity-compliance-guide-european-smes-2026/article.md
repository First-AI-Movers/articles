---
title: "NIS2 Compliance Guide for European SMEs in 2026"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/nis2-cybersecurity-compliance-guide-european-smes-2026"
published_date: "2026-04-25"
license: "CC BY 4.0"
---
> **TL;DR:** NIS2 is live and EU SMEs in covered sectors face new mandatory cybersecurity obligations. Learn who is in scope and what the five starting steps are.

The NIS2 Directive (Directive 2022/2555/EU) became effective across EU member states in October 2024. Why this matters: NIS2 significantly expanded the scope of the original NIS Directive, bringing thousands of mid-sized European companies under mandatory cybersecurity obligations for the first time. A 30-person software company in Bucharest or a 45-person logistics firm in Bratislava may now be a covered "important entity" without realising it.

This guide explains who is in scope, what NIS2 requires, and what a growing EU SME should do in 2026 to build a defensible compliance posture.

---

## Who NIS2 Covers

NIS2 divides covered organisations into two categories:

**Essential entities**: Large organisations in critical sectors (energy, transport, banking, financial market infrastructure, health, drinking water, waste water, digital infrastructure, ICT service management, public administration, space). Size threshold: generally 250+ employees or annual turnover above EUR 50 million.

**Important entities**: Mid-sized organisations in a broader set of sectors, including postal services, waste management, chemicals, food production, manufacturing of medical devices, computers and electronics, machinery, and motor vehicles. Also includes digital providers (online marketplaces, online search engines, cloud services) and certain research organisations.

**The practical threshold for SMEs**: Important entities are generally organisations with 50-249 employees or annual turnover of EUR 10-49 million. If your company meets the size threshold AND operates in one of the 18 covered sectors, you are likely subject to NIS2 as an important entity.

**Exceptions**: Micro enterprises (fewer than 10 employees, annual turnover under EUR 2 million) are generally excluded from NIS2 scope regardless of sector. Very small SMEs below this threshold are not covered.

---

## What NIS2 Requires

For important entities, NIS2 Article 21 mandates a set of cybersecurity risk management measures. These are not optional guidance: they are legal obligations that national competent authorities (NCAs) can enforce with administrative fines of up to EUR 7 million or 1.4% of global annual turnover for important entities.

**The 10 mandatory cybersecurity measures** under NIS2 Article 21(2):

1. **Risk analysis and information system security policies**: A documented information security policy and a process for identifying and managing cybersecurity risks.

1. **Incident handling**: Procedures for detecting, managing, and recovering from cybersecurity incidents. This includes designated incident response roles.

1. **Business continuity**: Backup management, disaster recovery, and crisis management procedures.

1. **Supply chain security**: Policies for assessing cybersecurity risks from suppliers and third-party service providers. This is particularly relevant if you use cloud providers or SaaS tools in your operations.

1. **Security in network and information systems acquisition, development, and maintenance**: Secure development practices and vulnerability handling procedures.

1. **Policies and procedures for assessing effectiveness of cybersecurity risk management measures**: Regular security testing, including penetration testing where appropriate.

1. **Basic cyber hygiene practices and cybersecurity training**: Staff training, phishing awareness, and foundational security hygiene (patch management, access controls, MFA).

1. **Policies and procedures regarding the use of cryptography and encryption**: Documented encryption standards for data at rest and in transit.

1. **Human resources security, access control policies, and asset management**: Clear processes for onboarding/offboarding access, privileged access management, and asset inventory.

1. **Use of multi-factor authentication, continuous authentication solutions, or emergency communication systems**: MFA is mandatory for access to critical systems and remote access.

---

## The Incident Reporting Timeline

NIS2 introduces strict incident reporting timelines that are shorter than most organisations expect:

- **24 hours**: Initial early warning notification to the national competent authority (NCA) after becoming aware of a significant incident.
- **72 hours**: Incident notification with an initial assessment of the severity and impact.
- **1 month**: Final incident report with a detailed description, root cause analysis, and measures taken.

A "significant incident" under NIS2 is one that has caused or can cause severe operational disruption, financial loss, or material or non-material damage to other natural or legal persons. This is a broad definition: a ransomware attack affecting your production systems, a data breach affecting customer data, or a supply chain compromise affecting your software delivery pipeline would all qualify.

**Who to report to**: Each EU member state designated a national competent authority for NIS2. In Romania, this is DNSC (Directoratul National de Securitate Cibernetica). In Slovakia, it is NBU (Narodny bezpecnostny urad). In the Netherlands, it is NCSC-NL under the Digital Trust Center. In France, it is ANSSI.

---

## The Intersection with GDPR and EU AI Act

NIS2 and GDPR operate in parallel. A cybersecurity incident that also involves personal data creates dual reporting obligations: NIS2 to the NCA (24-hour early warning) and GDPR to the supervisory authority (72 hours under GDPR Article 33). The timelines overlap but the recipients and content differ. Organisations that have already built GDPR incident response processes have a head start on NIS2 incident reporting.

**AI systems and NIS2**: If your organisation deploys AI tools in network or information systems covered by NIS2, those tools are within scope for the cybersecurity risk management requirements. An AI-powered customer service chatbot that runs on your production network is a system asset that must be included in your risk analysis and supply chain security assessment. The EU AI Act and NIS2 overlap most directly in: (a) supply chain security for AI vendors, (b) incident handling when an AI system fails or is compromised, and (c) access control for AI system administration.

---

## Practical Starting Point for EU SMEs in Scope

If you have determined that your organisation is an important entity under NIS2, the practical starting point is a gap analysis against the 10 Article 21 measures:

**Step 1: Scope your covered systems.** Identify which of your IT systems are "network and information systems" in scope for NIS2. For most tech SMEs, this includes your core production environment, customer-facing services, and employee systems.

**Step 2: Assign a NIS2 owner.** NIS2 Article 20 requires that management bodies (boards, senior executives) approve cybersecurity risk management measures and are personally accountable for compliance. Designate a senior owner: CTO, CISO, or a fractional security lead.

**Step 3: Document existing controls.** Audit what you already have (MFA, patch management, backup procedures, security training) against the 10 Article 21 requirements. Most growing EU tech companies will find they have 5-6 of the 10 requirements partially met.

**Step 4: Register with your NCA.** NIS2 requires important entities to register with their national competent authority. Registration deadlines vary by member state (many set deadlines in 2024-2025). Check your country's NCA for the current registration portal.

**Step 5: Build incident response procedures.** The 24-hour early warning requirement is the hardest part of NIS2 for most SMEs: you need to know something has happened before you can report it. Implement centralised log monitoring, alerting thresholds, and a clear escalation path from technical team to the executive who will send the NCA notification.

---

## FAQ

### Is my company in scope for NIS2 if we serve enterprise clients but are only 45 employees?
Size threshold is only one criterion. Sector also determines scope. A 45-person cybersecurity software company that provides managed security services to other organisations is likely in scope as an "important entity" in the digital providers sector, regardless of being under 50 employees. Check both the size threshold AND the sector classification before concluding you are out of scope.

### What are the NIS2 fines for important entities?
For important entities, NIS2 provides for administrative fines of up to EUR 7 million or 1.4% of total annual worldwide turnover, whichever is higher. Member states may set higher national fines. The Dutch NCA (Digital Trust Center under NCSC-NL) and the French ANSSI have both signalled active enforcement postures in 2025-2026.

### Do we need to hire a cybersecurity specialist to comply with NIS2?
Not necessarily a full-time hire. NIS2 does not mandate an in-house CISO. A fractional security lead or a managed security service provider (MSSP) can satisfy the governance requirements if they are formally engaged and have documented scope. The Article 20 management accountability requirement does mean your leadership team cannot fully delegate responsibility: a board member or C-level executive must be personally accountable for approving your cybersecurity risk management policy.

### How does NIS2 relate to ISO 27001?
ISO 27001 is not required by NIS2, but an organisation with a current ISO 27001 certification will find significant overlap with NIS2 Article 21 requirements. The ISO 27001 Annex A controls cover most of the 10 NIS2 measures. If you are considering both ISO 27001 and NIS2 compliance, pursue them together: the audit and documentation effort is highly overlapping.

---

## Further Reading

- [AI Security Fundamentals for European SMEs](https://radar.firstaimovers.com/ai-security-fundamentals-european-smes-2026)
- [EU AI Act August 2026 Deadline Action Plan for SMEs](https://radar.firstaimovers.com/eu-ai-act-august-2026-deadline-action-plan-smes)
- [AI Data Governance Framework for European SMEs](https://radar.firstaimovers.com/ai-data-governance-framework-european-smes-2026)
- [Should You Adopt AI in EU Regulated Manufacturing?](https://radar.firstaimovers.com/should-you-adopt-ai-in-regulated-manufacturing-2026)
- [AI Governance Framework for European SMEs](https://radar.firstaimovers.com/ai-governance-framework-european-sme-2026)

Unsure whether your EU SME is in scope for NIS2 or how AI tools intersect with your cybersecurity obligations? [Start with our AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment).

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "NIS2 Compliance Guide for European SMEs in 2026",
  "description": "NIS2 is live and EU SMEs in covered sectors face new mandatory cybersecurity obligations. Learn who is in scope and what the five starting steps are.",
  "datePublished": "2026-04-25T04:18:16.854127+00:00",
  "dateModified": "2026-04-25T04:18:16.854127+00:00",
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
    "@id": "https://radar.firstaimovers.com/nis2-cybersecurity-compliance-guide-european-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&h=630&fit=crop&q=80",
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
      "name": "Is my company in scope for NIS2 if we serve enterprise clients but are only 45 employees?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Size threshold is only one criterion. Sector also determines scope. A 45-person cybersecurity software company that provides managed security services to other organisations is likely in scope as an "important entity" in the digital providers sector, regardless of being under 50 employees. Check ..."
      }
    },
    {
      "@type": "Question",
      "name": "What are the NIS2 fines for important entities?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For important entities, NIS2 provides for administrative fines of up to EUR 7 million or 1.4% of total annual worldwide turnover, whichever is higher. Member states may set higher national fines. The Dutch NCA (Digital Trust Center under NCSC-NL) and the French ANSSI have both signalled active en..."
      }
    },
    {
      "@type": "Question",
      "name": "Do we need to hire a cybersecurity specialist to comply with NIS2?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Not necessarily a full-time hire. NIS2 does not mandate an in-house CISO. A fractional security lead or a managed security service provider (MSSP) can satisfy the governance requirements if they are formally engaged and have documented scope. The Article 20 management accountability requirement d..."
      }
    },
    {
      "@type": "Question",
      "name": "How does NIS2 relate to ISO 27001?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "ISO 27001 is not required by NIS2, but an organisation with a current ISO 27001 certification will find significant overlap with NIS2 Article 21 requirements. The ISO 27001 Annex A controls cover most of the 10 NIS2 measures. If you are considering both ISO 27001 and NIS2 compliance, pursue them ..."
      }
    }
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "NIS2 Compliance Guide for European SMEs in 2026",
  "description": "NIS2 is live and EU SMEs in covered sectors face new mandatory cybersecurity obligations. Learn who is in scope and what the five starting steps are.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Risk analysis and information system security policies",
      "text": "A documented information security policy and a process for identifying and managing cybersecurity risks."
    },
    {
      "@type": "HowToStep",
      "name": "Incident handling",
      "text": "Procedures for detecting, managing, and recovering from cybersecurity incidents. This includes designated incident response roles."
    },
    {
      "@type": "HowToStep",
      "name": "Business continuity",
      "text": "Backup management, disaster recovery, and crisis management procedures."
    },
    {
      "@type": "HowToStep",
      "name": "Supply chain security",
      "text": "Policies for assessing cybersecurity risks from suppliers and third-party service providers. This is particularly relevant if you use cloud providers or SaaS tools in your operations."
    },
    {
      "@type": "HowToStep",
      "name": "Security in network and information systems acquisition, development, and maintenance",
      "text": "Secure development practices and vulnerability handling procedures."
    },
    {
      "@type": "HowToStep",
      "name": "Policies and procedures for assessing effectiveness of cybersecurity risk management measures",
      "text": "Regular security testing, including penetration testing where appropriate."
    },
    {
      "@type": "HowToStep",
      "name": "Basic cyber hygiene practices and cybersecurity training",
      "text": "Staff training, phishing awareness, and foundational security hygiene (patch management, access controls, MFA)."
    },
    {
      "@type": "HowToStep",
      "name": "Policies and procedures regarding the use of cryptography and encryption",
      "text": "Documented encryption standards for data at rest and in transit."
    },
    {
      "@type": "HowToStep",
      "name": "Human resources security, access control policies, and asset management",
      "text": "Clear processes for onboarding/offboarding access, privileged access management, and asset inventory."
    },
    {
      "@type": "HowToStep",
      "name": "Use of multi-factor authentication, continuous authentication solutions, or emergency communication systems",
      "text": "MFA is mandatory for access to critical systems and remote access."
    }
  ]
}
</script>
-->

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/nis2-cybersecurity-compliance-guide-european-smes-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*