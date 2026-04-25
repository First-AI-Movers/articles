---
title: "Where Does Your AI Vendor's Data Go? A Practical EU Residency Guide for SMEs"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/ai-data-residency-guide-european-smes-2026"
published_date: "2026-04-24"
license: "CC BY 4.0"
---
> **TL;DR:** Which AI vendors store your data in the EU, and what configuration is required. A GDPR and EU AI Act compliance guide for European SME operators.

Why this matters: When a team member at your 30-person consulting firm pastes a client contract into Claude or ChatGPT, that text leaves your office and travels to a server. Where it goes, how long it stays, and who can access it determines whether your AI tool use is GDPR-compliant. Most European SME operators do not know the answer for the tools their teams use daily.

Data residency for AI tools is not the same as general cloud data residency. A company might store its CRM data in an EU AWS region but use an AI assistant that processes all queries through US-based inference infrastructure. The two are separate configurations, and both matter under GDPR.

This guide maps the data residency options for the five AI tools used most frequently by European business teams, explains what GDPR requires, and gives you a practical configuration checklist.

## What GDPR Requires for AI Tool Data Residency

GDPR does not prohibit transferring personal data outside the EU, but it does require that appropriate safeguards are in place when data is transferred to countries without an EU adequacy decision.

The United States does not have a blanket adequacy decision, though the EU-US Data Privacy Framework (DPF) adopted in 2023 provides a mechanism for transfers to certified US organisations. All major AI vendors (OpenAI, Anthropic, Google, Microsoft) participate in or maintain Standard Contractual Clauses (SCCs) for EU-to-US transfers.

**What this means in practice**:
- If you are using a paid business plan from a major AI vendor with a signed Data Processing Agreement (DPA), your transfer mechanism is typically covered by SCCs or DPF certification.
- If you are using a free consumer plan, you likely have no DPA in place, which means any personal data you process through the tool creates a compliance gap.
- If your team processes personal data of EU residents through any AI tool (client names, employee records, health information, financial data), you need a DPA before that processing starts.

The additional EU AI Act consideration: if the AI tool makes decisions or assists in decisions that affect individuals (hiring, credit, performance evaluation), you must classify it under the EU AI Act risk framework and maintain records accordingly.

## AI Vendor Data Residency: What Is Available in 2026

### OpenAI (ChatGPT, ChatGPT Enterprise, API)

ChatGPT Free and ChatGPT Plus: Data processed in OpenAI's standard infrastructure, primarily US-based. No EU data residency option. OpenAI uses EU-US DPF and SCCs for EU data transfers. Training on your data occurs by default unless you opt out in settings.

ChatGPT Team: DPA available. Data processed in US infrastructure. Training on your data is off by default. EU data residency is not available at this tier.

ChatGPT Enterprise: DPA available. Zero-data retention by default (prompts and responses not stored after session). EU data residency options available for some configurations. Confirm specifics with your account manager before committing.

