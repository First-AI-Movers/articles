# Summary Review — Why GitHub Stars Are a Bad Procurement Metric for AI Tools

Article folder: 2026-05-10-github-stars-bad-procurement-metric-ai-tools-2026
Canonical URL: https://radar.firstaimovers.com/github-stars-bad-procurement-metric-ai-tools-2026
Generated at: 2026-05-31
Model: manual / human editorial draft from source article text

## 50-word summary

GitHub stars measure attention, not procurement fitness. A 122k-star repo with no LICENSE file is unusable; a 28k-star repo stale for seven months is a liability. Replace star-driven selection with a five-gate decision rule covering legal, security, maintenance, evidence, and a 30-day pilot — the evidence shape EU AI Act sandbox audits expect.

## 200-word summary

GitHub stars are a leading indicator of attention, not a lagging indicator of suitability. The article shows how star-driven procurement repeatedly selects high-attention, high-risk repositories — a 122,000-star repo with no LICENSE file (unusable under default copyright), a 28,000-star repo stale for seven months, non-OSI licenses on heavily-starred tools that restrict commercial embedding — while passing over lower-star but safer alternatives that pair a permissive license, corporate backing, and active commits. The argument is not that stars are useless; they are a weak but valid discovery filter. The argument is that they cannot be a decision input. The article reframes procurement evidence into three categories: legal (OSI-approved license is a hard gate), operational (commit recency, release cadence, maintainer count, Scorecard signals), and security (the five-feature GitHub security baseline, SLSA L2 as the practical procurement floor for build provenance, SBOM for dependency transparency). A ten-row procurement scorecard adds enterprise support, integration fit, observability, and reversibility. A five-gate decision rule — legal, security, maintenance, evidence, decision — replaces "we picked this because it has 100k stars" with an answer that survives the August 2026 EU AI Act sandbox milestone.

## 500-word summary

GitHub stars are a leading indicator of attention, not a lagging indicator of suitability. The article opens with concrete examples that European procurement teams keep tripping over: a repository with 122,000 stars and no LICENSE file, which under default copyright cannot legally be used or distributed in commercial products; a 28,000-star repository whose last commit was seven months ago, abandoning the dependency to silent security drift; non-OSI licenses on very high-star tools that are valid open-source but restrict hosted-service redistribution and require dedicated legal review before commercial embedding. Stars conceal each of these blockers because they collapse popularity, safety, maintenance, and licensing into one number.

The case is reframed into three categories of procurement evidence. Legal: the license file is the most common blocker. No license is a hard pass because default copyright applies; non-OSI licenses such as Sustainable Use or Dify's restricted license require legal review against the specific business model before embedding. A one-page legal memo per pilot is cheap insurance. Operational: maintenance health depends on commit recency (the 90-day floor), release cadence, and maintainer count; OpenSSF Scorecard packages contributor-diversity, code-review, and dependency-update-tool checks into a 0-10 score that procurement can consult before any pilot starts. Security: the GitHub security baseline names five features as the minimum — dependency graph, Dependabot alerts with automatic security updates, CodeQL default setup, secret scanning with push protection, and a published SECURITY.md. SLSA L2 is the practical procurement floor for build provenance, with L3 the hardened bar for high-stakes deployments. SBOM is the dependency-transparency floor. For European teams, the data-flow question is decisive under the EU AI Act: self-hosting (where supported) reduces residency risk; cloud-only AI tools need a documented residency posture before pilot.

A ten-row procurement scorecard turns those categories into a usable artefact, adding enterprise support, integration fit, observability, and reversibility / exit path. The seven-step 30-day pilot then validates the procurement signals: define exit criteria, set up a sandbox environment without production data, review data flow against OWASP LLM01 mitigations, run the security baseline including Scorecard and an SBOM, test integration into staging, conduct a load test against 2x expected traffic, then document lessons against the exit criteria and make a go / no-go decision.

The article closes with a five-gate decision rule that fits on a slide. Legal gate: does the repo carry a license permitting commercial use? Security gate: does it pass the GitHub security baseline? Maintenance gate: commit or release in the last 90 days? Evidence gate: at least one positive pilot or community reference? Decision: if all pass, run a 30-day pilot with exit criteria; if any fail, require a mitigation plan first. Stars sit where they belong — a weak but useful discovery signal, not a decision input. For European teams under the August 2026 EU AI Act sandbox milestone, every procurement decision made now will be reviewed under sandbox conditions, and a star count is not a justifiable answer.

## Review status

Status: approved
Reviewer: Dr. Hernani Costa
Reviewed at: 2026-05-31

## Notes

- Star-count examples (122k stars no LICENSE, 28k stars 7-month stale, non-OSI licenses on heavily-starred tools) reproduced as in the source body; example IDs (R5, R6, R7, R8) not surfaced to avoid orphan references.
- SLSA levels, the GitHub security baseline (5 features), and the EU AI Act sandbox milestone (2 August 2026) taken from the source.
- Specific project names from the article body (stanford-oval/storm, forrestchang/andrej-karpathy-skills, n8n-io/n8n, langgenius/dify) are kept abstract in the summaries.
