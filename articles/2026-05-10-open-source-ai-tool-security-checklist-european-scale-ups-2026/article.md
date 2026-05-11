---
title: "Open-Source AI Tool Security Checklist for European Scale-Ups"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/open-source-ai-tool-security-checklist-european-scale-ups-2026"
published_date: "2026-05-10"
license: "CC BY 4.0"
---

> **TL;DR:** A practical security checklist for European scale-ups evaluating open-source AI tools before procurement, covering license through DORA.

GitHub stars measure popularity, not security. For every open-source AI tool your engineering team or platform engineering team considers, a proper security review is the only way to know whether it belongs in your production infrastructure. This checklist replaces star-count procurement with a repeatable evaluation built for a CTO, a security lead, an AI transformation lead, a procurement-aware engineering manager, or a founder-led company moving fast. It covers everything from license clarity to EU regulatory compliance, with concrete owners and artifacts at every step. Why this matters: one unreviewed dependency can leak personal data, violate GDPR Article 28, or create liability under the EU AI Act, and the cost of unwinding a bad procurement decision lands on the operations leader and the finance team six months later. European scale-ups face three concurrent pressures: the EU AI Act sandbox deadline of 2 August 2026 (S11), GDPR data-flow obligations on every cross-border prompt and completion (S12), and for financial-services entities and their critical ICT vendors, DORA third-party-vendor rules effective since January 2025 (S15). The checklist below accounts for all three.

## The short version

- This article gives you a 22-item security checklist organized by signal category, plus a 30-day evaluation workflow and a procurement-ready artifact table.
- The seven signal categories separate **attention** from **maintenance**, **security**, **license**, **data flow**, **deployment / control**, and **support / vendor**. Stars sit only in the first column.
- The mandatory items are license clarity (S13), maintenance recency (last 90 days), OpenSSF Scorecard above 5 (S1), SBOM generation (S10), data-flow review, and an EU AI Act risk-tier classification (S11).
- The default decision is **do not promote without evidence**. A pilot that has not exercised rollback is not a pilot, it is a hope.
- For European teams, the data-flow question is decisive. Self-hosting (where supported) collapses residency risk; cloud-only tools need a documented residency posture before pilot.

## Why a security checklist replaces the star count

Star counts hide license risk, maintenance risk, and supply-chain risk. A repo with 50,000 stars may have no license file (S13), no recent commits, no security policy, and no SBOM. The seven signal categories in the next section separate these dimensions; the checklist then gives you a pass / fail or a graded score for each. Policy controls the merge button regardless of which AI tool the team adopts: CODEOWNERS (S14), repository rulesets (S8), and OWASP LLM01 mitigations (S4) form the policy spine. Without a checklist, you are flying blind on a procurement decision that locks in operating risk for years.

The other reason a checklist beats a star count is **comparability**. Two tools that both report 80,000 stars might score 8 / 10 and 3 / 10 on OpenSSF Scorecard, ship SLSA L3 build provenance and SLSA L0 respectively, and have completely different data-flow postures. A buyer-aware procurement memo lines up those columns and makes the decision obvious. Stars-only procurement throws away that comparability. Once your security team has the checklist artifacts in hand, the procurement conversation moves from "the team likes this one" to "this one passes the gates we agreed on; that one fails on items 4, 9, and 17." That is the conversation that holds up at the 2 August 2026 EU AI Act sandbox audit.

## The seven signal categories you must read separately

