---
title: "Should Your Maintainer Health Rubric Change by Dependency Tier?"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/tune-maintainer-health-rubric-thresholds-dependency-tier-2026"
published_date: "2026-05-11"
license: "CC BY 4.0"
---

> **TL;DR:** Tier your open-source maintainer health rubric by dependency blast radius and replaceability to meet EU AI Act and DORA conformity expectations.

No, a single maintainer-health threshold does not work for every dependency. The verdict: you must tier your rubric by dependency impact level. Why this matters: a one-size rubric discards critical risk signals for runtime AI frameworks while overblocking harmless developer tools, wasting CTO and platform engineering lead time. With the EU AI Act regulatory sandbox deadline on 2 August 2026 (S7), European scale-ups must defend their dependency decisions with documented, risk-based evidence. This article shows how CTOs, platform engineering leads, AI transformation leads, procurement-aware engineering managers, and security leads can build a tiered maintainer health rubric that aligns with EU AI Act and DORA compliance.

## The short answer

Yes, your maintainer health rubric must change by dependency tier. A single threshold for bus factor, release recency, or security coverage is too blunt. The same signal means different things depending on blast radius, replaceability, data access, and deployment path. A single-maintainer build-chain dev tool is not equivalent to a single-maintainer runtime model-serving framework. The rubric should define per-tier thresholds, then gate adoption decisions accordingly. A failing rubric at a higher tier blocks adoption; at a lower tier it warns and routes to manual review.

## Why this matters for European scale-ups

European scale-ups, mid-sized companies, and founder-led software teams of 20 to 50 engineers face dual regulatory pressure. The EU AI Act (S7) requires conformity assessments for high-risk AI systems, and DORA (S11) imposes third-party risk management on critical ICT dependencies. Both demand evidence that your dependency decisions are risk-based and documented. A flat rubric (for example, requiring two maintainers and a 90-day release for every package) does not satisfy a regulator. You need a tiered policy that shows you calibrated thresholds to blast radius, replaceability, and data sensitivity. For CTOs and security leads, this is the difference between a rubber stamp and a defensible procurement log.

## Why one threshold across all dependencies breaks at scale-up

At 20 dependencies, a single threshold works. At 200 (typical for a scale-up using AI tooling), it breaks. Build-chain linters fail the bus-factor gate, forcing wasteful manual reviews. Meanwhile, a runtime-critical inference framework with one maintainer passes the same gate because it has frequent releases, hiding true risk. The problem is not the rubric; it is the assumption that all dependencies are equal. OpenSSF Scorecard (S1) gives you contributor-diversity, code-review, maintained, dependency-update-tool, and signed-releases as automatable signals, but these signals must be weighted differently per tier. License clarity is a hard gate at every tier: no license means default copyright (S6), making enterprise commercial use unsafe. A tiered rubric encodes these distinctions.

The OWASP CI/CD Top 10 (S8) frames the threat model that motivates tiering. Two of the ten top risks (CICD-SEC-3 dependency chain abuse and CICD-SEC-6 insufficient credential hygiene) hit build-chain dependencies harder than developer-only ones; conversely, CICD-SEC-1 insufficient flow control and CICD-SEC-7 insecure system configuration hit runtime-critical paths harder. A flat rubric treats both clusters the same and either over-blocks the harmless side or under-protects the dangerous one. Tiering aligns the strength of the gate with the threat surface the OWASP catalogue actually names. For AI runtime stacks, OWASP LLM Top 10 (S14) adds a layer the build-chain piece does not see: prompt-injection-class risks, training-data poisoning, and model denial-of-service, each of which sits inside the runtime-critical tier and demands stricter signed-release and SBOM coverage than a non-AI runtime library at the same tier would need.

## The six dependency tiers

1. **Runtime-critical**: dependencies that ship in production, serve user requests, or process sensitive data. Blast radius: full system compromise. Replaceability: very low. Gates: maximum rigor on all signals.
2. **Security-sensitive**: dependencies that handle authentication, encryption, or network security. Similar blast radius to runtime-critical but often narrower scope. Replaceability: low.
3. **Build-chain**: dependencies used during build, test, or CI, but not present in production. Blast radius: supply-chain injection. Replaceability: moderate (can pin versions or fork).
4. **Developer-only**: dependencies used on dev machines, not in CI or production. Blast radius: local developer environment. Replaceability: high.
5. **Experimental**: dependencies used for prototyping or research, with no production path. Blast radius: limited to notebook or sandbox. Replaceability: very high.
6. **Replaceable**: libraries with multiple mature alternatives, minimal unique functionality. Blast radius: low. Replaceability: immediate swap.

## The dependency-tier matrix

