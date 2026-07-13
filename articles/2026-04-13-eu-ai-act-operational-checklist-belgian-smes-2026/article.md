---
title: "EU AI Act Compliance for Belgian SMEs: A 12-Step Operational Checklist"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/eu-ai-act-operational-checklist-belgian-smes-2026"
published_date: "2026-04-13"
license: "CC BY 4.0"
---

> **TL;DR:** A practical 12-step EU AI Act compliance checklist for Belgian SMEs, mapped to Belgian authorities: DPA, FSMA, SPF Économie, and bilingual documentation r…

The EU AI Act is no longer a future concern. Enforcement of obligations for deployers of high-risk AI systems is active in 2026, and Belgian SMEs face a compliance picture that is measurably more complex than the one facing their neighbours. The reason is structural: Belgium's institutional architecture — split between federal authorities, regional bodies, and sector regulators — creates overlapping jurisdictions that do not exist in single-language, unitary-state markets. Add the bilingual and trilingual documentation requirements for regulated AI outputs, and the compliance task for a Belgian SME in financial services or professional services becomes substantially heavier than the generic EU guidance suggests.

This checklist is designed to be operational, not theoretical. Each of the twelve steps is actionable by a COO, compliance officer, or CTO without a legal team. Each step is mapped to the Belgian authority responsible, so you know who you are accountable to — not just what you need to do.

---

## Who This Applies To

The EU AI Act distinguishes between providers (companies that develop AI systems) and deployers (companies that use AI systems in their operations). Most Belgian SMEs are deployers. If your company uses an AI system that falls within a high-risk category — recruitment and HR management, creditworthiness assessment, AI used in critical infrastructure, systems that affect access to essential services — you have active compliance obligations now.

If you use only general-purpose AI tools such as productivity assistants, drafting tools, or internal search, your obligations are lighter but not zero. Transparency requirements, staff information obligations, and GDPR alignment apply regardless of risk category.

If you are uncertain whether your AI systems are high-risk, Step 1 of this checklist resolves that question.

---

## Phase 1: Inventory and Classify

### Step 1 — Build a complete AI system inventory

List every AI system your company uses or has deployed, including third-party SaaS tools with AI features. For each system, record: the vendor name and version, the business function it supports, whether it makes or informs decisions about individuals, and whether it was procured with explicit AI disclosure.

Many Belgian SMEs discover at this step that they are using AI systems they did not formally evaluate — embedded features in HR platforms, credit scoring integrations in accounting tools, or AI-assisted document review in legal workflows. Discovery precedes classification.

**Responsible authority:** Internal governance. No external filing required at this stage.

### Step 2 — Apply the EU AI Act risk classification

For each system on your inventory, apply the four-tier classification: unacceptable risk (prohibited), high-risk (Annex III), limited risk (transparency obligations), minimal risk (no mandatory obligations).

The Annex III high-risk categories most relevant to Belgian SMEs include: AI systems used in employment and worker management (scheduling, performance evaluation, candidate screening), AI systems used in access to financial services (credit scoring, insurance underwriting), and AI systems used in education and vocational training. If your company operates in financial services, the FSMA layer applies on top of the EU AI Act baseline — see Step 8.

**Responsible authority:** Classification is self-assessment. For disputed classifications, the Belgian national competent authority under the EU AI Act will be designated by SPF Économie / FOD Economie.

### Step 3 — Map data flows for each high-risk system

For every system classified as high-risk, document the data flow: what personal data enters the system, where it is processed, where outputs go, and how outputs are used in decisions. This step integrates your EU AI Act obligations with your GDPR record of processing activities under Article 30. Belgian SMEs that have maintained clean GDPR documentation will find this step substantially faster.

**Responsible authority:** Belgian DPA (Autorité de protection des données / Gegevensbeschermingsautoriteit) retains jurisdiction over the personal data processing dimensions of this step.

---

## Phase 2: Governance and Documentation

### Step 4 — Designate an AI governance owner

Assign a named individual — not a committee — as accountable for AI Act compliance. In a Belgian SME of ten to fifty employees, this is typically the COO or CTO. Their responsibilities include maintaining the AI system inventory, reviewing vendor compliance documentation annually, and serving as the internal point of contact for regulatory enquiries.

This role does not require a dedicated headcount. It requires clear designation and documented authority. Assign it in writing and reflect it in your organisational chart.

**Responsible authority:** Internal. No external registration required, but the designation should appear in your governance documentation in case of audit.

### Step 5 — Create bilingual technical documentation for high-risk systems