| Signal category | What it tells you | What to check | Red flag |
|---|---|---|---|
| Attention signals | How many people watch or star the repo; community interest | Compare star count with commit recency; look for issue response times | Many stars but no commits in 6 months; unanswered critical issues |
| Maintenance signals | Whether the project is alive and well | Last commit date, release cadence, number of maintainers, bus factor | One maintainer with no activity for 90+ days |
| Security signals | How seriously the team takes security | OpenSSF Scorecard (S1), presence of SECURITY.md (S5), Dependabot alerts (S6), CodeQL (S5) | Scorecard below 5; no SECURITY.md; no automated security scanning |
| License signals | Legal permission to use, modify, distribute | OSI-approved license (S13); check for commercial use clauses | No license file; non-OSI license like "Sustainable Use" without legal review |
| Data-flow signals | Where prompts, outputs, and telemetry go | Data-flow diagram; check for external API calls; read privacy policy | Prompts or outputs sent to untrusted third parties without opt-in |
| Deployment / control signals | How you run and govern the tool | Support for self-hosting; branch protection; rulesets (S8); SLSA provenance (S2, S9) | No container image available; no signed releases; cloud-only deployment |
| Support / vendor signals | Who to call when it breaks | Existence of a paid support channel; response SLAs; community size | No clear way to get help; single vendor lock-in |

## The full security checklist

- [ ] License clarity: confirm an OSI-approved license exists (S13).
- [ ] OSI approval check: ensure the license is on the OSI list; avoid "no license" default (S13).
- [ ] Last-commit recency check: commits within the last 90 days; ideally within 30.
- [ ] Maintainer count and bus-factor check: at least 2 active maintainers; no single point of failure.
- [ ] OpenSSF Scorecard score above 5 (S1).
- [ ] SECURITY.md present with disclosure policy (S5).
- [ ] Dependabot alerts enabled on the repo (S6).
- [ ] Secret scanning with push protection enabled (S5).
- [ ] CodeQL default setup enabled (S5).
- [ ] SBOM generation possible (S10).
- [ ] SLSA L2 build provenance available (S2, S9).
- [ ] Dependency graph reviewed against Advisory Database (S7).
- [ ] CODEOWNERS coverage on critical paths (S14).
- [ ] Branch protection rules + rulesets for production branches (S8).
- [ ] OWASP CI/CD Top 10 mitigations checked (S3).
- [ ] OWASP LLM01 prompt-injection mitigations addressed: least privilege, input/output filtering, human-in-the-loop for privileged operations (S4).
- [ ] Data-flow review: document where prompts and outputs are sent; ensure no unauthorized data leakage.
- [ ] GDPR Article 28 Data Processing Agreement in place where applicable (S12).
- [ ] EU AI Act risk-tier classification documented: determine whether the tool is low, high, or unacceptable risk (S11).
- [ ] DORA third-party-vendor coverage if financial services entity (S15).
- [ ] Rollback / exit plan documented: how to quickly remove the tool and restore previous state.
- [ ] Key / credential rotation cadence defined: rotate API keys and secrets every 90 days or on incident.

## A 30-day evaluation workflow

The 30-day workflow below is bounded, time-boxed, and produces named artifacts that hold up under audit. Skipping the artifacts is the most common failure mode; the artifacts are what carry the rigor between legal, security, and engineering when nobody has time for a daily meeting.

