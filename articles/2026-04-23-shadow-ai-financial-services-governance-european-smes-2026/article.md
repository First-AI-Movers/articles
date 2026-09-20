---
title: "Shadow AI in European Financial Services: Why the Regulatory Stakes Are Higher Than You Think"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/shadow-ai-financial-services-governance-european-smes-2026"
published_date: "2026-04-23"
license: "CC BY 4.0"
---

> **TL;DR:** MiFID II, DORA, GDPR Article 22: why financial services SMEs face higher shadow AI risk and how to govern it before your regulator finds it first.

Your analysts are summarising client portfolios in ChatGPT. Your credit team is running informal scoring logic in a personal Claude account. Your operations manager built a no-code automation that screens incoming payments using an AI classifier nobody documented.

Why this matters: financial services firms face a category of shadow AI risk that general SMEs do not. MiFID II requires auditable records of investment decisions. DORA mandates operational resilience for ICT systems, including third-party tools. GDPR Article 22 restricts automated decisions that significantly affect clients. When a member of staff uses an unapproved AI tool inside these workflows, the firm is not just taking a data security risk. It is creating a regulatory gap that an auditor, a DPO, or the FCA can walk straight through. A 20-person independent financial adviser in Dublin or a boutique asset manager in Amsterdam faces exactly the same obligations as a large bank. The difference is that the small business rarely has a dedicated second line to catch this before it becomes a finding.

This article covers the specific shadow AI risk scenarios regulators are already watching for, a detection approach scaled to financial services SMEs, and a governance framework that maps to your actual obligations under DORA, MiFID II, and GDPR.

## Why Financial Services SMEs Face Disproportionate Shadow AI Risk

Shadow AI exists in every sector. The problem in financial services is not the volume of unsanctioned tools. It is the intersection of those tools with three regulatory frameworks simultaneously.

**MiFID II** (Markets in Financial Instruments Directive II) requires that investment firms maintain records of investment decisions, communications, and the rationale behind advice given to clients. If an adviser uses a generative AI tool to draft a portfolio summary or generate a market commentary, that output becomes part of the decision trail. The tool is not in your ICT register. The prompt is not stored. The output was not reviewed under a documented process. That is a record-keeping gap.

**DORA** (Digital Operational Resilience Act), which became applicable in January 2025, requires financial services firms to maintain registers of ICT third-party providers, assess their operational risk, and demonstrate resilience. An AI tool a staff member subscribes to on a personal card is a third-party ICT provider. It is outside your DORA register. If a workflow depends on it and the tool goes down or changes its terms of service, you have an undocumented operational dependency.

**GDPR Article 22** restricts decisions based solely on automated processing when those decisions produce legal or similarly significant effects for a natural person. A credit assessment, a risk suitability score, a fraud flag: all of these can be Article 22 decisions. If an employee builds an informal AI workflow that contributes to such a decision without disclosure, without a human review process, and without a lawful basis documented, you have a live compliance breach.

The combination means that a single unapproved AI tool in a financial services workflow can simultaneously create a MiFID II record-keeping gap, a DORA third-party risk exposure, and a GDPR Article 22 breach. That is a profile no other sector faces in quite the same configuration.

## Five Shadow AI Scenarios Regulators Are Already Watching

These are not hypothetical. They represent patterns already identified in regulatory guidance from the FCA, the EBA, and supervisory communications from EU NCAs (national competent authorities) during 2025.

### Scenario 1: ChatGPT-Assisted Portfolio Summaries

An adviser at a 15-person IFA practice pastes client portfolio data into ChatGPT to generate a quarterly review summary for the client meeting. The data includes account values, asset allocations, and performance figures. This creates a GDPR data transfer to a third-party processor with no DPA in place, a MiFID II record-keeping gap (the AI output is not stored or reviewed under a documented process), and an implicit DORA third-party dependency that is not in the ICT register.

### Scenario 2: AI-Drafted Financial Advice Without Disclosure

