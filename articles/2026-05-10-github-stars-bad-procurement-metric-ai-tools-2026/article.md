---
title: "Why GitHub Stars Are a Bad Procurement Metric for AI Tools"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/github-stars-bad-procurement-metric-ai-tools-2026"
published_date: "2026-05-10"
license: "CC BY 4.0"
---

> **TL;DR:** GitHub stars measure attention, not procurement fitness. Replace them with a license, maintenance, security, and pilot evidence frame.

GitHub stars measure attention, not procurement fitness. A high-star count does not tell you whether a repository has a license, is maintained, or can be safely embedded in your commercial product. Yet many engineering teams, including some at well-run growing software teams and mid-sized companies, still default to "it has X thousand stars" as the primary signal when selecting an open-source AI tool. The buyer moment is the next procurement review, the vendor scorecard discussion, the AI tooling roadmap meeting, or the board-level question on open-source risk. Why this matters: for European scale-ups facing the EU AI Act sandbox milestone on 2 August 2026 (S8), every procurement decision made this quarter will be reviewed under sandbox conditions. If a CTO, a platform engineering lead, an AI transformation team, or a procurement-aware engineering manager keeps the procurement frame anchored on stars, the result is selecting high-attention, high-risk repos like 122k stars with no LICENSE file, or 28k stars with no commits in seven months, while passing over lower-star but safer alternatives that pair an Apache-2.0 license, corporate backing, and active commits. The stakes are concrete: regulatory exposure, litigation risk from unlicensed code, supply-chain compromise, and a quarter of operations leader time spent unwinding a bad pick.

## The problem with using GitHub stars as a buying signal

Stars are a leading indicator of attention, not a lagging indicator of suitability. Attention precedes contribution by months, but procurement needs evidence that a project will survive, be secure, and remain legally usable. The OpenSSF Scorecard (S1) measures contributor diversity, code review, and dependency update tools. Stars correlate poorly with these metrics. A repo can go viral on Hacker News and accumulate 100k stars in a week, yet have zero code review process or security policy. The canonical example is R6: 122k stars, no LICENSE file. Under copyright law, that means no one can use, copy, distribute, or modify the code without risk of litigation (S7). Stars hide that showstopper completely.

For European teams, the problem is compounded by the EU AI Act. By August 2026, every Member State must establish at least one AI regulatory sandbox (S8). Procurement decisions made today will be reviewed under those sandbox conditions. A star-driven selection of a non-compliant or unlicensed component creates governance debt that will surface during sandbox audits.

## What stars are good for and where they fail

Stars are not entirely useless. They signal community interest and can point you toward tools worth investigating. But they fail as a decision input because they conflate popularity with safety, maintenance, and licensing. Forks can indicate active development but can also be cherry-picked. Recent commits and release cadence are stronger signals. Issues and PR health reveal maintainer responsiveness. Security policy (SECURITY.md), SBOM, and license are procurement-grade signals that stars ignore. Customer or community evidence and pilot results are the gold standard.

| Stars vs Procurement Evidence | |
|---|---|
| Signal | Procurement value (low / medium / high) and reasoning |
| Stars | Low. Attention is not procurement fitness. A repo can have 122k stars and no license (R6) or be stale for 7 months (R5). |
| Forks | Low to medium. Forks can indicate active use, but many are copies with zero changes. Check the origin of the most popular fork. |
| Recent commits | Medium to high. Commits in the past month signal maintenance. R3 (31k stars) has recent commits; R5 (28k stars) does not. |
| Releases | High. Tagged releases indicate stability and versioning. Compare with SLSA build provenance (S3). |
| Issues / PR health | High. Closed vs open ratio, median response time, and PR merge latency reveal maintainer capacity. |
| Security policy (SECURITY.md) | High. Required for responsible vulnerability disclosure. Part of the GitHub security baseline (S5). |
| SBOM / provenance | High. SBOM (S10) gives transparency into dependencies. SLSA L2 or L3 (S3) verifies build integrity. |
| License | High. Determines legal usability. R2 (MIT), R3 (Apache-2.0) are safe. R6 (no license) and R7 (non-OSI) require legal review. |
| Customer / community evidence | High. Case studies, enterprise testimonials, or active community discussions on security. |
| Pilot result | Highest. A controlled 30-day pilot with exit criteria (see below) is the only true measure of fit. |