This is the step where Belgian complexity becomes concrete. The EU AI Act requires technical documentation for high-risk AI systems that is intelligible to the competent authority. In Belgium, where the competent authority and your workforce may operate in French, Dutch, or both, documentation that exists only in English is insufficient for audit purposes.

For each high-risk system, prepare a documentation package that includes: system description, intended purpose, risk assessment, human oversight mechanisms, and data governance summary. Where your workforce operating the system is French-speaking, the user-facing documentation must be in French. Where it is Dutch-speaking, Dutch is required. For Brussels-based firms with mixed-language workforces, both versions are the safe default.

**Responsible authority:** SPF Économie / FOD Economie (national competent authority), Belgian DPA for data governance components.

### Step 6 — Implement a human oversight procedure for each high-risk system

The EU AI Act requires that deployers of high-risk AI systems implement appropriate human oversight measures. This means defining, for each high-risk system: who reviews AI-assisted decisions before they are acted upon, what criteria trigger escalation for human review, and how overrides are recorded.

Document this procedure in writing. It does not need to be elaborate — a one-page procedure per system is sufficient for most SME contexts. What matters is that it is written, communicated to the staff involved, and followed in practice.

**Responsible authority:** Oversight procedures are subject to review by the national competent authority in the event of an incident or complaint.

---

## Phase 3: Vendor Due Diligence

### Step 7 — Require EU AI Act compliance documentation from AI vendors

As a deployer, you are entitled to receive from your AI system providers the technical documentation, conformity assessments, and post-market monitoring information required under the EU AI Act. Send a formal request to each vendor of a high-risk system asking for: their EU AI Act conformity documentation, their data processing terms, and their incident notification procedure.

Vendors who cannot provide this documentation within a reasonable period are a compliance liability. Document your requests and their responses. Vendors operating in the EU market have obligations under the Act; a failure to respond is relevant information for your own risk assessment.

**Responsible authority:** Vendor obligations are enforced through the market surveillance mechanism. Your documentation of vendor requests protects you in the event of a regulatory enquiry directed at your operations.

### Step 8 — Apply FSMA overlay if operating in financial services

Belgian companies in financial services — insurance, lending, investment, payment processing — face an additional regulatory layer from the FSMA (Financial Services and Markets Authority / Autorité des services et marchés financiers / Autoriteit voor Financiële Diensten en Markten). The FSMA has published supervisory expectations for AI use in financial services that go beyond the EU AI Act baseline, including requirements around model explainability, fairness testing, and governance documentation.

If your company is FSMA-supervised or uses AI systems that inform financial decisions about clients, review your AI governance documentation against FSMA guidance and assess whether your AI systems require notification or prior approval.

**Responsible authority:** FSMA. This step is specific to Belgian financial sector SMEs and has no equivalent in the generic EU AI Act implementation guidance.

### Step 9 — Review AI clauses in your insurance and professional liability coverage

EU AI Act non-compliance can result in administrative fines up to €15 million or 3% of global annual turnover for deployers. More immediately, an AI system failure that causes harm to a client or employee may generate a liability claim. Review your professional indemnity and technology errors and omissions policies to confirm that AI-related incidents are covered. Many policies written before 2024 are silent on AI liability.

**Responsible authority:** Internal. No regulatory filing, but material gaps in insurance coverage should be disclosed to your board or governing body.

---

## Phase 4: Staff and Management Routines

### Step 10 — Train all staff who operate high-risk AI systems

The EU AI Act requires that deployers ensure their staff have sufficient AI literacy to operate high-risk systems appropriately. For Belgian SMEs, this means training content must be available in the working language of the staff involved — French for Walloon operations, Dutch for Flemish operations, both for Brussels mixed-language teams.

Training does not need to be lengthy. A two-hour session covering: what the system does, what its limitations are, how to identify outputs that require human review, and how to log concerns is an appropriate baseline. Document attendance and retain records for at least three years.

**Responsible authority:** AI literacy obligations are enforceable by the national competent authority. The Belgian DPA may also examine training adequacy in the context of GDPR-adjacent AI processing.

### Step 11 — Establish an AI incident log and reporting procedure

Create a simple log for recording AI system incidents: cases where the system produced an output that was incorrect, biased, or harmful; cases where a human override was applied; and cases where a client or employee raised a concern about an AI-assisted decision. Review the log quarterly and use it to inform vendor discussions and system reviews.

Under the EU AI Act, serious incidents involving high-risk AI systems must be reported to the national competent authority. Define in advance what constitutes a serious incident in your operational context, and assign responsibility for making the report.

