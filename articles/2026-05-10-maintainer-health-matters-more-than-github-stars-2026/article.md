---
title: "Maintainer Health Matters More Than GitHub Stars for AI Tool Procurement"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/maintainer-health-matters-more-than-github-stars-2026"
published_date: "2026-05-10"
license: "CC BY 4.0"
---

> **TL;DR:** CTOs and platform leaders discover why maintainer health outranks star counts for enterprise when selecting open source AI tools.

If your procurement process for AI tools still leans heavily on GitHub star counts, you are selecting for popularity, not reliability. Stars signal attention; maintainer health signals survival. **Why this matters**: the EU AI Act sandbox milestone of 2 August 2026 (S7) will require demonstrable due diligence on the tools incorporated into AI systems, and a high-star, abandoned repository is a compliance liability. For CTOs, platform engineering leads, procurement-aware engineering managers, AI transformation leads, security leads, and operations leaders in founder-led companies or growing software teams, the shift from star chasing to health checking is the single most impactful change you can make in your open source procurement workflow. Finance teams need this too: abandoned tools burn budget through security incidents and migration costs.

## The short version

- Maintainer health is a set of leading and lagging indicators that tell you whether a project will still be alive next quarter. Star counts measure attention, not maintenance.
- The ten dimensions in this article (commit recency, contributor breadth, bus factor, issue response time, release cadence, security responsiveness, license clarity, dependency hygiene, governance model, enterprise support) are the columns of a procurement-grade scorecard. Pull them once for every open-source AI tool before adoption.
- Contributor breadth plus recency together survive the loss of any single contributor. Single-author MIT licensed projects are safe for personal use but unsafe for enterprise commercial deployment.
- Backed-but-orphaned is a real failure mode. A corporate sponsor stopping investment looks identical to a community-maintained project losing momentum, and the cost of unwinding both is the same.
- Policy controls the merge button; maintainer health controls the supply chain. Both gates need to be in place. The 15-minute rubric in this article belongs in every procurement scorecard, not in a separate security review.
- For European scale-ups, the EU AI Act sandbox milestone (2 August 2026, S7) and DORA third-party-vendor obligations for financial services (S11) make documented maintainer-health evidence a compliance artifact, not just a procurement preference.

## What maintainer health actually measures

The table below lays out the ten dimensions you need to track, where to find the data, and the red flags that should stop your procurement process.

| Dimension | What it tells you | Where to find it | Red flag |
|---|---|---|---|
| Commit recency | Whether the project is actively maintained | GitHub Insights > Code frequency | Last commit > 6 months ago |
| Contributor breadth | How many distinct people contribute | Insights > Contributors > Individuals | 80%+ commits from one or two people |
| Bus factor | Number of contributors whose loss would stall the project | Insights > Contributors > Commits | Bus factor < 3 |
| Issue response time | Whether maintainers care about users | REST API /repos/{owner}/{repo}/issues | Median first response > 30 days |
| Release cadence | How often new versions are shipped | Releases page | No release in 12 months |
| Security responsiveness | Speed of patch delivery for CVEs | GitHub Advisory Database (S5) | Advisory unfixed > 90 days |
| License clarity | Legal permission to use | LICENSE file or choosealicense.com (S6) | No license or non-OSI license |
| Dependency hygiene | Health of recursive dependencies | Dependabot alerts (S12), SBOM | High count of unfixed alerts |
| Governance model | Decision-making structure | CODEOWNERS file (S10), contributing guide | No governance doc, single person merges |
| Enterprise support | Commercial backing or SLAs | README, website, vendor contact | No support channel, no SLA |

## How to read the GitHub signals: contributors, commits, releases, issues

GitHub provides several built-in surfaces to assess maintainer health without leaving the platform.

**Insights tab** (S2): Navigate to `Insights > Contributors` to see commit activity per contributor over time. The `Individuals` view shows unique authors per month. A healthy project has a stable or growing number of contributors month over month. `Insights > Code Frequency` gives commit volume trends; a long flat tail indicates abandonment. `Insights > Pulse` shows recent activity across issues and pull requests.

**REST API endpoints** (S3, S4): For automated checks, call `GET /repos/{owner}/{repo}/issues` to list issues with timestamps. Filter by `state:open` and `sort:updated` to see issue response lag. Use `GET /repos/{owner}/{repo}/pulls` to review pull request merge times. Track `GET /repos/{owner}/{repo}/stats/contributors` for contributor diversity over time.