## The procurement signals that actually matter

Procurement for AI tools must move beyond star counts to a multi-signal framework. The signals that matter cluster into three categories: **legal**, **operational**, and **security**. Each category has its own gate, its own owner inside the organization, and its own evidence type. A finance team will recognize this shape from any vendor scorecard exercise; the difference for AI tooling is that license risk and supply-chain risk now sit at the top of the matrix instead of pricing.

**Legal.** The license is the most common blocker. Per S7, no license means default copyright applies, which is a hard pass for any commercial use. The 122k-star repo with no LICENSE file is the canonical trap: the star count masks an unusable artifact. Non-OSI licenses such as the Sustainable Use License (n8n) or Dify's restricted license are valid open-source licenses but require legal review against your specific business model before commercial embedding or hosted-service deployment. Star counts tell you none of this. The license file does. A one-page legal memo per pilot is cheap insurance.

**Operational.** Maintenance health is the second blocker. A repo with no commits in six months should not enter production regardless of star count, because security patches lag and dependencies bit-rot fast. Check three operational signals together: commit recency (last 90 days is the floor for a pilot), release cadence (monthly or quarterly tagged releases indicate versioning discipline), and maintainer count (three or more active contributors, or one with corporate backing, survives a single departure). The OpenSSF Scorecard (S1) bakes contributor-diversity, code-review, and dependency-update-tools checks into its 0-10 score; consult the score before you run the pilot. Dependabot alerts (S4) on the repository show whether the project is responding to advisory-database entries within a reasonable window.

**Security.** The GitHub repo security quickstart (S5) defines a five-feature minimum: dependency graph, Dependabot alerts plus automatic security updates, CodeQL default setup, secret scanning with push protection, and a published SECURITY.md disclosure policy. SLSA build levels (S3) define the build-provenance bar: L0 is dev-only, L1 is trivially forgeable, L2 is the practical procurement minimum (hosted build platform with cryptographic signing), and L3 is the hardened bar for high-stakes use. SBOM (S10) is the dependency-transparency bar; CISA SBOM minimum-elements guidance is increasingly cited in EU Cyber Resilience Act conversations. For European teams, the data-flow question is decisive under the EU AI Act (S8): where do prompts, completions, and logs go? Self-hosting (where supported) reduces residency risk; cloud-only AI tools need a documented residency posture before pilot, not after.

## A practical AI tool evaluation scorecard

The following scorecard condenses the signals into a table your team can use during vendor assessment or tool selection.