| Tier | Blast radius if compromised | Replaceability | Suggested release-recency floor | Suggested bus-factor floor | License gate | SBOM/SLSA required |
|------|----------------------------|----------------|----------------------------------|----------------------------|--------------|--------------------|
| Runtime-critical | Full production compromise | Very low | Last 30 days | 2+ maintainers, 2+ orgs | Must be permissive or LGPL with explicit patent grant | Yes (SBOM + SLSA L1+) |
| Security-sensitive | Compromise of auth/crypto | Low | Last 60 days | 2+ maintainers, 1+ org | Must be permissive | Yes (SBOM + SLSA L1 recommended) |
| Build-chain | Supply-chain injection | Moderate | Last 90 days | 1+ maintainer | Must be permissive or GPL with known terms | SBOM recommended, SLSA optional |
| Developer-only | Local dev machine | High | Last 180 days | 1+ maintainer | Any license acceptable if cleared | Optional |
| Experimental | Notebook/sandbox | Very high | Last 365 days | 0+ maintainers | Any license, but note in risk log | Not required |
| Replaceable | Low | Immediate swap | Last 365 days | 1+ maintainer | Any license, but prefer known | Not required |

## Worked example: applying the matrix to a real dependency tree

Consider three illustrative dependencies in a typical AI scale-up stack:

- **Runtime LLM-serving framework**: sits in production, handles user prompts, accesses model weights. This is runtime-critical. The tier classifier checks: does data flow through it? Is it in the critical path? Yes. Thresholds: release within 30 days, bus factor 2+, permissive license, SBOM and SLSA required. The rubric queries GitHub REST API for release recency (S2), contributors (S2), CODEOWNERS (S10) for merge control, OpenSSF Scorecard (S1) for maintenance signal. If any check fails, adoption is blocked. For example, if the framework has a single maintainer (bus factor 1), the rubric blocks automatically, triggering a risk review. For AI-specific risk, OWASP LLM Top 10 (S14) prompt-injection and training-data poisoning are flagged as items the rubric cannot itself test; the framework's documentation, model-card, and incident-response history are required as compensating evidence before the security lead signs off.

- **Build-time linter**: used only in CI, not packaged in production. This is build-chain. The tier classifier asks: does it run in deployment pipeline? Is it ephemeral? Yes. Thresholds: release within 90 days, bus factor 1+, permit any license but verify, SBOM recommended but not required. The rubric passes a single-maintainer linter with infrequent releases, but flags it for manual review if the maintainer has no recent activity or if there are unaddressed advisories (S5). Dependabot (S12) monitors for vulnerabilities, but the severity threshold is relaxed: only critical or high blocking advisories trigger a fail.

- **Experimental research notebook**: used by a data scientist for ad-hoc model evaluation, not in production. This is experimental. The tier classifier asks: is it on the production path? Is it replaceable? Yes. Thresholds: release within 365 days, no bus factor requirement, any license as long as noted in risk log. The rubric warns but does not block. The team documents the risk and moves on. This tier saves hours of review time compared to treating it as runtime-critical.

## A 30-day implementation plan

**Days 1 to 7: tier inventory and dry-run scoring against your top 20 dependencies.** The platform engineering lead and security lead collaborate to classify the top 20 dependencies using the six-tier model. The CTO approves the classification criteria. For each dependency, run a dry-run score using OpenSSF Scorecard (S1), GitHub contributor stats (S2), release recency (S2), advisory checks (S5), and license verification (S6). Record what the tiered rubric would decide versus your current flat rubric. Expect mismatches: that is the point.

**Days 8 to 21: CI integration: tier metadata + tiered thresholds.** The platform engineering lead embeds tier metadata into your dependency management system. Each dependency gets a `tier` field in its config file or database. Then configure CI scripts to apply tier-specific thresholds. Use the OpenSSF Scorecard GitHub Action to pull scores and compare against per-tier pass/fail rules. For example, for runtime-critical: require score >= 7 on maintained, code-review, contributor-diversity, signed-releases. For build-chain: require >= 5 on maintained and code-review. Use Dependabot (S12) for security patching, but tier its alert severity: runtime-critical blocks on any open advisory; build-chain blocks only on critical/high. The AI transformation lead can automate the scoring for common Python/JavaScript AI packages using a lookup table.

**Days 22 to 30: procurement handoff: link rubric output to risk-class register.** The procurement-aware engineering manager maps the rubric output to your existing risk-class register. The handoff itself takes roughly two working days for a 100-dependency inventory: half a day to define the tier-to-risk-class mapping, half a day to load the existing dependency tags into the register, and one full day to dry-run the first five procurement requests against the new evidence shape so that finance and security have aligned expectations. Each tier corresponds to a risk level: runtime-critical = high risk, security-sensitive = medium-high, build-chain = medium, developer-only = low, experimental = minimal, replaceable = negligible. The security lead updates the third-party risk policy to require the rubric evidence for any new dependency approval. The CTO reviews the first five procurement requests to validate the process. This handoff ensures that every new dependency has a documented risk-based rationale, satisfying EU AI Act and DORA audit trails.

