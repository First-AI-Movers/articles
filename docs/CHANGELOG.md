# Changelog

> This is a reviewed snapshot generated manually. It is not deployment-generated.
> Run `python3 tools/build_changelog.py` to refresh.

## Features

- feat(ingest): one eligibility gate for ingestion, reconciliation and recovery, receipt mode behind a switch [#423 #388] ([428](https://github.com/First-AI-Movers/articles/pull/428))
- feat(ingest): verified publication receipt verifier, unwired [#423 #388] ([427](https://github.com/First-AI-Movers/articles/pull/427))
- feat(governance): adopt the identifier-integrity manifest (no-op, attested) ([358](https://github.com/First-AI-Movers/articles/pull/358))

## Bug Fixes

- fix(recover-backlog): name the backlog by what the gate admitted [#423] ([442](https://github.com/First-AI-Movers/articles/pull/442))
- fix(ingest): retention is not gated; unresolved Hashnode receipts fall through to the source [#423] ([431](https://github.com/First-AI-Movers/articles/pull/431))
- fix(ingest): decide archive presence before paying for a receipt lookup [#423] ([430](https://github.com/First-AI-Movers/articles/pull/430))
- fix(ci): one open E41 incident, one comment per failed run [#423 #388] ([424](https://github.com/First-AI-Movers/articles/pull/424))
- fix(ci): dedicated App auth for publication, independent alarm path [#388] ([396](https://github.com/First-AI-Movers/articles/pull/396))
- fix(tests): assert the SHA pin shape, not the tag PR #390 replaced [#3311] ([394](https://github.com/First-AI-Movers/articles/pull/394))
- fix(infra): remove unsupported actions cooldown key ([374](https://github.com/First-AI-Movers/articles/pull/374))

## Documentation

- docs(adr): archive-eligibility-by-verified-publication-receipt Archive eligibility by verified publication receipt [#423 #388] ([426](https://github.com/First-AI-Movers/articles/pull/426))
- docs(ir): state the zizmor retirement rationale and the two pin policies precisely [agent-toolkit#3460] ([401](https://github.com/First-AI-Movers/articles/pull/401))
- docs(3311): retire the tools/tests file index and the stale PR-lifecycle prose [#3311] ([393](https://github.com/First-AI-Movers/articles/pull/393))
- docs(3311): add a repository-specific AGENTS.md and CLAUDE.md [#3311] ([391](https://github.com/First-AI-Movers/articles/pull/391))
- docs(contributing): name aeos-merge-ready as the incoming org pre-merge gate ([386](https://github.com/First-AI-Movers/articles/pull/386))

## Tests

- test: isolate the suite from the runner's ARCHIVE_ELIGIBILITY_GATE [#423] ([434](https://github.com/First-AI-Movers/articles/pull/434))

## Chores

- chore(deps): bump hono from 4.13.7 to 4.13.8 in /mcp-server [#432] ([443](https://github.com/First-AI-Movers/articles/pull/443))
- chore(embeddings): refresh article embedding index ([440](https://github.com/First-AI-Movers/articles/pull/440))
- chore(deps): update openai requirement from >=3.3.1 to >=3.8.0 in /tools ([416](https://github.com/First-AI-Movers/articles/pull/416))
- chore(deps): update numpy requirement from >=2.5.2 to >=2.5.3 in /tools ([417](https://github.com/First-AI-Movers/articles/pull/417))
- chore(deps): bump qs from 6.15.2 to 6.16.0 in /mcp-server ([409](https://github.com/First-AI-Movers/articles/pull/409))
- chore(deps): bump the npm-minor-patch group across 2 directories with 4 updates ([418](https://github.com/First-AI-Movers/articles/pull/418))
- chore: retire the one delivery-closeout artifact [First-AI-Movers/agent-toolkit#3311] ([397](https://github.com/First-AI-Movers/articles/pull/397))
- chore(3311): retire ROADMAP.md and the machinery that maintained it [#3311] ([392](https://github.com/First-AI-Movers/articles/pull/392))
- chore(ci): pin the two third-party actions to commits, not moving tags ([390](https://github.com/First-AI-Movers/articles/pull/390))
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

## CI/CD

- ci(reconciliation): per-run eligibility-gate override for the read-only receipt delta [#423] ([429](https://github.com/First-AI-Movers/articles/pull/429))
- ci: retire the dormant zizmor advisory [agent-toolkit#3460] ([399](https://github.com/First-AI-Movers/articles/pull/399))
- ci(aeos): adopt the post-main smoke rail — smoke only, revert not armed ([387](https://github.com/First-AI-Movers/articles/pull/387))

## Other Changes

- ingest(articles): recover missed Airtable batch 11 ([439](https://github.com/First-AI-Movers/articles/pull/439))
- ingest(articles): recover missed Airtable batch 10 ([438](https://github.com/First-AI-Movers/articles/pull/438))
- ingest(articles): recover missed Airtable batch 09 ([437](https://github.com/First-AI-Movers/articles/pull/437))
- ingest(articles): recover missed Airtable batch 08 ([436](https://github.com/First-AI-Movers/articles/pull/436))
- ingest(articles): recover missed Airtable batch 07 ([435](https://github.com/First-AI-Movers/articles/pull/435))
- ingest(articles): add articles from Airtable ([433](https://github.com/First-AI-Movers/articles/pull/433))
