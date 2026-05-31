# Summary Review — How to Automate a Maintainer Health Rubric in CI Before You Adopt an AI Tool

Article folder: 2026-05-10-automate-maintainer-health-rubric-ci-ai-tools-2026
Canonical URL: https://radar.firstaimovers.com/automate-maintainer-health-rubric-ci-ai-tools-2026
Generated at: 2026-05-31
Model: manual / human editorial draft from source article text

## 50-word summary

Automate a maintainer-health rubric in CI before piloting any open-source AI tool. Score nine public-source signals — license, release recency, contributors, issue responsiveness, bus factor, security posture, CODEOWNERS, dependency hygiene, SBOM — to a pass/warn/fail output. The JSON record is the evidence EU AI Act Article 16 and DORA Article 28 expect.

## 200-word summary

A spreadsheet ages the moment it is saved. The article argues that maintainer-health evaluation for open-source AI tooling belongs in CI, where it runs every time a dependency is added or a procurement candidate is filed, and where every run produces a machine-readable JSON that feeds the procurement record. The rubric scores nine public signals: license clarity (a hard gate — no license means default copyright applies), release recency, contributor activity in the last 90 days, issue responsiveness, bus factor, security posture against the GitHub Advisory Database and Dependabot, CODEOWNERS coverage, dependency hygiene, and SBOM or SLSA provenance readiness. OpenSSF Scorecard CLI and the GitHub REST API provide the raw signals. A 30-day implementation plan moves the team from a manual rubric on three candidates in week one, to a CI workflow that scores any repo URL in weeks two and three, to a procurement handoff in week four that maps pass/warn/fail to category-specific next steps. For European scale-ups, the same JSON evidence package satisfies EU AI Act Article 16 technical documentation, DORA Article 28 third-party risk reporting, and the audit response shape that turns two weeks of work into two days.

## 500-word summary

A maintainer-health rubric in a spreadsheet ages the moment it is saved. The article makes the case that for open-source AI tooling, that rubric belongs in CI: an automation that runs on every new-dependency PR, on every procurement candidate filed in the issue tracker, and on a scheduled re-evaluation of the existing tool inventory. Each run produces a JSON document with a pass/warn/fail decision, individual signal scores, and a timestamp — exactly the audit-trail shape EU AI Act Article 16 and DORA Article 28 demand.

Nine signals form the rubric. License clarity is a hard gate — no license means default copyright applies, and commercial deployment is unsafe; the GitHub REST repos endpoint returns a `license` field with an SPDX identifier when a recognised license file is detected, and a null value fails the build before any other check runs. Release recency uses `/repos/{owner}/{repo}/releases`, with a 6-month floor for general use. Contributor activity uses `/repos/{owner}/{repo}/stats/contributors`, requiring at least two active contributors in the last 90 days. Issue responsiveness pulls median time-to-first-response from `/repos/{owner}/{repo}/issues`. Bus factor inspects the contributor stats for diversification of commit ownership. Security posture queries the GitHub Advisory Database and Dependabot alerts. CODEOWNERS coverage checks that critical paths have an owner. Dependency hygiene reads Dependabot alert counts and severities. SBOM readiness verifies the presence of CycloneDX or SPDX files, or SLSA L2-plus build provenance as a substitute.

OpenSSF Scorecard CLI packages many of those signals into a single call. The article shows a worked Python example that hits the GitHub REST API directly, returning a JSON decision (PASS / WARN / FAIL) with a reason field. The dependency-hygiene path uses Dependabot via the GitHub GraphQL API with an authenticated token.

The 30-day implementation plan assigns owners. Days one to seven: the platform engineering lead and security lead manually run the rubric on three candidate AI tools to calibrate thresholds and teach the team which signals are meaningful; the CTO reviews the first three reports. Days eight to twenty-one: the AI transformation lead and platform engineering lead wire the rubric into GitHub Actions so any repo URL posted in an issue or PR receives a comment with the JSON summary. Days twenty-two to thirty: the procurement-aware engineering manager maps rubric outputs to procurement categories — pass goes to standard approval, warn requires a documented risk acceptance from CTO and security lead, fail is rejected unless a logged exception is granted. The first 30 days run in warn-only mode to build trust; after that, hard gates block on license absence, unpatched critical advisories, and missing CODEOWNERS.

Three categories must remain human-reviewed. Model-supply-chain checks: a clean repo can ship a poisoned checkpoint hosted elsewhere; the security lead verifies checkpoint provenance via SLSA or vendor-published hashes. License compatibility: detecting a license is automatable; deciding whether it permits your commercial use is a legal review. Strategic fit: architecture, support availability, and 24-month TCO remain CTO decisions. The rubric reduces noise; it does not make decisions.

## Review status

Status: approved
Reviewer: Dr. Hernani Costa
Reviewed at: 2026-05-31

## Notes

- Nine-signal rubric matrix and per-row thresholds reproduced as written in the source body.
- The Python example script is referenced but not embedded in the summary text.
- EU AI Act Article 16 and DORA Article 28 references taken from the source.