A wealth management associate uses an AI writing tool to draft the narrative sections of a suitability report. The AI output is lightly edited and sent to the client. Under MiFID II, the firm must be able to demonstrate that the advice reflects the client's actual profile and circumstances. An AI-generated narrative that has not been reviewed against that standard, documented, and stored creates a suitability audit trail problem.

### Scenario 3: Informal Credit Scoring Automation

A fintech startup's credit operations team builds a no-code automation using a personal Zapier account. The automation queries an AI model to assess incoming loan applications based on text descriptions. No Article 22 disclosure exists. No human review checkpoint is documented. No explainability mechanism is in place. The automation processes real client data. This is a GDPR Article 22 breach and a potential FCA consumer duty issue.

### Scenario 4: Payment Screening via Unapproved AI Classifier

A payments company's compliance analyst uses an AI tool to help screen high-volume transaction data for sanctions or AML flags. The tool is not in the firm's approved software list. The screening logic is not documented. If the tool misses a flag or produces a false positive that is acted upon, the firm cannot demonstrate to its regulator that its screening process was robust, auditable, or compliant with its AML policy.

### Scenario 5: Insurance Underwriting Inputs

An insurance broker's commercial underwriting team uses an AI tool to summarise broker submissions and suggest initial pricing bands. These outputs inform underwriting decisions. The AI tool is not documented in the firm's underwriting framework. The pricing suggestions are not disclosed as AI-assisted outputs. If a client challenges a decision or a regulator reviews the process, the firm cannot produce an audit trail for the input stage of the underwriting decision.

## Detection Approach for Financial Services Teams

General shadow AI detection (browser history scanning, procurement audits) is necessary but not sufficient in financial services. You need to map shadow AI to workflow risk, not just to tool presence.

**Step 1: Workflow-first inventory.** Start with your five highest-risk workflow categories: client communications, investment or credit decisions, compliance screening, client data processing, and regulatory reporting. For each, ask: does any step in this workflow involve a tool that is not in our approved software register?

**Step 2: Expense and SaaS audit.** Review corporate card statements, personal expense claims, and SaaS billing for AI tool subscriptions. Look specifically for generative AI subscriptions (OpenAI, Anthropic, Google Gemini, Perplexity), no-code automation tools (Zapier, Make, n8n), and AI writing tools. Cross-reference against your approved vendor list.

**Step 3: Staff disclosure review.** Issue a structured disclosure request to all staff: list any AI tools you use in connection with your work, including personal accounts. Frame this as an amnesty process, not a disciplinary one. Financial services staff are aware of regulatory obligations; most will disclose when asked directly.

**Step 4: Workflow-regulatory mapping.** For each identified shadow tool, map it to the regulatory obligation it touches: Does it process client data? (GDPR, DORA.) Does it contribute to an investment or credit decision? (MiFID II, Article 22.) Is it a third-party ICT dependency? (DORA.) This mapping drives your remediation priority order.

## Governance Framework: Satisfying DORA and MiFID II Requirements

A governance framework for financial services shadow AI needs three elements beyond the baseline SME approach.

**Approved vendor register with regulatory mapping.** Your AI vendor register should include, for each approved tool: the regulatory obligations it touches, the DPA or data processing addendum in place, the DORA third-party risk classification (material or non-material ICT dependency), and the review cadence. This register is the evidence file you produce for a DORA or MiFID II audit.

**Decision trail protocol for AI-assisted outputs.** Any AI-assisted output that contributes to a MiFID II-relevant decision (investment advice, suitability assessment, portfolio review) must be: stored in the firm's record-keeping system, marked as AI-assisted, reviewed and signed off by a named responsible person, and retained for the applicable MiFID II retention period (typically five years, or seven for pension advice).

**Article 22 boundary document.** Document which workflows involve automated decisions that may have significant effects on clients. For each, document the lawful basis relied upon, the human review checkpoint, and the disclosure mechanism used with clients. This document is your GDPR accountability evidence under Article 5(2).