OpenAI API: DPA available. Zero-data retention by default. EU data residency is available through Azure OpenAI Service (not directly through OpenAI's API), which offers EU-resident inference for most models.

**Key action**: If your team uses ChatGPT for any task involving personal data of EU residents, upgrade to at least ChatGPT Team, sign the DPA, and confirm training is disabled. For EU data residency, use Azure OpenAI Service or ChatGPT Enterprise with EU configuration confirmed.

### Anthropic (Claude.ai, Claude API)

Claude.ai Free and Pro: Data processed in Anthropic's standard infrastructure. Anthropic uses SCCs for EU data transfers. Prompts and responses are retained for 30 days by default.

Claude.ai Team: DPA available. Data retention controls available. Training on your data is off by default. EU data residency is not currently offered directly by Anthropic.

Claude API (directly): DPA available. Prompts and responses are not used for training by default. Retention is configurable. EU data residency is available through AWS Bedrock (Claude on AWS Bedrock in eu-west-1, eu-central-1 regions), not directly through Anthropic's API.

**Key action**: For EU data residency with Claude, use AWS Bedrock with an EU region selected. For standard use with GDPR compliance, use the Claude API or Claude Team plan with a signed DPA.

### Google (Gemini, Google Workspace AI)

Gemini for Google Workspace: For organisations using Google Workspace Business or Enterprise, Gemini AI features process data under the Google Workspace DPA. Data residency follows your Google Workspace data region configuration (EU region available). Prompts are not used for training under the Workspace terms.

Gemini Advanced (personal): No business DPA. Not appropriate for personal data of EU residents.

Google Cloud Vertex AI (Gemini API): Enterprise-grade. EU data residency available through Google Cloud EU regions. DPA available. Zero training on your data by default.

**Key action**: For EU SMEs already in Google Workspace, Gemini is the clearest path to EU data residency for AI features. Configure your Workspace data region to EU and confirm the DPA covers AI processing.

### Microsoft (Copilot for Microsoft 365, Azure OpenAI)

Copilot for Microsoft 365: For organisations with Microsoft 365 Business or Enterprise plans, Copilot processes data under the Microsoft Product Terms and DPA. EU data residency follows your Microsoft 365 data location configuration. Prompts are not used to train foundation models.

Azure OpenAI Service: Enterprise-grade. EU data residency available (West Europe, North Europe regions). DPA available. Zero training on customer data by default.

**Key action**: For EU SMEs already on Microsoft 365, Copilot for M365 with EU data location configured is a straightforward path to compliant AI tool use with EU data residency.

## The GDPR Configuration Checklist

Before using any AI tool for tasks involving personal data of EU residents, complete this five-step checklist:

**Step 1: Categorise the data your team pastes into AI tools**
Map what categories of personal data your team uses AI to process: client names, email addresses, employee records, financial data, health information. Each category has different GDPR sensitivity and some (health, biometric) require explicit legal basis.

**Step 2: Confirm a DPA exists for each tool**
For each AI tool in use, confirm you have a signed Data Processing Agreement with the vendor. Consumer plans (free tiers, personal subscriptions) do not come with DPAs. Business plans typically do. Keep copies of signed DPAs in your legal records.

**Step 3: Confirm training-off settings**
Verify that your AI vendor is not using your prompts and outputs to train or fine-tune its models. For most paid business plans, training is off by default. Check the settings panel and confirm in writing with your vendor if the setting is not clearly documented.

**Step 4: Confirm data residency configuration if required**
If your organisation processes sensitive personal data (health, financial, biometric) or if your clients or regulators require EU data residency, configure EU-resident processing through your vendor's supported path (Azure, AWS Bedrock, Google Cloud EU regions, or Microsoft 365 EU data location).

**Step 5: Update your Article 30 records**
Add each AI tool used for personal data processing to your GDPR Article 30 records of processing activities. Include the tool name, the categories of data processed, the legal basis, the retention period, and the transfer mechanism (DPA, SCCs, DPF).

## What to Include in Your AI Use Policy

Your AI use policy should specify which tools are approved for which data categories. A practical structure:

- **Green list (approved for all work, including personal data)**: Tools with signed DPA, training disabled, EU residency configured (or SCC/DPF transfer mechanism documented)
- **Yellow list (approved for non-personal data only)**: Tools with signed DPA but no EU residency; acceptable for internal use on data that does not include personal information of EU residents
- **Red list (not approved for work use)**: Consumer-tier tools with no DPA; personal devices with consumer AI apps

This structure gives team members clear guidance without requiring them to understand GDPR in detail.

## FAQ

### Does "EU data residency" mean my data never leaves the EU?

EU data residency means that your data is stored and processed within EU infrastructure. However, vendor employees, including those based outside the EU, may access data for support or maintenance purposes under controlled conditions. Your DPA should specify the access controls and sub-processor locations. "EU data residency" is not the same as "no access by non-EU staff," but it significantly reduces your GDPR transfer risk.

### If I use Claude through AWS Bedrock in an EU region, does Anthropic ever see my data?

AWS Bedrock provides isolated inference infrastructure. When you use Claude through AWS Bedrock, your prompts are processed in the selected AWS region and are not accessible to Anthropic for training or review under standard terms. The AWS DPA and Anthropic's Bedrock terms govern the arrangement. This is the standard enterprise model for AI data isolation.

### Do I need EU data residency for all AI use, or only for sensitive data?

EU data residency is required or strongly recommended specifically when processing personal data of EU residents under circumstances where a US-based transfer without adequate safeguards would create GDPR exposure. For internal tasks that do not involve personal data (e.g., summarising industry news, drafting generic content), EU data residency is not legally required, though many organisations prefer it as a default for simplicity.

### What happens if my team uses consumer AI tools for work tasks?

Using consumer AI tools (free-tier ChatGPT, personal Gemini accounts) for work tasks involving personal data of EU residents creates a GDPR compliance gap. There is no DPA, so you are the data controller without a compliant processing arrangement. If audited, this could result in regulatory action. The practical fix is to provide your team with approved business-tier alternatives and update your AI use policy to prohibit consumer tool use for work data.

## Further Reading

- [AI Vendor Evaluation Scorecard for European SMEs](https://radar.firstaimovers.com/ai-vendor-evaluation-scorecard-european-smes-2026)
- [AI Data Governance Framework for European SMEs](https://radar.firstaimovers.com/ai-data-governance-framework-european-smes-2026)
- [EU AI Act GPAI August 2026 Compliance Checklist](https://radar.firstaimovers.com/eu-ai-act-gp-systems-august-2026-compliance-checklist)
- [AI Vendor Contract Negotiation: 7 Clauses Every European SME Needs](https://radar.firstaimovers.com/ai-vendor-contract-negotiation-european-smes-2026)
- [Claude Code Security and Data Privacy for European Teams](https://radar.firstaimovers.com/claude-code-security-data-privacy-european-teams-2026)

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Where Does Your AI Vendor's Data Go? A Practical EU Residency Guide for SMEs",
  "description": "Which AI vendors store your data in the EU, and what configuration is required. A GDPR and EU AI Act compliance guide for European SME operators.",
  "datePublished": "2026-04-24T22:18:05.432085+00:00",
  "dateModified": "2026-04-24T22:18:05.432085+00:00",
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
    "@id": "https://radar.firstaimovers.com/ai-data-residency-guide-european-smes-2026"
  },
  "image": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1200&h=630&fit=crop&q=80",
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
      "name": "Does "EU data residency" mean my data never leaves the EU?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "EU data residency means that your data is stored and processed within EU infrastructure. However, vendor employees, including those based outside the EU, may access data for support or maintenance purposes under controlled conditions. Your DPA should specify the access controls and sub-processor ..."
      }
    },
    {
      "@type": "Question",
      "name": "If I use Claude through AWS Bedrock in an EU region, does Anthropic ever see my data?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "AWS Bedrock provides isolated inference infrastructure. When you use Claude through AWS Bedrock, your prompts are processed in the selected AWS region and are not accessible to Anthropic for training or review under standard terms. The AWS DPA and Anthropic's Bedrock terms govern the arrangement...."
      }
    },
    {
      "@type": "Question",
      "name": "Do I need EU data residency for all AI use, or only for sensitive data?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "EU data residency is required or strongly recommended specifically when processing personal data of EU residents under circumstances where a US-based transfer without adequate safeguards would create GDPR exposure. For internal tasks that do not involve personal data (e.g., summarising industry n..."
      }
    },
    {
      "@type": "Question",
      "name": "What happens if my team uses consumer AI tools for work tasks?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Using consumer AI tools (free-tier ChatGPT, personal Gemini accounts) for work tasks involving personal data of EU residents creates a GDPR compliance gap. There is no DPA, so you are the data controller without a compliant processing arrangement. If audited, this could result in regulatory actio..."
      }
    }
  ]
}
</script>
-->

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/ai-data-residency-guide-european-smes-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*