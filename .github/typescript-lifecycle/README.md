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
- **Re-sync:** copy the file from the pinned-or-newer upstream commit, re-run
  `python3 typescript_lifecycle_drift.py --self-test` (must pass), and bump the
  pin above.

`scan.json` (observed TypeScript surfaces) and `registry.json` (the per-package
lifecycle registry) are inputs to the detector. Regenerate them when a manifest,
lockfile, `tsconfig`, or worker CI workflow changes on a tracked surface.