**Release page**: Check `GitHub Releases` for semantic versioning and release notes. A project with regular releases (monthly or quarterly) signals active maintenance, and a project that ships release notes describing security fixes signals an even more mature posture.

A platform engineering lead automating these checks should script the four endpoints together. The procurement-grade pattern is: pull `GET /repos/{owner}/{repo}/stats/contributors` to compute the bus factor (count contributors whose share of the last 90 days of commits crosses 5%); pull `GET /repos/{owner}/{repo}/issues?state=open&sort=updated&per_page=20` to sample issue-response lag; pull `GET /repos/{owner}/{repo}/pulls?state=closed&per_page=30` to compute median merge time; cross-check against the GitHub Advisory Database (S5) for any open advisories the maintainer has not patched. Layer Dependabot alerts on top per S12. The four pulls together fit in a 60-line script that an AI transformation lead or a security lead can run before the procurement scorecard meeting. None of the calls require write authentication; a personal access token with `public_repo` scope is enough for any public repository, and rate limits at 60 requests per hour unauthenticated or 5,000 per hour authenticated handle a procurement-batch of 30 to 50 repositories comfortably.

## Bus-factor and corporate backing: when one maintainer is enough

The bus factor is the number of contributors whose departure would cripple the project. A single-maintainer project has a bus factor of 1. Even if backed by a well-known company, if all commits flow through one person, the project is fragile. Corporate backing can provide resources, but if the sole maintainer leaves the company, the project may stall. Healthy projects have a bus factor of 3 or more, or a governance model that distributes responsibilities across multiple people. R1 (qdrant) has multiple core contributors; R2 (llama.cpp) benefits from broad community engagement. R5 (DeepSeek-TUI) is a single-author project with high bus-factor risk.

There are three legitimate exceptions to the "bus factor must be at least 3" rule, and a CTO or security lead should know them before the procurement-aware engineering manager raises an objection. First, a paid support contract that names a specific bench of engineers as the SLA-bound responders effectively raises the bus factor by the bench size; the maintainer-health column on your scorecard then reads "1 + N (under SLA)" and the procurement decision becomes a contract-review decision. Second, an escrow agreement that gives you the right to fork and continue the project on the original maintainer's incapacity; this is rare in OSS but common in dual-licensed commercial OSS. Third, a tool whose blast radius if abandoned is genuinely contained (a CLI utility used only by your own engineering team, never embedded in a customer-facing product) where the operations leader can absorb the rewrite cost. Outside those three, single-maintainer is unsafe for enterprise commercial deployment regardless of how clean the code is or how responsive the maintainer was last quarter.

The corporate-backing-as-substitute pattern deserves a separate note. A platform engineering lead who has seen one project orphaned after a strategic shift at a sponsoring company will never trust corporate backing alone again. The signal you actually want is contributor breadth that survives a sponsor change: commits from at least three distinct organizations or domains in the last twelve months. The OpenSSF Scorecard contributor-diversity check (S1) computes this directly. Read it as "diversity-adjusted bus factor" rather than "is the sponsor on the README."

## The OpenSSF Scorecard contributor-diversity check

OpenSSF Scorecard (S1) automates several maintainer-health checks and produces a single 0-10 score that procurement-aware engineering managers can drop straight into a vendor scorecard. Three Scorecard checks bear directly on maintainer health.

The `contributor-diversity` check verifies that project commits come from multiple organizations within a recent window. A repo where every commit comes from one company will score low here even if the company is a household name. The check defends against the backed-but-orphaned failure mode by treating "diverse organizational sources" as the more durable signal than "one well-known sponsor."

The `code-review` check ensures that changes are reviewed before merging. A single-maintainer project where every commit lands without review will score zero on this check. Even if the rest of the score is acceptable, the absence of code review is a procurement red flag because it means the project has no peer-validation step on the code that ends up in your supply chain. The OWASP CI/CD Top 10 (S8) treats poisoned-pipeline execution as a top supply-chain risk for exactly this reason.

The `maintained` check confirms recent commit and issue activity. It is not a binary "alive vs dead" signal; it is a graded score that captures both commit recency and issue-response cadence. A repo that ships one commit a quarter to keep the check satisfied without engaging with issues will score lower here than the maintained check first appears to suggest.

Operating instruction: run `scorecard --repo=github.com/owner/repo` against any AI tool before procurement and record the score in the artifact register. A score below 5 for `contributor-diversity` or `maintained` should block procurement absent a documented mitigation. A score above 7 is the comfortable bar for high-stakes use; below 5 is a hard stop until the maintainers address the gaps. Pair the Scorecard score with the 15-minute rubric in the next section; Scorecard answers the "is this maintained at all" question deterministically, the rubric answers the "is this maintained well enough for our specific use case" question.

