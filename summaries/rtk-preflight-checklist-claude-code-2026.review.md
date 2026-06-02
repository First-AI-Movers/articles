# Summary Review — RTK Preflight Checklist: What to Inspect Before `rtk init -g`

Article folder: 2026-03-23-rtk-preflight-checklist-claude-code-2026
Canonical URL: https://radar.firstaimovers.com/rtk-preflight-checklist-claude-code-2026
Generated at: 2026-06-02
Model: minimax (MiniMax-M2)

## 50-word summary

RTK preflight checklist for Claude Code users covers eight critical steps before running `rtk init -g`. The checklist verifies the actual problem being solved, confirms authentic RTK installation, inspects config changes, reviews hook scripts, pilots with real commands, and maintains rollback options. Security considerations include hook permissions and global settings impact.

## 200-word summary

RTK (Rewrite Tool Kit) offers a practical solution for Claude Code users experiencing token waste from noisy Bash output. Before installing RTK with `rtk init -g`, this eight-step preflight checklist ensures safe evaluation.

First, confirm whether Bash output specifically drives your token consumption, or if MCP responses or bloated prompts are the actual culprit. Second, verify you're installing the authentic RTK by navigating directly to the official repository rather than sponsored search results, as security researchers documented fake Claude Code installers in early 2026.

Third, check whether RTK is already present using `rtk --version` and `which rtk`. Fourth, choose your installation scope carefully: local for evaluation, global only after establishing trust, or hook-only for reduced context overhead.

Fifth, preview all configuration changes using `rtk init -g --no-patch` before applying them. Sixth, review the hook script itself—Anthropic's documentation confirms hooks execute with full user permissions, making thorough code review essential.

Seventh, pilot RTK with actual commands from your workflow like pytest, git status, or docker logs rather than toy examples. Finally, prepare rollback procedures including uninstall commands and configuration backups before installation.

The core principle: audit first, pilot second, standardize last. RTK appears well-engineered with SHA-256 integrity verification and broad command coverage, but the installation fundamentally adds a hook-based rewrite layer requiring careful evaluation.

## 500-word summary

RTK (Rewrite Tool Kit) addresses a genuine pain point for Claude Code users: verbose Bash output that consumes context tokens and reduces the AI assistant's effectiveness. The tool uses a PreToolUse hook to rewrite commands like `git status` into `rtk git status`, then feeds Claude Code a compressed version of the output instead of the raw terminal dump. Before running `rtk init -g`, this preflight checklist treats RTK as infrastructure requiring inspection rather than a theme to install casually.

The first checklist item confirms whether Bash output specifically drives your token waste. RTK's architecture rewrites commands around Bash, so if token bloat comes from giant MCP responses, bloated project instructions, or long-lived sessions, RTK will only partially help. Check whether MAX_MCP_OUTPUT_TOKENS might address the issue first.

Second, verify you're installing the authentic RTK, not malware. Check Point disclosed patched Claude Code vulnerabilities in February 2026 involving malicious project configurations. Separate March 2026 reporting from Malwarebytes and Bitdefender documented fake Claude Code install pages and sponsored-search traps pushing malicious one-liners through cloned documentation. Navigate directly from the official RTK repo rather than sponsored results.

Third, check whether RTK is already installed using `rtk --version`, `rtk gain`, and `which rtk`. If it's present, inspect the current installation before changing anything.

Fourth, choose your scope deliberately: local for evaluation, global only after establishing trust, or hook-only for reduced context overhead. User settings in ~/.claude/settings.json apply across all projects unless deliberately scoped.

Fifth, inspect exactly what RTK will write using `rtk init -g --no-patch`, which prints the JSON snippet without patching your config. Review whether it targets PreToolUse and points to the correct hook path.

Sixth, read the hook script like infrastructure code. Anthropic explicitly states hooks run with full user permissions and can modify, delete, or access anything your account can access. Review what gets rewritten, what passes through, parser failure behavior, whether useful debugging detail gets suppressed, and whether environment variables or sensitive paths are touched. The March 2026 update added SHA-256 hook integrity verification, but your own review remains essential.

Seventh, pilot with real commands from your workflow—pytest, git status, docker compose logs, psql, aws—rather than toy examples. Measure token reduction while ensuring Claude still receives the right signal and that useful edge-case detail doesn't disappear.

Eighth, keep the rollback path ready. Document `rtk init -g --uninstall` and know how to restore from ~/.claude/settings.json.bak backups.

The evaluation principle is straightforward: audit first, pilot second, standardize last. RTK appears well-engineered with SHA-256 integrity verification and broad command coverage including AWS CLI and psql, but the installation fundamentally adds a hook-based rewrite layer into Claude Code's execution path, requiring the same careful evaluation you'd give to any infrastructure component.

## Review status

Status: approved
Reviewer:
Reviewed at:

## Notes

- Gate status: PASS
- Retries used: 0
- Corrective JSON retries used: 0
- Fallback attempts used: 0
- Fallback: not invoked
- Termination: PASS
- Estimated cost (USD): 0.004924
- Word counts: short=51, medium=213, long=446

## Verification

Verification status: AUTO_APPROVE
Deterministic gate: PASS
Primary verifier: openai/gpt-5.4-mini — AUTO_APPROVE
Secondary verifier: anthropic/claude-haiku-4-5-20251001 — AUTO_APPROVE
Fallback verifier: not-used
Single verifier: false
Estimated verifier cost (USD): 0.005813
Verified at: 2026-06-02

### Verification notes

- Merge rationale: both verifiers AUTO_APPROVE
- openai/gpt-5.4-mini: Covers the article’s checklist structure and main recommendations accurately.
- openai/gpt-5.4-mini: Preserves the key security and scope warnings around Claude Code hooks.
- openai/gpt-5.4-mini: No invented sections or vendor claims beyond the source.
- anthropic/claude-haiku-4-5-20251001: All three summaries accurately reflect source content without invention or omission
- anthropic/claude-haiku-4-5-20251001: Specific dates (February 2026, March 2026) and technical details (SHA-256, PreToolUse) preserved correctly
- anthropic/claude-haiku-4-5-20251001: No volatile facts embedded; durable regulatory/security facts (Check Point disclosure, Malwarebytes/Bitdefender reporting) maintained with dates