**Responsible authority:** SPF Économie / FOD Economie for serious incident reporting. Belgian DPA if the incident involves a personal data breach dimension.

### Step 12 — Schedule an annual AI governance review

EU AI Act obligations are not a one-time implementation project. Vendor systems change, your operational use of AI evolves, and regulatory guidance is updated. Schedule an annual review — one half-day is sufficient for most SME contexts — to: refresh the AI system inventory, check that vendor documentation is current, confirm that human oversight procedures are being followed, review the incident log, and update training materials.

Document the outcome of each annual review and retain it. In the event of a regulatory enquiry, a documented history of good-faith annual reviews is material evidence of diligent compliance.

**Responsible authority:** Internal governance, with outputs available for inspection by SPF Économie / FOD Economie and the Belgian DPA.

---

## The Belgian Compliance Advantage You Should Not Miss

Belgian SMEs that invest in structured EU AI Act compliance are better positioned in EU institutional procurement, in FSMA-supervised financial services, and in any client relationship where AI governance is a contractual requirement. The compliance burden is real — particularly the bilingual documentation requirement and the FSMA overlay — but it is manageable at SME scale if approached systematically rather than reactively.

The twelve steps above are designed to be completed over a three-month period by an existing team member with part-time focus. The output is a compliance posture that will withstand scrutiny from the Belgian DPA, SPF Économie, and FSMA — and a documented foundation that makes future updates straightforward rather than costly.