| AI Tool Procurement Scorecard | | | | |
|---|---|---|---|---|
| Signal | Why it matters | What to check | Red flag | Decision impact |
| License | Determines legal usability and commercial embeddability. | Check the LICENSE file. Is it OSI-approved? (S7) | No LICENSE file (R6) or non-OSI license (R7, R8) without legal review. | Hard pass if no license. Requires legal review for non-OSI. |
| Maintainer health | Indicates long-term viability. | How many active maintainers? Are issues and PRs closed regularly? (S1, Scorecard contributor-diversity) | Single maintainer or repo abandoned for 6+ months (R5). | High risk of no support or security patches. |
| Release cadence | Shows versioning discipline and bug fix frequency. | Check the Releases page. Are there recent releases? Are they semantically versioned? | No releases in 6+ months or all releases are pre-release. | Stale projects may have unpatched vulnerabilities. |
| Security posture | Protects your supply chain and user data. | Does the repo have a SECURITY.md? Are Dependabot alerts enabled? (S5) | No security policy, no vulnerability reporting path. | You will be blind to vulnerabilities. |
| Dependency risk | Every dependency is a potential attack vector. | Use Dependabot to inspect the dependency graph. (S4, S9) | Many outdated or unmaintained dependencies. | Increased attack surface. |
| Data flow | Determines regulatory compliance (EU AI Act, GDPR). | Where do prompts, outputs, and logs go? Can it be self-hosted? (S8) | Cloud-only with no data residency option or unclear data processing terms. | Non-compliance risk. |
| Enterprise support | Critical for production incidents. | Is there a company backing the project? Are there paid support options? | No company, no forum, no SLA. | You are on your own if something breaks. |
| Integration fit | Reduces engineering cost. | Does it plug into your existing stack (e.g., Kubernetes, GitHub Actions, observability tools)? | Requires custom integration work or replaces core infrastructure. | High migration cost. |
| Observability | Essential for monitoring and debugging. | Does it expose metrics, logs, or traces? Can it be monitored with your existing tools? | No observability hooks or black-box behavior. | Hard to diagnose issues in production. |
| Reversibility / exit path | Avoids vendor lock-in. | Can you export data, models, or configurations? Is there an alternative? | Proprietary format, no export mechanism. | High switching cost. |

## How to run a 30-day pilot without creating governance debt

A pilot is the only way to validate procurement signals before committing to production. Follow these seven steps to run a controlled, low-risk evaluation.

1. Define exit criteria: Write down what success looks like. Example: "The tool must integrate with our existing CI/CD pipeline without modifying our security controls." Owner: Engineering Lead. Success criterion: All criteria met at day 30.

1. Set up a sandbox environment: Use a dedicated namespace in your Kubernetes cluster or a separate cloud subscription. Do not connect to production data. Owner: Platform Engineer. Success criterion: Isolated environment with network policies.

1. Review data flow: Document where prompts, outputs, and logs travel. Check against OWASP LLM01 (S6) prompt injection mitigations. For European teams, verify data residency against the EU AI Act sandbox requirements (S8). Owner: Security Engineer. Success criterion: Data flow diagram with risk assessment.

1. Run the security baseline: Execute the OpenSSF Scorecard (S1) on the repo and its dependencies. Generate an SBOM using a tool like Syft. Owner: DevOps Lead. Success criterion: Scorecard score above 7.0, SBOM produced.

1. Test integration: Connect the AI tool to your staging environment. Verify that it works with your existing identity provider, API gateway, and monitoring. Owner: Integration Engineer. Success criterion: Integration completes without errors and produces observability data.

1. Conduct a load test: Simulate production traffic to measure latency, throughput, and resource consumption. Owner: SRE Lead. Success criterion: Tool meets performance SLAs under 2x expected load.

1. Document lessons and decide: Compile findings against exit criteria. Present to the procurement team. Owner: Engineering Manager. Success criterion: Go/no-go decision with rationale.

If you need help structuring your AI readiness process, consider our AI Readiness Assessment at https://radar.firstaimovers.com/page/ai-readiness-assessment or consult with our team at https://radar.firstaimovers.com/page/ai-consulting.

## What not to automate yet

Some repos are attractive because of their star count but carry risks that automation cannot mitigate. A founder-led company shipping fast is especially exposed here, because the cost of unwinding a star-driven choice falls on the same small technical team that picked it. The avoid bucket from the example set illustrates three concrete risk classes.

- **Abandoned but popular.** stanford-oval/storm (28k stars, last commit September 2025) is the canonical "stars do not decay, but code does" pattern. Seven months without a push, in an ecosystem where dependencies and model interfaces shift quarterly, is a liability. Automating the use of a stale repo, even one with strong stars, exposes the engineering leader running the procurement to security drift, dependency vulnerabilities the maintainer has not patched, and the eventual hard fork. Do not embed an unmaintained dependency in production, period.