**Quarterly shadow AI review.** Build a standing agenda item into your quarterly compliance committee or IT governance meeting: new shadow AI incidents, approved vendor register updates, and any regulatory guidance updates relevant to AI use. Fifteen minutes per quarter prevents the cumulative drift that creates regulatory findings.

## When to Escalate to Your DPO or Compliance Officer

Not every shadow AI discovery requires DPO involvement. Escalate when:

- A shadow tool has processed or could have processed personal data of clients, including financial data, health data for insurance, or identity documents.
- A shadow tool has contributed to a decision that could qualify under GDPR Article 22 (credit, insurance pricing, suitability).
- A shadow tool is a material operational dependency (staff cannot perform a core function without it) and is not in your DORA ICT register.
- A client has been affected by an AI-assisted output that was not disclosed as such.

For independent financial advisers and smaller asset managers without an in-house DPO, this escalation may go to an external DPO or a compliance consultant. The obligation to have a documented escalation path is the same regardless of firm size.

## Frequently Asked Questions

### Does DORA apply to small financial services firms?

DORA applies to a broad range of financial entities including credit institutions, investment firms, insurance undertakings, and payment institutions. Proportionality applies: smaller firms face lighter requirements in some areas, but the obligation to maintain an ICT third-party register and assess operational resilience is not exempted by size. If your firm is regulated and uses AI tools in operational workflows, DORA applies.

### What counts as an "automated decision" under GDPR Article 22?

Article 22 applies to decisions based solely on automated processing that produce legal effects or similarly significant effects for an individual. In financial services, this includes automated credit decisions, insurance pricing decisions based purely on algorithmic outputs, and suitability assessments where AI output is not reviewed by a human before the recommendation is made. Human review is both a safeguard and the primary mechanism for establishing that a decision is not "solely" automated.

### Can we simply ban all unapproved AI tools?

Prohibition without an approved alternative tends to drive use further underground. A more effective approach is to establish a fast-track approval process for commonly requested tools, communicate it clearly to staff, and pair prohibition with a small approved list that covers the most common use cases. Complete prohibition is also practically unenforceable without monitoring infrastructure most professional services firms do not have.

## Further Reading

- [Shadow AI Detection and Governance for European SMEs](https://radar.firstaimovers.com/shadow-ai-detection-governance-european-smes-2026)
- [AI Governance in Financial Services: A Framework for European SMEs](https://radar.firstaimovers.com/ai-governance-financial-services-european-smes-2026)
- [AI Vendor Evaluation Scorecard for European SMEs](https://radar.firstaimovers.com/ai-vendor-evaluation-scorecard-european-smes-2026)

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Shadow AI in European Financial Services: Why the Regulatory Stakes Are Higher Than You Think",
  "description": "MiFID II, DORA, GDPR Article 22: why financial services SMEs face higher shadow AI risk and how to govern it before your regulator finds it first.",
  "datePublished": "2026-04-23T12:03:40.721291+00:00",
  "dateModified": "2026-04-23T12:03:40.721291+00:00",
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
    "@id": "https://radar.firstaimovers.com/shadow-ai-financial-services-governance-european-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=1200&h=630&fit=crop&q=80"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Does DORA apply to small financial services firms?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DORA applies to a broad range of financial entities including credit institutions, investment firms, insurance undertakings, and payment institutions. Proportionality applies: smaller firms face lighter requirements in some areas, but the obligation to maintain an ICT third-party register and ass..."
      }
    },
    {
      "@type": "Question",
      "name": "What counts as an "automated decision" under GDPR Article 22?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Article 22 applies to decisions based solely on automated processing that produce legal effects or similarly significant effects for an individual. In financial services, this includes automated credit decisions, insurance pricing decisions based purely on algorithmic outputs, and suitability ass..."
      }
    },
    {
      "@type": "Question",
      "name": "Can we simply ban all unapproved AI tools?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Prohibition without an approved alternative tends to drive use further underground. A more effective approach is to establish a fast-track approval process for commonly requested tools, communicate it clearly to staff, and pair prohibition with a small approved list that covers the most common us..."
      }
    }
  ]
}
</script>
-->