## A 15-minute maintainer-health rubric

Spend 15 minutes on the following checklist for any AI open source tool before adding it to your stack. Each item includes the action and the pass criterion.

- [ ] Check commit recency: GitHub Code Frequency graph (last commit < 90 days)
- [ ] Assess contributor breadth: Insights > Contributors > Individuals (at least 3 unique authors in last quarter)
- [ ] Calculate bus factor: Review top 5 contributors by commit count (no single person > 50% of total)
- [ ] Scan issue response time: REST API issues endpoint (median response < 7 days)
- [ ] Review release cadence: Releases page (at least one release in last 12 months)
- [ ] Verify security responsiveness: GitHub Advisory Database (no critical unfixed advisory > 30 days)
- [ ] Confirm license: LICENSE file present and OSI approved (MIT, Apache 2.0, BSD)
- [ ] Inspect dependency hygiene: Dependabot alerts (no high/critical unfixed alerts)
- [ ] Evaluate governance: CODEOWNERS file or governance doc (clear review process)
- [ ] Run OpenSSF Scorecard: Score >= 5 on contributor-diversity and maintained

If your team needs a structured approach consider booking an AI readiness assessment at https://radar.firstaimovers.com/page/ai-readiness-assessment or consulting support at https://radar.firstaimovers.com/page/ai-consulting.

## Three failure modes from public repos

These three patterns surface across the open-source AI corpus more often than any operations leader would like. Each is a teaching example, not a hit-list. The point is not that the named repos are bad; the point is that a CTO or AI transformation lead who scans only the star count would miss every one.

**Failure 1: Abandoned but popular (R3: stanford-oval/storm).** This repository's last commit was September 2025 per `gh api` check on 2026-05-10, more than seven months stale at the time of this article. Despite high attention and a citation-rich README, the project is no longer being maintained. Security patches do not arrive. Dependencies rot. The maintainers may resume activity later, but a procurement decision today cannot rest on that hope. Compare with R1 (qdrant/qdrant), which has regular commits, frequent tagged releases, and a security-disclosure policy. The two repositories are in the same broad ecosystem; the maintainer-health columns separate them cleanly.

**Failure 2: No license but popular (R4: forrestchang/andrej-karpathy-skills).** High star count, no LICENSE file. Under default copyright (S6), you have no right to use, modify, or distribute the code in your commercial product. Even if your engineering team loves the design, your legal lead cannot sign off, and your procurement-aware engineering manager cannot record a green legal-review memo. Procurement teams routinely skip legal review for trending repos because the absence of a license file is invisible from the GitHub homepage. The maintainer-health rubric in this article surfaces it on the License clarity row in 30 seconds. This is a hard pass for enterprise commercial deployment unless the operator obtains an explicit written license grant from the maintainer.

**Failure 3: Single-author bus factor (R5: Hmbown/DeepSeek-TUI).** All commits come from one person. If that person disappears, so does the project. Even if the code is MIT and the engineering team has every right to fork it, the cost of forking and maintaining a production-critical tool falls on the operations leader and the technical team that picked it. For a 20-person company or a growing software team, that is rarely a cost worth absorbing. Single-author repositories are safe for personal use and for dev-only experimentation; they are unsafe for production embedding without one of the three exceptions named in the bus-factor section above. Contrast with R2 (ggml-org/llama.cpp), which has diverse contributors across multiple organizations and a stable cadence; the maintainer-health rubric scores R2 high on contributor breadth and low on bus-factor risk.

The procurement implication is the same in all three cases. The 15-minute rubric catches each pattern in the first five minutes. Star counts catch none of them. The cost of the rubric is twenty minutes of platform engineering lead or security lead time per candidate tool; the cost of skipping the rubric is the migration project that arrives twelve months later when the tool's maintenance gap finally hits production.

## What not to delegate to maintainer-health metrics

Avoid these anti-patterns that misinterpret maintainer health:

- **Star count as health proxy** . Stars measure attention, not maintenance. A 50K star repo can be dead.
- **Single corporate sponsor as substitute for breadth** . VMware-backed projects have gone orphaned when priorities shift.
- **"Active in last 90 days" without checking who committed** . One person pushing cosmetic commits is not health.
- **Skipping legal review on non-OSI licenses** (S6) . Non-OSI licenses can create compliance issues under EU AI Act.
- **Auto-promoting trending tools** . GitHub Trending highlights velocity, not sustainability.
- **Confusing release cadence with release quality** . Frequent releases of buggy code are worse than none.

