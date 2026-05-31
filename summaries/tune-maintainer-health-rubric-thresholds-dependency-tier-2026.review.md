# Summary Review — Should Your Maintainer Health Rubric Change by Dependency Tier?

Article folder: 2026-05-11-tune-maintainer-health-rubric-thresholds-dependency-tier-2026
Canonical URL: https://radar.firstaimovers.com/tune-maintainer-health-rubric-thresholds-dependency-tier-2026
Generated at: 2026-05-31
Model: manual / human editorial draft from source article text

## 50-word summary

A single maintainer-health threshold does not survive scale-up. Tier dependencies by blast radius and replaceability — runtime-critical, security-sensitive, build-chain, developer-only, experimental, replaceable — then calibrate bus-factor, release-recency, license, and SBOM gates per tier. The same tier metadata feeds EU AI Act conformity assessments and DORA Article 28 third-party risk reports.

## 200-word summary

A single maintainer-health threshold may work at twenty dependencies, but it breaks at two hundred — the typical scale-up posture once AI tooling enters the stack. The article argues for tiering open-source dependencies by blast radius and replaceability into six classes: runtime-critical, security-sensitive, build-chain, developer-only, experimental, and replaceable. Each tier carries its own thresholds for release recency, bus factor, license, and SBOM / SLSA coverage; license clarity is a hard gate at every tier because no license means default copyright and unsafe commercial use. The 30-day implementation plan walks platform engineering, security, and procurement-aware roles through tier inventory and dry-run scoring on the top twenty dependencies (days one to seven), CI integration of tier metadata and tier-specific thresholds via OpenSSF Scorecard and the GitHub REST API (days eight to twenty-one), and procurement handoff mapping tier output to the risk-class register (days twenty-two to thirty). Three named failure modes — classification errors, tier-tag rot as projects drift toward production, and engineer downgrade pressure under shipping deadlines — each have specific mitigations. For European scale-ups, the resulting tier evidence directly satisfies EU AI Act conformity assessments and DORA Article 28 third-party risk reporting.

## 500-word summary

A single open-source maintainer-health threshold does not survive scale-up. At twenty dependencies, one bus-factor floor and one release-recency window is workable. At two hundred — the typical posture once a European scale-up takes on AI tooling — the same flat rule either over-blocks harmless dev tools or under-protects runtime-critical inference frameworks. The article makes the case for a tiered rubric calibrated by blast radius and replaceability, and shows how that tier metadata then doubles as the evidence pack EU AI Act and DORA reviewers will ask for.

Six tiers form the spine of the rubric. Runtime-critical dependencies ship in production and handle user requests; the tier requires releases within thirty days, two or more maintainers from two or more organisations, a permissive or LGPL-with-explicit-patent-grant license, and SBOM plus SLSA L1 or higher. Security-sensitive dependencies handle auth, crypto, or network security and carry similar gates with a sixty-day release window. Build-chain dependencies run in CI but never ship to production; release windows widen to ninety days and bus-factor floors drop. Developer-only dependencies stay on engineer laptops. Experimental dependencies sit in notebooks. Replaceable libraries have multiple mature alternatives.

License clarity is a hard gate at every tier. No license means default copyright applies, which makes commercial deployment unsafe regardless of how popular or technically excellent the project looks. OpenSSF Scorecard supplies the contributor-diversity, code-review, maintained, dependency-update-tool, and signed-releases signals; the article weights those signals differently per tier. OWASP CI/CD Top 10 frames the threat model — dependency-chain abuse and credential hygiene hit build-chain harder, while insufficient flow control and insecure system configuration hit runtime-critical harder. For AI runtime stacks, OWASP LLM Top 10 adds prompt-injection, training-data poisoning, and model denial-of-service to the gate.

The 30-day implementation plan assigns clear ownership. Days one to seven: the platform engineering lead and security lead classify the top twenty dependencies and run dry-run scores against the six-tier model. Days eight to twenty-one: tier metadata gets embedded into the dependency management system and CI applies tier-specific Scorecard thresholds. Days twenty-two to thirty: the procurement-aware engineering manager maps tier output to the risk-class register and the CTO reviews the first five procurement requests against the new evidence shape.

Three named failure modes deserve attention. Classification error: misclassifying a runtime-critical dependency as build-chain leads directly to under-scrutiny and a supply-chain attack. Tier-tag rot: a project that started experimental in week one quietly becomes runtime-critical by week twelve because someone wired it into the inference path; mitigation is a quarterly tier-reclassification review plus an event-driven re-tier on any change to the production import graph. Human downgrade pressure: engineers under shipping pressure will downgrade tiers to make a rubric pass; mitigations include an append-only tier-change log, a second approver for runtime-critical-to-build-chain downgrades, and surfacing tier-downgrade events in CTO review. Combined with mandatory SLSA attestations on the top two tiers, the rubric's failure modes become observable even when individual classifications are wrong.

## Review status

Status: approved
Reviewer: Dr. Hernani Costa
Reviewed at: 2026-05-31

## Notes

- Six-tier model and per-tier threshold matrix reproduced as the article presents them.
- EU AI Act sandbox milestone (2 August 2026), DORA Article 28, OWASP CI/CD Top 10, and OWASP LLM Top 10 references taken from the source body.
- No invented statistics, citations, or vendor claims were introduced.
