# Summary Review — Open-Source AI Tool Security Checklist for European Scale-Ups

Article folder: 2026-05-10-open-source-ai-tool-security-checklist-european-scale-ups-2026
Canonical URL: https://radar.firstaimovers.com/open-source-ai-tool-security-checklist-european-scale-ups-2026
Generated at: 2026-05-31
Model: manual / human editorial draft from source article text

## 50-word summary

A 22-item security checklist replaces star-count procurement for European scale-ups evaluating open-source AI tools. Seven signal categories separate attention from maintenance, security, license, data flow, deployment, and vendor support. A four-week workflow produces named artefacts that satisfy EU AI Act, GDPR Article 28, and DORA third-party-vendor reviews from a single pass.

## 200-word summary

Star counts hide license risk, maintenance risk, and supply-chain risk. The article gives European scale-ups a 22-item security checklist for open-source AI tools, organised by seven signal categories that must be read separately: attention, maintenance, security, license, data flow, deployment and control, and support and vendor. Stars sit only in the attention column. The checklist's mandatory items are license clarity (no LICENSE means default copyright and a hard pass), maintenance recency in the last 90 days, OpenSSF Scorecard above 5, SBOM generation, a documented data-flow review, and an EU AI Act risk-tier classification memo. A four-week workflow assigns owners and named artefacts to each phase: legal and initial triage in week one, security and supply-chain audit (Dependabot, CodeQL, secret scanning, SLSA L2 provenance, SBOM against CISA minimum elements, OWASP CI/CD Top 10) in week two, data-flow and regulation review (GDPR Article 28 DPA, EU AI Act tier classification, DORA register entry where applicable) in week three, pilot and governance gate (branch protection, rulesets, CODEOWNERS, OWASP LLM01 prompt-injection battery, exercised rollback) in week four. The default decision is "do not promote without evidence." Continuous monitoring refreshes the artefacts every 90 days after promotion.

## 500-word summary

Star counts hide license risk, maintenance risk, and supply-chain risk. The article gives European scale-ups a 22-item security checklist that replaces star-count procurement for open-source AI tools and a four-week workflow that produces the named artefacts an EU AI Act sandbox audit, a GDPR Article 28 review, or a DORA third-party register update will ask for.

The seven signal categories must be read separately. Attention covers stars, watchers, and community interest — necessary for discovery, never sufficient for procurement. Maintenance covers last-commit date, release cadence, maintainer count, and bus factor; the floor is a commit in the last 90 days and at least two active maintainers. Security covers OpenSSF Scorecard, SECURITY.md, Dependabot alerts, secret scanning with push protection, and CodeQL default setup. License covers OSI approval and any non-OSI commercial-use clauses that need legal review. Data flow covers where prompts, completions, and telemetry travel and whether third-party API calls happen by default. Deployment and control covers self-hosting support, branch protection, repository rulesets, and SLSA provenance for build integrity. Support and vendor covers commercial backing, paid-support availability, and community size.

The 22-item checklist mandates the high-impact gates: license clarity, OSI approval, last-commit recency, maintainer count and bus factor, OpenSSF Scorecard above 5, SECURITY.md, Dependabot, secret scanning, CodeQL, SBOM generation, SLSA L2 build provenance, dependency-graph cross-check against the GitHub Advisory Database, CODEOWNERS coverage on critical paths, branch protection and rulesets, OWASP CI/CD Top 10 mitigations, OWASP LLM01 prompt-injection mitigations, data-flow review, GDPR Article 28 DPA where applicable, EU AI Act risk-tier classification memo, DORA third-party-vendor coverage for financial-services entities, a documented rollback plan, and a credential-rotation cadence.

The four-week workflow assigns clear ownership. Week one is legal lead plus security engineer: license check, Scorecard, recency scan, traffic-light memo. Week two is security engineer: enable Dependabot and CodeQL and secret scanning on a fork or mirror, verify SLSA L2 build provenance via Actions artefact attestations, generate an SBOM that meets CISA minimum elements, walk OWASP CI/CD Top 10 against the tool's pipeline definitions. Week three is the Data Protection Officer plus the CISO: map every prompt, completion, and log destination, draft a GDPR Article 28 DPA if personal data of EU residents is processed, classify against EU AI Act tiers, complete a DORA register entry for financial-services entities. Week four is platform lead plus security engineer: deploy to a restricted staging environment with branch protection, rulesets, CODEOWNERS, and least-privilege agent access, run an OWASP LLM01 prompt-injection battery, exercise rollback at least once so revert is real, not theoretical, and produce a pilot evidence report.

The governance gate decides one of four outcomes: extend, promote-bounded, reject, or pause-for-fix. After promotion, the OpenSSF Scorecard, the SBOM, and the data-flow diagram refresh every 90 days; Dependabot alerts wire into the security team's pager. The checklist is not a one-shot gate.

## Review status

Status: approved
Reviewer: Dr. Hernani Costa
Reviewed at: 2026-05-31

## Notes

- 22-item checklist, seven signal categories, and the four-week workflow with named owners and artefacts are reproduced as written.
- EU AI Act sandbox milestone (2 August 2026), GDPR Article 28, DORA effective date (January 2025), CISA SBOM minimum elements, SLSA L2 build provenance, and OWASP CI/CD Top 10 + LLM01 references are taken from the source.
- The four governance-gate outcomes (extend, promote-bounded, reject, pause-for-fix) and the "do not promote without evidence" default are preserved verbatim.