## Frequently Asked Questions

### Q: Is a single-maintainer project ever safe for enterprise use?
A: Rarely. A single maintainer project can be safe only if you have a paid support contract, an escrow agreement, or you fork and maintain it yourself. For most enterprise contexts, a bus factor of at least 3 is required.

### Q: How recent is "recent enough" for the commit-recency check?
A: For a project in active development, a commit within the last 90 days is a baseline. For stable libraries, 6 months may be acceptable, but verify that security issues are still addressed.

### Q: Does corporate backing replace the contributor-diversity check?
A: No. Corporate backing can provide resources but does not guarantee contributor diversity. A project with commits from a single company still has a single point of failure if that company changes priorities.

### Q: How does the EU AI Act change maintainer-health expectations?
A: The EU AI Act (S7) sandbox milestone of 2 August 2026 requires documented due diligence on tools used in AI systems. A maintainer-health assessment becomes a compliance artifact. Abandoned or opaque projects may fail audits.

### Q: What is the realistic time to run the 15-minute rubric?
A: For an experienced platform engineering lead or security lead, the manual checklist takes 10 to 15 minutes per repository on the first run. The first time a technical team builds the muscle, expect closer to 25 to 30 minutes while they learn which Insights tab path to click and which REST API endpoint returns the data they need. By the third or fourth run, the rubric drops to under 10 minutes. Automated tools like OpenSSF Scorecard (S1) and GitHub REST API scripts (S3, S4) can reduce the per-project pass to under 2 minutes when the operations leader wires the checks into a CI pre-procurement step. The cost of running the rubric is dwarfed by the cost of unwinding a bad procurement decision six months in, especially for a founder-led company or a finance team that has to absorb the migration spend off-budget.

### Q: How does maintainer health interact with cluster pieces in this Radar series?
A: This article is the operational rubric layer for the cluster anchored by `github-stars-bad-procurement-metric-ai-tools-2026`. The parent piece argues that stars are not procurement evidence; this piece converts the argument into a 15-minute checklist a technical team can run. The companion `open-source-ai-tool-security-checklist-european-scale-ups-2026` extends the rubric into the security-specific dimensions (SBOM per S9, dependency hygiene per S12, OWASP CI/CD Top 10 per S8). The companion `30-day-pilot-open-source-ai-coding-agent-2026` is the next step after the rubric passes: once a tool clears the maintainer-health rubric, the 30-day pilot is the procurement gate that produces the evidence the EU AI Act sandbox audit (S7) will look for.

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Maintainer Health Matters More Than GitHub Stars for AI Tool Procurement",
  "description": "CTOs and platform leaders discover why maintainer health outranks star counts for enterprise when selecting open source AI tools.",
  "datePublished": "2026-05-10T19:48:44.982279+00:00",
  "dateModified": "2026-05-10T19:48:44.982279+00:00",
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
    "@id": "https://radar.firstaimovers.com/maintainer-health-matters-more-than-github-stars-2026"
  },
  "image": "https://images.unsplash.com/photo-1488229297570-58520851e868?w=1200&h=630&fit=crop&q=80",
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
      "name": "Q: Is a single-maintainer project ever safe for enterprise use?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A: Rarely. A single maintainer project can be safe only if you have a paid support contract, an escrow agreement, or you fork and maintain it yourself. For most enterprise contexts, a bus factor of at least 3 is required."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How recent is "recent enough" for the commit-recency check?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A: For a project in active development, a commit within the last 90 days is a baseline. For stable libraries, 6 months may be acceptable, but verify that security issues are still addressed."
      }
    },
    {
      "@type": "Question",
      "name": "Q: Does corporate backing replace the contributor-diversity check?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A: No. Corporate backing can provide resources but does not guarantee contributor diversity. A project with commits from a single company still has a single point of failure if that company changes priorities."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How does the EU AI Act change maintainer-health expectations?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A: The EU AI Act (S7) sandbox milestone of 2 August 2026 requires documented due diligence on tools used in AI systems. A maintainer-health assessment becomes a compliance artifact. Abandoned or opaque projects may fail audits."
      }
    },
    {
      "@type": "Question",
      "name": "Q: What is the realistic time to run the 15-minute rubric?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A: For an experienced platform engineering lead or security lead, the manual checklist takes 10 to 15 minutes per repository on the first run. The first time a technical team builds the muscle, expect closer to 25 to 30 minutes while they learn which Insights tab path to click and which REST API ..."
      }
    }
  ]
}
</script>
-->