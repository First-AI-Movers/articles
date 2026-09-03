# Changelog

> This is a reviewed snapshot generated manually. It is not deployment-generated.
> Run `python3 tools/build_changelog.py` to refresh.

## Features

- feat(governance): adopt the identifier-integrity manifest (no-op, attested) ([358](https://github.com/First-AI-Movers/articles/pull/358))
- feat(ci): add bounded Airtable backlog recovery ([341](https://github.com/First-AI-Movers/articles/pull/341))
- feat(ci): add read-only Airtable ingestion reconciliation ([339](https://github.com/First-AI-Movers/articles/pull/339))

## Bug Fixes

- fix(infra): remove unsupported actions cooldown key ([374](https://github.com/First-AI-Movers/articles/pull/374))
- fix(ci): make the sitemap guard structural (residual stability gap) ([346](https://github.com/First-AI-Movers/articles/pull/346))
- fix(ci): close residual Articles stability gaps ([343](https://github.com/First-AI-Movers/articles/pull/343))
- fix(ci): gate ingest auto-merge on mergeStateStatus CLEAN; dedup incidents ([337](https://github.com/First-AI-Movers/articles/pull/337))
- fix(ci): align dispatch + external ingestion with generated-artifact contract ([338](https://github.com/First-AI-Movers/articles/pull/338))
- fix(ci): repair weekly embeddings refresh PR workflow ([336](https://github.com/First-AI-Movers/articles/pull/336))
- fix(ci): disambiguate mcp-server build job from required `test` context ([335](https://github.com/First-AI-Movers/articles/pull/335))

## Documentation

- docs(contributing): name aeos-merge-ready as the incoming org pre-merge gate ([386](https://github.com/First-AI-Movers/articles/pull/386))
- docs: WordPress/Hetzner migration SEO pre-flight checklist (ROADMAP N4) ([357](https://github.com/First-AI-Movers/articles/pull/357))

## Chores

- chore(deps): bump @hono/node-server from 1.19.14 to 2.1.1 in /mcp-server ([382](https://github.com/First-AI-Movers/articles/pull/382))
- chore(deps): bump ip-address from 10.2.0 to 10.7.0 in /mcp-server ([384](https://github.com/First-AI-Movers/articles/pull/384))
- chore(deps): bump fast-uri from 3.1.2 to 3.1.6 in /mcp-server ([385](https://github.com/First-AI-Movers/articles/pull/385))
- chore(content): update Wrangler to 4.125 ([383](https://github.com/First-AI-Movers/articles/pull/383))
- chore(deps): bump the npm-minor-patch group across 3 directories with 5 updates ([381](https://github.com/First-AI-Movers/articles/pull/381))
- chore(deps-dev): bump @cloudflare/workers-types from 4.20260621.1 to 5.20260816.1 in /og-worker ([377](https://github.com/First-AI-Movers/articles/pull/377))
- chore(deps-dev): bump @cloudflare/workers-types from 4.20260621.1 to 5.20260816.1 in /mcp-server ([376](https://github.com/First-AI-Movers/articles/pull/376))
- chore(embeddings): refresh article embedding index ([352](https://github.com/First-AI-Movers/articles/pull/352))
- chore(deps): bump @modelcontextprotocol/sdk from 1.26.0 to 1.29.0 in /mcp-server ([304](https://github.com/First-AI-Movers/articles/pull/304))
- chore(deps): bump actions/setup-node from 6 to 7 ([353](https://github.com/First-AI-Movers/articles/pull/353))
- chore(deps): update openai requirement from >=2.48.0 to >=3.3.1 in /tools ([371](https://github.com/First-AI-Movers/articles/pull/371))
- chore(deps): update python-dotenv requirement from >=1.2.2 to >=1.2.3 in /tools ([370](https://github.com/First-AI-Movers/articles/pull/370))
- chore(deps): update pyarrow requirement from >=25.0.0 to >=25.0.1 in /tools ([367](https://github.com/First-AI-Movers/articles/pull/367))
- chore(deps): update numpy requirement from >=2.4.6 to >=2.5.2 in /tools ([366](https://github.com/First-AI-Movers/articles/pull/366))
- chore(deps): update markdown requirement from >=3.10.2 to >=3.10.3 in /tools ([363](https://github.com/First-AI-Movers/articles/pull/363))
- chore(infra): adopt Python 3.14 as the canonical runtime [PY314-ADOPTION-A] ([361](https://github.com/First-AI-Movers/articles/pull/361))
- chore(deps): update openai requirement in /tools ([333](https://github.com/First-AI-Movers/articles/pull/333))
- chore(deps): update pyarrow requirement in /tools ([332](https://github.com/First-AI-Movers/articles/pull/332))
- chore(deps): update pillow requirement in /tools ([321](https://github.com/First-AI-Movers/articles/pull/321))
- chore(deps): bump actions/setup-python from 5 to 6 ([334](https://github.com/First-AI-Movers/articles/pull/334))
- chore(deps): bump actions/upload-artifact from 4 to 7 ([331](https://github.com/First-AI-Movers/articles/pull/331))
- chore(deps): bump actions/cache from 5 to 6 ([303](https://github.com/First-AI-Movers/articles/pull/303))
- chore(deps-dev): bump typescript from 5.9.3 to 7.0.2 in /og-worker ([312](https://github.com/First-AI-Movers/articles/pull/312))
- chore(deps-dev): bump typescript from 5.9.3 to 7.0.2 in /mcp-server ([308](https://github.com/First-AI-Movers/articles/pull/308))

## CI/CD

- ci(aeos): adopt the post-main smoke rail — smoke only, revert not armed ([387](https://github.com/First-AI-Movers/articles/pull/387))
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