- **Licenseless landmine.** forrestchang/andrej-karpathy-skills (122k stars, no LICENSE file) is the highest-star example in the set and the one that fails procurement on the first gate. Per S7, default copyright applies, which means no permission to use, modify, or distribute. Any commercial deployment of a no-license repo creates a litigation surface that no amount of star-count enthusiasm covers. Stars do not just fail to flag this risk; they actively obscure it by signalling community confidence the legal facts do not support.

- **Non-OSI licenses without legal review.** n8n-io/n8n (Sustainable Use License) and langgenius/dify both have very high star counts and restricted licenses that are valid but limit hosted-service redistribution and commercial embedding. The license is on the repo; the analysis is in your legal team's memo. Skip the memo and you are guessing at compliance with a non-OSI clause that lawyers, not engineers, are paid to read.

General anti-patterns to avoid, applicable across coding agents, vector databases, MCP servers, and AI app builders:

- **Star-first filtering.** Using a star threshold as the first filter. Replace it with: (1) license check, (2) commit-recency check, (3) Scorecard score per S1.
- **Ignoring dependency depth.** Building on a tool whose own dependency graph is hundreds of packages deep. Generate an SBOM per S10 before pilot, scan it against the GitHub Advisory Database (S9), and document any unresolved high-severity items in the pilot's data-flow review.
- **Assuming corporate backing means safety.** A vendor-backed tool can still ship without a clean license file, without SLSA L2 conformance, or without a SECURITY.md. The presence of a logo on the README is not a substitute for the procurement scorecard above.
- **Granting an AI agent merge or release authority.** Per S6 OWASP LLM01, indirect prompt injection from repo content can subvert an autonomous agent. The merge button must remain policy-controlled regardless of which AI tool the team adopts, and regardless of how many stars that tool has.

## A better decision rule for engineering leaders

Replace "we picked this because it has 100k stars" with a decision rule that balances attention signals with procurement evidence. Here is a simple rule that fits on a slide:

1. **Legal gate**: Does the repo have a license that permits commercial use? (If no license, hard pass. If non-OSI, legal review.)
2. **Security gate**: Does the repo pass the GitHub security baseline? (S5: dependency graph, Dependabot alerts, CodeQL, secret scanning, SECURITY.md.)
3. **Maintenance gate**: Has the repo had a commit or release in the last 90 days? (If no, deprioritize.)
4. **Evidence gate**: Has at least one positive pilot or community reference? (Pilot result is highest evidence.)
5. **Decision**: If all gates pass, proceed to a 30-day pilot with exit criteria. If any gate fails, require a mitigation plan before moving forward.

This rule puts stars in their proper place: a weak but useful signal for discovery, not decision. For European teams, the sandbox milestone (August 2026) means that every AI tool procurement should be justifiable under the EU AI Act's transparency and documentation requirements. A star count is not justifiable. A pilot report with scorecard results is.

## Frequently Asked Questions

### Q: Are stars completely useless?

No. Stars are a useful but weak market signal. They indicate community interest and can help you discover tools worth investigating. But they fail as a procurement signal because they conflate attention with safety, maintenance, and licensing. Treat stars as a discovery filter, not a decision input.

### Q: How many stars is enough to take a tool seriously?

There is no magic number. A tool with 1k stars that is actively maintained, licensed, and used in production by similar companies is more credible than a 100k-star repo that is stale or unlicensed. Use stars to get on the radar, then apply the evaluation scorecard.

### Q: Should European teams care about SLSA and SBOM right now?

Yes. SLSA L2 or L3 (S3) is becoming the procurement bar for build provenance. SBOM (S10) is becoming the procurement bar for dependency transparency. The EU AI Act and the upcoming Cyber Resilience Act increase the likelihood that these will become regulatory requirements. European teams that start collecting SBOMs today will be ahead of compliance deadlines.

