# Changelog

> This is a reviewed snapshot generated manually. It is not deployment-generated.
> Run `python3 tools/build_changelog.py` to refresh.

## Features

- feat(ci): add bounded Airtable backlog recovery ([341](https://github.com/First-AI-Movers/articles/pull/341))
- feat(ci): add read-only Airtable ingestion reconciliation ([339](https://github.com/First-AI-Movers/articles/pull/339))

## Bug Fixes

- fix(ci): make the sitemap guard structural (residual stability gap) ([346](https://github.com/First-AI-Movers/articles/pull/346))
- fix(ci): close residual Articles stability gaps ([343](https://github.com/First-AI-Movers/articles/pull/343))
- fix(ci): gate ingest auto-merge on mergeStateStatus CLEAN; dedup incidents ([337](https://github.com/First-AI-Movers/articles/pull/337))
- fix(ci): align dispatch + external ingestion with generated-artifact contract ([338](https://github.com/First-AI-Movers/articles/pull/338))
- fix(ci): repair weekly embeddings refresh PR workflow ([336](https://github.com/First-AI-Movers/articles/pull/336))
- fix(ci): disambiguate mcp-server build job from required `test` context ([335](https://github.com/First-AI-Movers/articles/pull/335))
- fix(deps): hold numpy <2.5 on the Python 3.11 baseline (closes #278 path) ([301](https://github.com/First-AI-Movers/articles/pull/301))
- fix(security): guard articles gitleaks config against no-op (SCANNER-EFFECTIVENESS-GUARD-MULTIREPO-ADOPTION-A) ([298](https://github.com/First-AI-Movers/articles/pull/298))
- fix(security): narrow Articles gitleaks path allowlists (ARTICLES-GITLEAKS-ALLOWLIST-PATH-TIGHTEN-A) ([297](https://github.com/First-AI-Movers/articles/pull/297))
- fix(security): make articles gitleaks gate non-trivial — extend default ruleset (MULTIREPO-GITLEAKS-ALLOWLIST-CONSISTENCY-AUDIT-A) ([293](https://github.com/First-AI-Movers/articles/pull/293))
- fix(test): migrate Cloudflare Workers Vitest pool to 0.16 and keep mcp/og tests offline ([289](https://github.com/First-AI-Movers/articles/pull/289))

## Documentation

- docs: WordPress/Hetzner migration SEO pre-flight checklist (ROADMAP N4) ([357](https://github.com/First-AI-Movers/articles/pull/357))
- docs(security): cross-link org no-paid posture index from IR runbook (MULTIREPO-IR-RUNBOOK-INDEX-CROSSLINK-A) ([292](https://github.com/First-AI-Movers/articles/pull/292))
- docs: close the generated-artifact drift-check stability window (ARTICLES-GENERATED-ARTIFACT-STABILITY-CLOSEOUT-A) ([290](https://github.com/First-AI-Movers/articles/pull/290))

## Chores

- chore(deps): update openai requirement in /tools ([333](https://github.com/First-AI-Movers/articles/pull/333))
- chore(deps): update pyarrow requirement in /tools ([332](https://github.com/First-AI-Movers/articles/pull/332))
- chore(deps): update pillow requirement in /tools ([321](https://github.com/First-AI-Movers/articles/pull/321))
- chore(deps): bump actions/setup-python from 5 to 6 ([334](https://github.com/First-AI-Movers/articles/pull/334))
- chore(deps): bump actions/upload-artifact from 4 to 7 ([331](https://github.com/First-AI-Movers/articles/pull/331))
- chore(deps): bump actions/cache from 5 to 6 ([303](https://github.com/First-AI-Movers/articles/pull/303))
- chore(deps-dev): bump typescript from 5.9.3 to 7.0.2 in /og-worker ([312](https://github.com/First-AI-Movers/articles/pull/312))
- chore(deps-dev): bump typescript from 5.9.3 to 7.0.2 in /mcp-server ([308](https://github.com/First-AI-Movers/articles/pull/308))
- chore(deps): bump actions/checkout from 6 to 7 ([268](https://github.com/First-AI-Movers/articles/pull/268))
- chore(deps): bump zod from 3.25.76 to 4.4.3 in /mcp-server ([271](https://github.com/First-AI-Movers/articles/pull/271))
- chore(deps): update openai requirement in /tools ([269](https://github.com/First-AI-Movers/articles/pull/269))
- chore(deps): update pyyaml requirement from >=6.0 to >=6.0.3 in /tools ([258](https://github.com/First-AI-Movers/articles/pull/258))
- chore(deps-dev): bump @playwright/test from 1.59.1 to 1.61.1 ([270](https://github.com/First-AI-Movers/articles/pull/270))
- chore(ci): group Dependabot minor+patch updates to cut PR noise ([300](https://github.com/First-AI-Movers/articles/pull/300))
- chore(deps): lift stale mcp-server vitest-major ignore (ARTICLES-POOL-WORKERS-UPSTREAM-WATCH-A) ([291](https://github.com/First-AI-Movers/articles/pull/291))

## CI/CD

- ci: align the protected required-check contract ([340](https://github.com/First-AI-Movers/articles/pull/340))
- ci(infra): TypeScript lifecycle advisory dogfood for mcp-server + og-worker (TYPECHECK-ADVISORY-DOGFOOD) ([327](https://github.com/First-AI-Movers/articles/pull/327))
- ci(og-worker): add real typecheck/test/build CI for og-worker package ([326](https://github.com/First-AI-Movers/articles/pull/326))

## Other Changes

- ingest(articles): recover missed Airtable batch 06 ([350](https://github.com/First-AI-Movers/articles/pull/350))
- ingest(articles): recover missed Airtable batch 05 ([349](https://github.com/First-AI-Movers/articles/pull/349))
- ingest(articles): recover missed Airtable batch 04 ([348](https://github.com/First-AI-Movers/articles/pull/348))
- ingest(articles): recover missed Airtable batch 03 ([347](https://github.com/First-AI-Movers/articles/pull/347))
- ingest(articles): recover missed Airtable batch 02 ([345](https://github.com/First-AI-Movers/articles/pull/345))
- ingest(articles): recover missed Airtable batch 01 ([344](https://github.com/First-AI-Movers/articles/pull/344))
- ingest(articles): add articles from Airtable ([328](https://github.com/First-AI-Movers/articles/pull/328))
- ingest(articles): add articles from Airtable ([323](https://github.com/First-AI-Movers/articles/pull/323))
- ingest(articles): add articles from Airtable ([322](https://github.com/First-AI-Movers/articles/pull/322))
- ingest(articles): add articles from Airtable ([319](https://github.com/First-AI-Movers/articles/pull/319))
- ingest(articles): add articles from Airtable ([316](https://github.com/First-AI-Movers/articles/pull/316))
- ingest(articles): add articles from Airtable ([315](https://github.com/First-AI-Movers/articles/pull/315))
- ingest(articles): add articles from Airtable ([314](https://github.com/First-AI-Movers/articles/pull/314))
- ingest(articles): add articles from Airtable ([313](https://github.com/First-AI-Movers/articles/pull/313))
- ingest(articles): add articles from Airtable ([302](https://github.com/First-AI-Movers/articles/pull/302))
- ingest(articles): add articles from Airtable ([294](https://github.com/First-AI-Movers/articles/pull/294))