## What you can automate safely today

- **OpenSSF Scorecard signals**: contributor-diversity, code-review, maintained, dependency-update-tool, signed-releases (S1). These are fully automatable via GitHub Actions.
- **Release recency and bus factor**: pull from GitHub REST API repos endpoint (S2) and contributor stats. Easy to script in CI.
- **License detection**: use tools like `licensee` or GitHub's API to verify presence. No license means default copyright (S6) and must block at tiers 1-3.
- **Advisory scanning**: GitHub Advisory Database (S5) and Dependabot (S12) cover known vulnerabilities. Automate severity-based alerts per tier.
- **SBOM generation and SLSA attestation**: tools like `syft` and `slsa-verifier` can be integrated in CI for runtime-critical and security-sensitive tiers (S13, S9).
- **CODEOWNERS check**: use the GitHub API to verify that the repository has CODEOWNERS set for relevant files (S10). Combine with contributor stats for bus factor.

## What must remain human-reviewed (and what not to automate yet)

1. Do not automate the final decision to block or allow a dependency when the rubric yields a borderline result. Manual review by the security lead or platform lead is required for all tier 1 and 2 failures.
2. Do not let tier classification become a substitute for security review of model weights, training data, or supply-chain integrity beyond the repo.
3. Do not automate classification for dependencies with ambiguous scope; always require a human to confirm the tier.
4. Do not automate the handling of dependencies with a single maintainer who has not responded to published advisories within 30 days; that requires human escalation.
5. Do not rely solely on release recency for non-maintained projects; check the issue tracker (S3) and pull requests (S4) for signs of life.
6. Do not automate exceptions for build-chain dependencies that have access to production secrets; that is a tier-misclassification bug.

## How tier classification interacts with EU AI Act and DORA

Tiered evidence directly supports EU AI Act (S7) conformity assessments. The Act requires that high-risk AI systems demonstrate a risk management process. By documenting that you classify dependencies by tier and apply proportional thresholds, you show the regulator that your risk decisions are systematic and documented. For each tier, the rubric output maps to a risk level that aligns with the Act's high-risk vs limited-risk classifications. The regulator can inspect your rubric logs to see why a runtime-critical dependency was accepted (e.g., because it passed all gates) or flagged (e.g., because bus factor threshold failed). This is stronger than a flat policy: it proves you considered blast radius and replaceability.

For DORA (S11), Article 28 on third-party risk reporting consumes tier metadata directly. Your ICT risk management framework must classify critical third-party dependencies. The tier rubric produces exactly that classification. You can report that runtime-critical and security-sensitive dependencies have passed SLSA L1 (S13) and SBOM minimum elements (S9), while developer-only dependencies are excluded from criticality assessment. This simplifies the reporting burden for the CTO, the security lead, the operations leader, and the finance team that signs off on the compliance budget.

A concrete walk-through. A 30-person engineering scale-up with a mid-sized B2B SaaS product runs through this in roughly half a day on the first dependency cohort. The CTO classifies the 5 dependencies sitting on the production inference path as runtime-critical. The security lead classifies the 12 dependencies that touch authentication, encryption, or external network calls as security-sensitive. The platform engineering lead classifies the 40 build-chain dependencies (linters, test runners, type checkers, schema validators) as build-chain. The AI transformation lead classifies the 8 research-notebook libraries the data team uses as experimental. The procurement-aware engineering manager classifies the 30 developer-only utilities (formatters, local dev servers, IDE-specific helpers) as developer-only. Total tagged: 95 of 120 dependencies. The remaining 25 are flagged as ambiguous and routed to the security lead for one-pass human classification. That single afternoon produces the metadata that every downstream CI gate, EU AI Act file, and DORA Article 28 report can reuse.