1. **Week 1: License and initial triage.** Owner: legal lead plus security engineer. Action: run license check (S13), OpenSSF Scorecard (S1), and repo recency scan. Confirm an OSI-approved license, Scorecard score above 5, last commit within 90 days, and three or more active maintainers (or a corporate sponsor). Artifact: license review memo with traffic-light status (green / amber / red) per use case. Success criterion: green or amber on every dimension; any red blocks progression to week 2 until the operations leader signs off on the explicit risk acceptance.
2. **Week 2: Security and supply-chain audit.** Owner: security engineer. Action: enable Dependabot alerts plus security updates (S6), CodeQL default setup (S5), and secret scanning with push protection (S5) on a fork or mirror. Verify SLSA L2 build provenance via GitHub Actions artifact attestations (S2, S9). Generate an SBOM that meets CISA minimum elements (S10) and cross-check it against the GitHub Advisory Database (S7). Walk the OWASP CI/CD Top 10 (S3) against the tool's pipeline definitions. Artifacts: SBOM, Scorecard report, OWASP CI/CD Top 10 review. Success criterion: no critical or high-severity advisories that lack a documented mitigation; SBOM completeness validated.
3. **Week 3: Data flow and regulation review.** Owner: Data Protection Officer plus CISO. Action: map every place a prompt, a completion, or a log can travel. Note storage region, encryption posture, and retention period. Draft a GDPR Article 28 Data Processing Agreement if the tool processes personal data of EU residents (S12). Classify the tool against the EU AI Act risk tiers (S11). For financial-services entities, complete a DORA third-party register entry (S15). For non-financial-services teams, use DORA framing as a maturity reference rather than a compliance requirement. Artifacts: data-flow diagram, GDPR DPA (if applicable), EU AI Act risk-tier classification memo, DORA register entry (if applicable). Success criterion: every data destination is documented, encrypted, and either inside the EU or covered by Standard Contractual Clauses.
4. **Week 4: Pilot and governance gate.** Owner: platform lead plus security engineer. Action: deploy to a restricted staging environment with branch protection rules (S5), repository rulesets (S8), CODEOWNERS coverage on critical paths (S14), and least-privilege access for any AI agent that participates. Run OWASP LLM01 prompt-injection tests against repo content and external retrieval surfaces (S4). Exercise rollback at least once during the week so the operations leader has confidence that revert is real, not theoretical. Artifact: pilot evidence report with one row per checklist item plus a rollback timing measurement. Success criterion: all critical checklist items pass; no unmitigated prompt-injection vector; rollback completes inside the team's stated incident-response window.
5. **Post-pilot: Rollback plan and owner assignment.** Owner: platform lead. Action: document the rollback steps in a runbook, assign an ongoing maintenance owner from the technical team, and set a credential rotation cadence (90 days is the cheapest default; 30 days where the tool touches sensitive data). Artifact: rollback / exit plan and credential rotation schedule. Success criterion: exit plan can be executed in under 15 minutes by the on-call engineer who did not run the pilot.
6. **Governance gate.** Review every artifact in a security committee with the CTO, CISO, legal lead, and a representative from the technical team that ran the pilot. Decide one of four outcomes: extend the pilot by two weeks if a single dimension is inconclusive, promote-bounded to a wider pilot in one more repo, reject the tool, or pause-for-fix on a named blocker. Artifact: governance gate decision memo signed by every named role.
7. **Continuous monitoring after promotion.** If the tool is promoted, schedule the OpenSSF Scorecard, the SBOM, and the data-flow diagram for refresh every 90 days. Wire Dependabot alerts to the security team's pager. The checklist is not a one-shot gate; the supply chain it covers shifts every quarter.