[Talk to us about AI advisory for your Belgian company →](https://radar.firstaimovers.com/page/ai-consulting)

[Start with an AI readiness assessment →](https://radar.firstaimovers.com/page/ai-readiness-assessment)

## Frequently Asked Questions

### Does the EU AI Act apply to Belgian SMEs that only use third-party AI tools, not build them?
Yes. The EU AI Act distinguishes between providers (developers) and deployers (users). Belgian SMEs that use AI systems from third-party vendors — including SaaS tools with AI features — are deployers and have active compliance obligations if any of those systems fall into high-risk categories. Obligations include human oversight procedures, staff training, and maintaining documentation of your use of the system.

### What is the role of the Belgian DPA in EU AI Act compliance?
The Belgian DPA (Autorité de protection des données / Gegevensbeschermingsautoriteit) retains jurisdiction over the personal data processing dimensions of AI system use. Where an AI system processes personal data — which is the case for most high-risk systems — GDPR and EU AI Act obligations overlap. The DPA can investigate AI-related complaints that have a personal data dimension, independent of any action by the national AI competent authority under SPF Économie.

### Do Belgian SMEs need to produce AI compliance documentation in both French and Dutch?
For high-risk AI systems, the answer is effectively yes for Brussels-based firms and firms with mixed-language workforces. User-facing documentation and staff training materials must be in the working language of the staff operating the system. Technical documentation for competent authority review must be intelligible to that authority. Belgian SMEs operating across language communities should treat bilingual documentation as a default, not an exception.

### What are the fines for EU AI Act non-compliance for Belgian SMEs?
Administrative fines for deployers of high-risk AI systems can reach €15 million or 3% of global annual turnover, whichever is higher, for serious violations. For prohibited AI practices, the ceiling is €35 million or 7% of turnover. For smaller infringements such as providing incorrect information to authorities, the ceiling is €7.5 million or 1% of turnover. For most Belgian SMEs, the proportionality principle means enforcement will prioritise documented good-faith efforts over technical gaps, but documented non-compliance is a material risk.

## Read Further

- [EU AI Act Operational Checklist for Dutch SMEs 2026](https://radar.firstaimovers.com/eu-ai-act-operational-checklist-dutch-smes-2026)
- [What an AI Readiness Assessment Should Cover](https://radar.firstaimovers.com/what-an-ai-readiness-assessment-should-cover)
- [AI Vendor Scorecard for Dutch SMEs 2026](https://radar.firstaimovers.com/ai-vendor-scorecard-dutch-smes-2026)
- [AI Readiness for Ghent and Antwerp Industrial SMEs](https://radar.firstaimovers.com/ai-readiness-ghent-manufacturing-smes-2026)

<!--
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Article","headline":"EU AI Act Compliance for Belgian SMEs: A 12-Step Operational Checklist","description":"A practical 12-step EU AI Act compliance checklist for Belgian SMEs, mapped to Belgian authorities: DPA, FSMA, SPF Économie, and bilingual documentation rules.","author":{"@type":"Organization","name":"First AI Movers","url":"https://radar.firstaimovers.com"},"publisher":{"@type":"Organization","name":"First AI Movers","url":"https://radar.firstaimovers.com"},"mainEntityOfPage":{"@type":"WebPage","@id":"https://radar.firstaimovers.com/eu-ai-act-operational-checklist-belgian-smes-2026"}}
</script>
-->

<!--
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"Does the EU AI Act apply to Belgian SMEs that only use third-party AI tools, not build them?","acceptedAnswer":{"@type":"Answer","text":"Yes. The EU AI Act distinguishes between providers (developers) and deployers (users). Belgian SMEs that use AI systems from third-party vendors — including SaaS tools with AI features — are deployers and have active compliance obligations if any of those systems fall into high-risk categories. Obligations include human oversight procedures, staff training, and maintaining documentation of your use of the system."}},{"@type":"Question","name":"What is the role of the Belgian DPA in EU AI Act compliance?","acceptedAnswer":{"@type":"Answer","text":"The Belgian DPA (Autorité de protection des données / Gegevensbeschermingsautoriteit) retains jurisdiction over the personal data processing dimensions of AI system use. Where an AI system processes personal data — which is the case for most high-risk systems — GDPR and EU AI Act obligations overlap. The DPA can investigate AI-related complaints that have a personal data dimension, independent of any action by the national AI competent authority under SPF Économie."}},{"@type":"Question","name":"Do Belgian SMEs need to produce AI compliance documentation in both French and Dutch?","acceptedAnswer":{"@type":"Answer","text":"For high-risk AI systems, the answer is effectively yes for Brussels-based firms and firms with mixed-language workforces. User-facing documentation and staff training materials must be in the working language of the staff operating the system. Technical documentation for competent authority review must be intelligible to that authority. Belgian SMEs operating across language communities should treat bilingual documentation as a default, not an exception."}},{"@type":"Question","name":"What are the fines for EU AI Act non-compliance for Belgian SMEs?","acceptedAnswer":{"@type":"Answer","text":"Administrative fines for deployers of high-risk AI systems can reach €15 million or 3% of global annual turnover, whichever is higher, for serious violations. For prohibited AI practices, the ceiling is €35 million or 7% of turnover. For smaller infringements such as providing incorrect information to authorities, the ceiling is €7.5 million or 1% of turnover. For most Belgian SMEs, the proportionality principle means enforcement will prioritise documented good-faith efforts over technical gaps, but documented non-compliance is a material risk."}}]}
</script>
-->

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "EU AI Act Compliance for Belgian SMEs: A 12-Step Operational Checklist",
  "description": "A practical 12-step EU AI Act compliance checklist for Belgian SMEs, mapped to Belgian authorities: DPA, FSMA, SPF Économie, and bilingual documentation r…",
  "datePublished": "2026-04-13T15:20:03.091265+00:00",
  "dateModified": "2026-04-13T15:20:03.091265+00:00",
  "author": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com"
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
    "@id": "https://radar.firstaimovers.com/eu-ai-act-operational-checklist-belgian-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&h=630&fit=crop&q=80"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Does the EU AI Act apply to Belgian SMEs that only use third-party AI tools, not build them?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. The EU AI Act distinguishes between providers (developers) and deployers (users). Belgian SMEs that use AI systems from third-party vendors — including SaaS tools with AI features — are deployers and have active compliance obligations if any of those systems fall into high-risk categories. O..."
      }
    },
    {
      "@type": "Question",
      "name": "What is the role of the Belgian DPA in EU AI Act compliance?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The Belgian DPA (Autorité de protection des données / Gegevensbeschermingsautoriteit) retains jurisdiction over the personal data processing dimensions of AI system use. Where an AI system processes personal data — which is the case for most high-risk systems — GDPR and EU AI Act obligations over..."
      }
    },
    {
      "@type": "Question",
      "name": "Do Belgian SMEs need to produce AI compliance documentation in both French and Dutch?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For high-risk AI systems, the answer is effectively yes for Brussels-based firms and firms with mixed-language workforces. User-facing documentation and staff training materials must be in the working language of the staff operating the system. Technical documentation for competent authority revi..."
      }
    },
    {
      "@type": "Question",
      "name": "What are the fines for EU AI Act non-compliance for Belgian SMEs?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Administrative fines for deployers of high-risk AI systems can reach €15 million or 3% of global annual turnover, whichever is higher, for serious violations. For prohibited AI practices, the ceiling is €35 million or 7% of turnover. For smaller infringements such as providing incorrect informati..."
      }
    }
  ]
}
</script>
-->