If you are not confident your team can structure this process, start with our [AI Readiness Assessment](https://radar.firstaimovers.com/page/ai-readiness-assessment) or explore how our [AI Consulting](https://radar.firstaimovers.com/page/ai-consulting) team can operationalize tiered rubric design within 30 days.

## Limits and failure modes

Tiered rubrics fail if the classification itself is wrong. Misclassifying a runtime-critical dependency as build-chain can lead to under-scrutiny and a supply-chain attack. Common failure modes: dependencies that straddle tiers (a library used in both production CI and development), dependencies that change tier after release (a research tool that gets promoted to production), and dependencies with no clear owner (orphaned projects). Also, the rubric cannot detect zero-day vulnerabilities; it only measures maintainer health and known security posture. Finally, bus factor thresholds based on GitHub contributor stats can be misleading if the real maintainers work in private repos.

A second class of failure is operational. Tiering adds metadata to your dependency graph, and that metadata can rot. A package that was experimental in week 1 quietly becomes runtime-critical by week 12 because someone wired it into the inference path; if the tier tag never updated, the rubric still applies experimental-tier thresholds and the project's risk surface grows without anyone noticing. Schedule a quarterly tier-reclassification review and an event-driven re-tier on any change to the production import graph. The platform engineering lead owns the schedule; the security lead owns the event-driven trigger.

A third class is human. Engineers under shipping pressure will downgrade a tier to make a rubric pass. This is the easiest failure to miss because the rubric still returns green. Mitigations: keep tier downgrades inside a one-way log (append-only) so post-hoc audit can flag any pattern; require a second approver for runtime-critical-to-build-chain downgrades; surface tier-downgrade events in the publishing-control-tower-equivalent platform analyst lane so the CTO sees them in routine review. Combine those with mandatory SLSA attestations (S13) for the top two tiers to reduce impersonation risk and you have a rubric whose failure modes are observable, even when individual decisions are wrong.

## Frequently Asked Questions

- **Q: How do I assign a tier to a new dependency in CI?** A: Automatically by checking its runtime scope: is it imported in production code? Does it touch sensitive data? Is it in the Docker image? Use a script that interrogates your dependency graph and assigns a provisional tier, then human-review for edge cases.
- **Q: Should one project be in two tiers at once?** A: Yes, if it is used in multiple contexts. For example, a logging library used in both production and development-only scripts. In that case, assign the higher tier for the most sensitive use. Document both usages in the risk register.
- **Q: Does tiering replace a security review?** A: No. Tiering is a triage step. It gates which dependencies get full security review (tier 1-2) versus lighter review (tier 3-4) versus accepted risk (tier 5-6). Security review depth scales with tier.
- **Q: How does tiering interact with EU AI Act risk classes?** A: Align yours: runtime-critical and security-sensitive tiers correspond to high-risk AI system dependencies, which require conformity assessment artifacts including tier classification logs. Lower tiers map to limited or minimal risk, reducing documentation burden.
- **Q: Can a single-maintainer project ever pass the runtime-critical tier?** A: It can pass only if the rubric exception process approves it with compensating controls: forking the repo, mirroring with signed releases, and continuous security monitoring. The rubric initially blocks, then a human review can override with documented risk acceptance.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Should Your Maintainer Health Rubric Change by Dependency Tier?",
  "description": "Tier your open-source maintainer health rubric by dependency blast radius and replaceability to meet EU AI Act and DORA conformity expectations.",
  "datePublished": "2026-05-11T07:23:49.020366+00:00",
  "dateModified": "2026-05-11T07:23:49.020366+00:00",
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
    "@id": "https://radar.firstaimovers.com/tune-maintainer-health-rubric-thresholds-dependency-tier-2026"
  },
  "image": "https://images.unsplash.com/photo-1560472355-536de3962603?w=1200&h=630&fit=crop&q=80",
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
  "name": "Should Your Maintainer Health Rubric Change by Dependency Tier?",
  "description": "Tier your open-source maintainer health rubric by dependency blast radius and replaceability to meet EU AI Act and DORA conformity expectations.",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Runtime-critical",
      "text": "dependencies that ship in production, serve user requests, or process sensitive data. Blast radius: full system compromise. Replaceability: very low. Gates: maximum rigor on all signals."
    },
    {
      "@type": "HowToStep",
      "name": "Security-sensitive",
      "text": "dependencies that handle authentication, encryption, or network security. Similar blast radius to runtime-critical but often narrower scope. Replaceability: low."
    },
    {
      "@type": "HowToStep",
      "name": "Build-chain",
      "text": "dependencies used during build, test, or CI, but not present in production. Blast radius: supply-chain injection. Replaceability: moderate (can pin versions or fork)."
    },
    {
      "@type": "HowToStep",
      "name": "Developer-only",
      "text": "dependencies used on dev machines, not in CI or production. Blast radius: local developer environment. Replaceability: high."
    },
    {
      "@type": "HowToStep",
      "name": "Experimental",
      "text": "dependencies used for prototyping or research, with no production path. Blast radius: limited to notebook or sandbox. Replaceability: very high."
    },
    {
      "@type": "HowToStep",
      "name": "Replaceable",
      "text": "libraries with multiple mature alternatives, minimal unique functionality. Blast radius: low. Replaceability: immediate swap."
    }
  ]
}
</script>
-->