### Q: What replaces 'we picked this because it has 100k stars' in a procurement memo?

"We selected this tool because it passed all gates in our procurement scorecard. The license allows commercial use, the maintainer team is active, security posture is verified by OpenSSF Scorecard, a 30-day pilot met our exit criteria, and the tool runs self-hosted with documented data flows." That is what a procurement memo should contain.

### Q: How long should a pilot run before a production decision?

30 days is the standard minimum. This allows one full iteration cycle: setup, integration testing, load testing, and evaluation. Extend to 60 days if the tool involves significant data migration or if you need to validate compliance in an EU AI Act sandbox.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Why GitHub Stars Are a Bad Procurement Metric for AI Tools",
  "description": "GitHub stars measure attention, not procurement fitness. Replace them with a license, maintenance, security, and pilot evidence frame.",
  "datePublished": "2026-05-10T11:28:13.901976+00:00",
  "dateModified": "2026-05-10T11:28:13.901976+00:00",
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
    "@id": "https://radar.firstaimovers.com/github-stars-bad-procurement-metric-ai-tools-2026"
  },
  "image": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1200&h=630&fit=crop&q=80",
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
      "name": "Q: Are stars completely useless?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Stars are a useful but weak market signal. They indicate community interest and can help you discover tools worth investigating. But they fail as a procurement signal because they conflate attention with safety, maintenance, and licensing. Treat stars as a discovery filter, not a decision input."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How many stars is enough to take a tool seriously?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "There is no magic number. A tool with 1k stars that is actively maintained, licensed, and used in production by similar companies is more credible than a 100k-star repo that is stale or unlicensed. Use stars to get on the radar, then apply the evaluation scorecard."
      }
    },
    {
      "@type": "Question",
      "name": "Q: Should European teams care about SLSA and SBOM right now?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. SLSA L2 or L3 (S3) is becoming the procurement bar for build provenance. SBOM (S10) is becoming the procurement bar for dependency transparency. The EU AI Act and the upcoming Cyber Resilience Act increase the likelihood that these will become regulatory requirements. European teams that sta..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: What replaces 'we picked this because it has 100k stars' in a procurement memo?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": ""We selected this tool because it passed all gates in our procurement scorecard. The license allows commercial use, the maintainer team is active, security posture is verified by OpenSSF Scorecard, a 30-day pilot met our exit criteria, and the tool runs self-hosted with documented data flows." Th..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How long should a pilot run before a production decision?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "30 days is the standard minimum. This allows one full iteration cycle: setup, integration testing, load testing, and evaluation. Extend to 60 days if the tool involves significant data migration or if you need to validate compliance in an EU AI Act sandbox."
      }
    }
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "Why GitHub Stars Are a Bad Procurement Metric for AI Tools",
  "description": "GitHub stars measure attention, not procurement fitness. Replace them with a license, maintenance, security, and pilot evidence frame.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Legal gate",
      "text": "Does the repo have a license that permits commercial use? (If no license, hard pass. If non-OSI, legal review.)"
    },
    {
      "@type": "HowToStep",
      "name": "Security gate",
      "text": "Does the repo pass the GitHub security baseline? (S5: dependency graph, Dependabot alerts, CodeQL, secret scanning, SECURITY.md.)"
    },
    {
      "@type": "HowToStep",
      "name": "Maintenance gate",
      "text": "Has the repo had a commit or release in the last 90 days? (If no, deprioritize.)"
    },
    {
      "@type": "HowToStep",
      "name": "Evidence gate",
      "text": "Has at least one positive pilot or community reference? (Pilot result is highest evidence.)"
    },
    {
      "@type": "HowToStep",
      "name": "Decision",
      "text": "If all gates pass, proceed to a 30-day pilot with exit criteria. If any gate fails, require a mitigation plan before moving forward."
    }
  ]
}
</script>
-->