Interested in a guided pilot? Start with our [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) or explore [AI Consulting](https://radar.firstaimovers.com/page/ai-consulting) for European-scale-up specific support, including the regulatory mapping that an internal team rarely has bandwidth to do alongside the technical pilot.

## A procurement-ready owner and artifact table

| Artifact | Owner | When produced | Used by |
|---|---|---|---|
| License review memo | Legal | Week 1 | Security Engineer, Procurement |
| SBOM | Security Engineer | Week 2 | Platform Lead, CISO |
| SLSA provenance check | Security Engineer | Week 2 | Platform Lead |
| OpenSSF Scorecard report | Security Engineer | Week 1 | CISO, Security Engineer |
| Data-flow diagram | Data Protection Officer | Week 3 | CISO, Legal |
| GDPR DPA (if applicable) | Legal | Week 3 | Data Protection Officer |
| EU AI Act risk-tier classification memo | CISO | Week 3 | Legal, Board |
| DORA third-party register entry (if applicable) | CISO | Week 3 | Risk Management |
| Rollback / exit plan | Platform Lead | Week 4 | Operations, Security |
| Pilot evidence report | Security Engineer | Week 4 | Security Committee |

## What not to automate yet

- **Agents with merge authority:** never give an AI agent the ability to directly merge code. OWASP LLM01 (S4) and CODEOWNERS (S14) require human-in-the-loop for privileged operations.
- **Agents with shell access on production hosts:** an injected prompt could execute arbitrary commands. Keep AI agents in read-only or sandboxed environments.
- **Browser-automation agents in customer-facing flows:** they can be manipulated to perform actions on behalf of users. Isolate them from sensitive data.
- **Reliance on a no-license repo for commercial deployment:** default copyright makes it unusable without risk of litigation (S13). Always get legal approval.
- **Auto-promotion of pilot to production without governance gate:** a pilot is not production. Require a formal review of all artifacts.
- **Skipping SBOM generation because the project is small:** even small components can hide transitive vulnerabilities. Always generate an SBOM.

## How European regulation shapes the checklist

**EU AI Act (S11):** Classify your tool as low, high, or unacceptable risk by 2 August 2026, when Member States must offer regulatory sandboxes. High-risk tools (e.g., those used in hiring, credit scoring, or critical infrastructure) require additional transparency and documentation. This checklist includes a risk-tier classification memo.

**GDPR (S12):** Any open-source AI tool that processes personal data of EU residents requires a lawful basis and a Data Processing Agreement (Article 28). Map data flows to identify whether prompts or outputs contain personal data. If they do, the tool must support data subject rights and breach notification.

**DORA (S15):** For financial-services entities, every third-party ICT provider (including an open-source AI tool) must be registered in a third-party register. Contracts must include specific DORA clauses. Even if your company is not financial-services, using DORA as a maturity benchmark elevates your security posture.

**EU Cyber Resilience Act (S10):** The CRA will require SBOMs for commercial software. Start generating SBOMs now; it positions you ahead of compliance deadlines.

**Pragmatic sovereignty:** Self-hosting the AI tool (where supported) collapses the residency question to a contained, in-network deployment. Cloud-only tools need a documented residency posture before pilot. Document where data is processed and stored.

## Frequently Asked Questions

### Q: Do we need every item on the checklist for every tool?

No. Prioritize by tool risk and use case. For an internal experiment that processes no personal data and never reaches a customer-facing path, skip the GDPR DPA, the DORA register entry, and the EU AI Act risk-tier memo; you still need license clarity, maintenance recency, and a basic Scorecard. For production-facing tools that process personal data, run every item. The risk-tier classification from S11 is the cleanest way to set the bar in advance: low-risk tools get the short list (license, Scorecard, data-flow review, rollback plan); high-risk tools get the full 22 items plus a documented sandbox plan. Document the bar you applied so a future auditor can reproduce the decision.

### Q: How do we handle non-OSI licenses like Sustainable Use?

Non-OSI licenses (n8n's Sustainable Use License, Dify's restricted license, business-source licenses generally) are valid open-source choices but require legal review against your specific business model before any commercial embedding or hosted-service redistribution. The pattern is: legal lead reads the specific clauses against your contract for the proposed use, produces a one-page memo with traffic-light status (green / amber / red), and the procurement-aware engineering manager records the memo in the artifact register. For internal-only use behind a firewall, non-OSI licenses are usually safe; the constraint typically only fires when you start to redistribute or resell the tool itself, not when you use it to build your own product. A repo with no LICENSE file at all is a hard pass per S13 regardless of how popular it is.

### Q: Is OpenSSF Scorecard enough on its own?

No. Scorecard (S1) is necessary but not sufficient for European-scale-up procurement. It covers 18+ technical security signals (branch protection, code review, dependency update tools, signed releases, security policy, fuzzing, token permissions) but does not cover the data-flow question, the regulatory tier under EU AI Act, the GDPR DPA status, the DORA third-party register requirement, or the OWASP LLM01 prompt-injection mitigations. Treat Scorecard as one input among seven (the seven signal categories above). A score above 5 is the floor; a score above 7 is the comfortable bar; below 5 is a hard stop until the maintainers address the gaps. For high-risk tools, also require SLSA L2 build provenance (S2) on top of the Scorecard score.

### Q: When does DORA apply to our AI tooling decisions?

DORA (S15) applies directly to financial entities supervised in the EU: banks, investment firms, payment institutions, central counterparties, central securities depositories, trading venues, insurance and reinsurance undertakings, certain crypto-asset service providers, and a list of others in the regulation's Article 2 scope. If your scale-up is not a financial entity, DORA does not apply by force of law but applies indirectly when you sell or integrate with a financial entity that names you as a critical ICT third-party provider. In that case the financial-entity customer will require DORA-aligned contract language, incident-reporting commitments, and a register entry on their side. Even for non-financial-services teams, the DORA framing on third-party-vendor risk, ICT incident reporting, and resilience testing is a strong maturity reference. We list the DORA register entry as conditional in the artifact table so non-financial teams can skip it cleanly.

### Q: What is the realistic effort to run this checklist?

For a single tool, expect 2 to 4 weeks of calendar time and roughly 0.4 to 0.6 FTE-weeks of distributed effort. Week 1 is mostly legal and a security engineer running automated scans (Scorecard, license review). Week 2 is the security engineer doing the SBOM and the OWASP CI/CD Top 10 review. Week 3 is the Data Protection Officer plus the CISO mapping data flows and producing the GDPR / EU AI Act / DORA memos. Week 4 is the platform lead plus security engineer running the bounded pilot. None of the four weeks is full-time work. The cost of running the checklist is dwarfed by the cost of unwinding a bad procurement decision six months later, especially for a 20-person company or a small business that does not have a separate procurement function.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Open-Source AI Tool Security Checklist for European Scale-Ups",
  "description": "A practical security checklist for European scale-ups evaluating open-source AI tools before procurement, covering license through DORA.",
  "datePublished": "2026-05-10T18:20:41.117027+00:00",
  "dateModified": "2026-05-10T18:20:41.117027+00:00",
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
    "@id": "https://radar.firstaimovers.com/open-source-ai-tool-security-checklist-european-scale-ups-2026"
  },
  "image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1200&h=630&fit=crop&q=80",
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
      "name": "Q: Do we need every item on the checklist for every tool?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Prioritize by tool risk and use case. For an internal experiment that processes no personal data and never reaches a customer-facing path, skip the GDPR DPA, the DORA register entry, and the EU AI Act risk-tier memo; you still need license clarity, maintenance recency, and a basic Scorecard. ..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How do we handle non-OSI licenses like Sustainable Use?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Non-OSI licenses (n8n's Sustainable Use License, Dify's restricted license, business-source licenses generally) are valid open-source choices but require legal review against your specific business model before any commercial embedding or hosted-service redistribution. The pattern is: legal lead ..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: Is OpenSSF Scorecard enough on its own?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Scorecard (S1) is necessary but not sufficient for European-scale-up procurement. It covers 18+ technical security signals (branch protection, code review, dependency update tools, signed releases, security policy, fuzzing, token permissions) but does not cover the data-flow question, the reg..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: When does DORA apply to our AI tooling decisions?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "DORA (S15) applies directly to financial entities supervised in the EU: banks, investment firms, payment institutions, central counterparties, central securities depositories, trading venues, insurance and reinsurance undertakings, certain crypto-asset service providers, and a list of others in t..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: What is the realistic effort to run this checklist?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For a single tool, expect 2 to 4 weeks of calendar time and roughly 0.4 to 0.6 FTE-weeks of distributed effort. Week 1 is mostly legal and a security engineer running automated scans (Scorecard, license review). Week 2 is the security engineer doing the SBOM and the OWASP CI/CD Top 10 review. Wee..."
      }
    }
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "Open-Source AI Tool Security Checklist for European Scale-Ups",
  "description": "A practical security checklist for European scale-ups evaluating open-source AI tools before procurement, covering license through DORA.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Week 1: License and initial triage.",
      "text": "Owner: legal lead plus security engineer. Action: run license check (S13), OpenSSF Scorecard (S1), and repo recency scan. Confirm an OSI-approved license, Scorecard score above 5, last commit within 90 days, and three or more active maintainers (or a corporate sponsor). Artifact: license review memo with traffic-light status (green / amber / red) per use case. Success criterion: green or amber on every dimension; any red blocks progression to week 2 until the operations leader signs off on the explicit risk acceptance."
    },
    {
      "@type": "HowToStep",
      "name": "Week 2: Security and supply-chain audit.",
      "text": "Owner: security engineer. Action: enable Dependabot alerts plus security updates (S6), CodeQL default setup (S5), and secret scanning with push protection (S5) on a fork or mirror. Verify SLSA L2 build provenance via GitHub Actions artifact attestations (S2, S9). Generate an SBOM that meets CISA minimum elements (S10) and cross-check it against the GitHub Advisory Database (S7). Walk the OWASP CI/CD Top 10 (S3) against the tool's pipeline definitions. Artifacts: SBOM, Scorecard report, OWASP CI/CD Top 10 review. Success criterion: no critical or high-severity advisories that lack a documented mitigation; SBOM completeness validated."
    },
    {
      "@type": "HowToStep",
      "name": "Week 3: Data flow and regulation review.",
      "text": "Owner: Data Protection Officer plus CISO. Action: map every place a prompt, a completion, or a log can travel. Note storage region, encryption posture, and retention period. Draft a GDPR Article 28 Data Processing Agreement if the tool processes personal data of EU residents (S12). Classify the tool against the EU AI Act risk tiers (S11). For financial-services entities, complete a DORA third-party register entry (S15). For non-financial-services teams, use DORA framing as a maturity reference rather than a compliance requirement. Artifacts: data-flow diagram, GDPR DPA (if applicable), EU AI Act risk-tier classification memo, DORA register entry (if applicable). Success criterion: every data destination is documented, encrypted, and either inside the EU or covered by Standard Contractual Clauses."
    },
    {
      "@type": "HowToStep",
      "name": "Week 4: Pilot and governance gate.",
      "text": "Owner: platform lead plus security engineer. Action: deploy to a restricted staging environment with branch protection rules (S5), repository rulesets (S8), CODEOWNERS coverage on critical paths (S14), and least-privilege access for any AI agent that participates. Run OWASP LLM01 prompt-injection tests against repo content and external retrieval surfaces (S4). Exercise rollback at least once during the week so the operations leader has confidence that revert is real, not theoretical. Artifact: pilot evidence report with one row per checklist item plus a rollback timing measurement. Success criterion: all critical checklist items pass; no unmitigated prompt-injection vector; rollback completes inside the team's stated incident-response window."
    },
    {
      "@type": "HowToStep",
      "name": "Post-pilot: Rollback plan and owner assignment.",
      "text": "Owner: platform lead. Action: document the rollback steps in a runbook, assign an ongoing maintenance owner from the technical team, and set a credential rotation cadence (90 days is the cheapest default; 30 days where the tool touches sensitive data). Artifact: rollback / exit plan and credential rotation schedule. Success criterion: exit plan can be executed in under 15 minutes by the on-call engineer who did not run the pilot."
    },
    {
      "@type": "HowToStep",
      "name": "Governance gate.",
      "text": "Review every artifact in a security committee with the CTO, CISO, legal lead, and a representative from the technical team that ran the pilot. Decide one of four outcomes: extend the pilot by two weeks if a single dimension is inconclusive, promote-bounded to a wider pilot in one more repo, reject the tool, or pause-for-fix on a named blocker. Artifact: governance gate decision memo signed by every named role."
    },
    {
      "@type": "HowToStep",
      "name": "Continuous monitoring after promotion.",
      "text": "If the tool is promoted, schedule the OpenSSF Scorecard, the SBOM, and the data-flow diagram for refresh every 90 days. Wire Dependabot alerts to the security team's pager. The checklist is not a one-shot gate; the supply chain it covers shifts every quarter."
    }
  ]
}
</script>
-->