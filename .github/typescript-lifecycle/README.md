# TypeScript lifecycle advisory (vendored)

An **advisory, non-required** CI check that runs the Agent Toolkit TypeScript
lifecycle drift detector over this repo's two direct `tsc` surfaces —
[`mcp-server`](../../mcp-server) and [`og-worker`](../../og-worker) — to catch
TypeScript-lifecycle drift (a removed compiler option, a registry/lockfile
mismatch, a preview/stable channel surprise, a stale entry) after Dependabot
rebases. It reads only committed facts; it never runs `tsc`, installs anything,
networks, or needs secrets, and it **does not deploy**.

## Provenance (vendored — keep in sync)

- **Source:** `scripts/typescript_lifecycle_drift.py` in `First-AI-Movers/agent-toolkit`.
- **Pinned at:** `0f5d2894763aba2e95b6306aa83d039f2cbe1d00`.
- `typescript_lifecycle_drift.py` here is a **byte-identical vendored copy** (kept
  pristine so a re-sync is a clean diff). It is stdlib-only and read-only.
- **Re-sync:** copy the file from the pinned-or-newer agent-toolkit commit,
  re-run `python3 typescript_lifecycle_drift.py --self-test` (must pass), and bump
  the pin above. The canonical runbook is the `typescript-lifecycle` skill in
  agent-toolkit.

## Files

| File | Role |
|---|---|
| `typescript_lifecycle_drift.py` | vendored detector (advisory, read-only, stdlib). |
| `scan.json` | observed TypeScript surfaces (`typescript-workspace-scan/v1`). |
| `registry.json` | per-package lifecycle registry (`typescript-lifecycle-registry/v1`). |

Regenerate `scan.json` / `registry.json` when a manifest, lockfile, `tsconfig`, or
worker CI workflow changes on a tracked surface.

## Current state (verified 2026-07-12)

Both surfaces are **class A (direct-upgrade), on `typescript@7.0.2` (stable), CI
exercises `tsc --noEmit` + vitest + `wrangler --dry-run`, no compiler-API-embedding
tool** (no `typescript-eslint`/Volar/Angular) → no ecosystem blocker. Detector: **0
findings**. `tsconfig` uses `moduleResolution: bundler`, `module: esnext`,
`target: es2022`, `esModuleInterop: true` — none of the options removed in TS 7.

## Open sibling Dependabot PR compatibility with TypeScript 7 (§A10, verified 2026-07-12)

Inspection only — **not** authorized to merge these here.

| PR | Package | Surface | Class | Reason |
|----|---------|---------|-------|--------|
| #304 | `@modelcontextprotocol/sdk` 1.26→1.29 | mcp-server (prod) | **safe** | runtime dep; TS-version-agnostic |
| #305 | `@cloudflare/workers-types` 4→5 (major) | mcp-server (dev) | **safe** | ambient `.d.ts`; TS7-agnostic — a types major may surface type errors that the worker's own `tsc` CI catches, not a TS7 blocker |
| #306 | `@cloudflare/vitest-pool-workers` 0.16→0.18 | mcp-server (dev) | **safe** | test tooling; TS7-agnostic |
| #307 | `wrangler` 4.103→4.110 | mcp-server (dev) | **safe** | build tool; TS7-agnostic |
| #309 | `@cloudflare/vitest-pool-workers` 0.16→0.18 | og-worker (dev) | **safe** | test tooling; TS7-agnostic |
| #310 | `@cloudflare/workers-types` 4→5 (major) | og-worker (dev) | **safe** | ambient `.d.ts`; TS7-agnostic (as #305) |
| #311 | `wrangler` 4.103→4.110 | og-worker (dev) | **safe** | build tool; TS7-agnostic |
| #303 | `actions/cache` 5→6 | CI (Actions) | **unrelated** | GitHub Action, no TypeScript surface |
| #320 | `numpy` | tools (Python) | **unrelated** | different ecosystem |
| #321 | `pillow` | tools (Python) | **unrelated** | different ecosystem |

**None are blocked by TypeScript 7.** No compiler-API-embedding dependency is being
introduced. The two `@cloudflare/workers-types` majors are ambient type packages,
not TS-version gates — the per-worker `tsc --noEmit` CI is the real check.
