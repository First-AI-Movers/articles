# Article Summaries

> **CI automation:** for the plan to automatically generate summaries for fresh (recently published) articles via a reviewed pull request — and its safety guardrails — see [`SUMMARY_CI_AUTOMATION_PRD.md`](./SUMMARY_CI_AUTOMATION_PRD.md).

## Overview

Each article can have three optional summaries of different lengths:

- **Short** (~50 words): Single-paragraph punchline. Used for JSON-LD `description`, Open Graph tags, and social preview cards.
- **Medium** (~200 words): Structured synthesis for LLM context windows and newsletter snippets.
- **Long** (~500 words): Comprehensive overview for research briefs and citation digests.

## Review Workflow

Summaries are generated into review files (`summaries/<slug>.review.md`) with **Status: draft**. A human reviewer must:

1. Read the review file
2. Edit summaries for accuracy, tone, and voice
3. Change `Status: draft` to `Status: approved`
4. Run `--apply-approved` to write the summaries into `metadata.json`

Only approved summaries are published. Draft summaries are never used by the build.

## Usage

```bash
# Dry-run preview (default, no writes)
python3 tools/build_summaries.py --dry-run --slug my-article

# Generate review files with the mock provider (no API key needed)
python3 tools/build_summaries.py --write-review-files --limit 5 --provider mock

# Apply approved review files to metadata.json
python3 tools/build_summaries.py --apply-approved --slug my-article

# Apply even if some lengths are missing
python3 tools/build_summaries.py --apply-approved --slug my-article --allow-partial
```

## Providers

- `mock` — deterministic synthetic summaries for testing. No API key.
- `manual` — paste your own summaries into the review file.
- `anthropic` / `openai` — live LLM calls (stubs; requires SDK + API key + `--allow-network`).

## File Layout

```
articles/
  2026-04-01-my-article/
    metadata.json   ← updated by --apply-approved
    article.md
summaries/
  my-article.review.md   ← created by --write-review-files, reviewed by human
```

## Safety

- `--dry-run` (default) never writes files or calls the network.
- Real LLM calls require `--write-review-files`, a provider, an API key, and `--allow-network`.
- Metadata writes are atomic via `_atomic_io.atomic_write_json`.
- No article metadata is modified during the infrastructure phase.

---

## Automated Summary Pipeline — Sprint Closeout

The automated summary pipeline (`tools/run_summary_batch.py`) ran for 11
batches against the missing-summary backlog. This section records the
result, what we learned from each intervention, the default operating
mode for future runs, and the stop conditions that should keep future
runs from repeating failed experiments.

### Cumulative result

| Metric | Value |
| --- | :-: |
| Articles selected across all batches | 2150 |
| Articles applied (dual-verifier AUTO_APPROVE) | 396 |
| Cumulative apply rate | 18.4% |
| Cumulative cost | ~$28.73 |

A meaningful share of the original missing-summary backlog was cleared.
The remaining backlog is structurally hard: thin sources, dated
specifics, or named-entity claims that the dual verifier correctly
refuses to invent.

### Intervention evidence

What worked:

- **JSON-shape hardening** of the MiniMax envelope eliminated
  generation_failed errors. After the corrective-retry path landed,
  generation_failed stayed at or below 1% across all subsequent
  batches.
- **DeepSeek fallback for long-only undersize** recovered articles
  where MiniMax persistently underproduced `summary_long`. The
  fallback activation predicate restricts the path to its intended
  shape (`summary_long` BELOW minimum, no other gate issues) and
  correctly steps aside on every other failure mode.

What partially worked:

- **Prompt grounding hardening** (explicit source-fidelity rules,
  dated-claim rules, expand-via-reasoning instruction) raised the
  apply rate on the cohort where it was first measured. It did not
  generalize to the harder residual cohort.
- **Long-summary expansion softening** (restate-core-argument-first,
  lower-middle long target, forbid-list against decision criteria /
  operational implications / workflow counts / governance details /
  author biography / strategic implications) reduced the
  over-expansion exception bucket. It did not restore the apply rate
  on the residual cohort.
- **Verifier-feedback repair loop, cycle 1**, produced modest measurable
  lift on the most common failure shape (`gate_undersize`). Repair
  converted approximately 3% of candidates on a 100-article diagnostic.

What did not work:

- **Verifier calibration was not the bottleneck.** A diagnostic over
  50 sampled exceptions found only one case where a calibrated rubric
  would safely move HUMAN_REVIEW to AUTO_APPROVE. The verifier is
  firing correctly on real source-fidelity and dated-claim issues.
- **Verifier-feedback repair loop, cycle 2**, added essentially no
  marginal value. A 100-article diagnostic at `--max-repair-cycles 2`
  produced fewer total repair conversions than the same scale at
  `--max-repair-cycles 1`. The repair feedback signal extracts its
  lift on cycle 1.

### Default operating mode for future runs

For new articles or fresh missing-summary candidates, the default mode
is:

1. **Start with small batches** (`--limit 50` to `--limit 100`).
   Confirm the apply rate before committing batch-scale budget.
2. **Use the DeepSeek fallback** for long-only undersize:
   `--enable-fallback-on-undersize`.
3. **Use the repair loop with cycle 1 only**:
   `--enable-verifier-repair-loop --max-repair-cycles 1`.
4. **Do not use** `--max-repair-cycles 2` in default runs. Cycle 2 is
   reserved for explicitly authorized small diagnostics only.
5. **Do not run a broad sweep of the existing hard residue** without
   source enrichment or editorial review (see escalation paths below).
6. **Keep the dual-verifier AUTO_APPROVE boundary intact**. Never
   pass `--single-verifier` or any flag that weakens the metadata
   write gate.

Public-safe command shape for a default run (the secret-manager
wrapper injects keys at runtime; concrete project/config names belong
in operator-local environment, not in committed text):

```bash
REPORT=<outside-repo temporary report path>

doppler run -- python3 tools/run_summary_batch.py \
  --batch \
  --limit 100 \
  --allow-network \
  --max-budget-usd 5.00 \
  --apply-auto-approved \
  --enable-fallback-on-undersize \
  --enable-verifier-repair-loop \
  --max-repair-cycles 1 \
  --report-path "$REPORT"
```

### Stop conditions

A batch (or the bulk-automation programme as a whole) should stop and
trigger a reassessment when any of the following holds:

- **Apply rate below 18%** on a non-trivial sample
  (`--limit 50` or larger). Below 18% has consistently been the band
  where prompt-side and feedback-side levers stopped paying back.
- **Per-applied cost materially above prior baseline** (the
  cumulative `$/applied` figure has hovered around $0.06–$0.07;
  rates above ~$0.15 on a non-cohort-anomaly batch are a signal that
  the marginal pipeline cost no longer pays back).
- **Repair conversions below 3 per 100** with the repair loop
  enabled. Below this rate the repair signal is not adding value.
- **Repeated undersize / gate failures dominate** the exception mix
  (substantially more than 50% of exceptions are word-count failures
  rather than verifier truthfulness rejections). This points to
  source-thinness as the root cause, not prompt-tuning territory.
- **Source-fidelity issues dominate** the exception mix at a level
  the prompt cannot reduce further (hallucination + dated-claim
  combined share above ~70% of substantively-flagged exceptions).

### Escalation paths

When a stop condition fires, the next intervention is not another
prompt revision. Escalate to one of:

1. **Source enrichment design.** Extract a structured "key claims"
   block per thin-source article via LLM + editorial review, then
   feed that enriched substrate to the generator. Largest scope,
   highest ceiling. Should be designed as its own initiative with an
   ADR and editorial review process; this is not a single-PR change.
2. **Editorial review queue.** Route the hardest residue to manual
   summary writing. Cheaper than (1) for the long tail; loses the
   automation property but preserves quality.
3. **Relaxed long-summary band.** Only with explicit operator
   approval. The hard band has been preserved across all interventions
   (`summary_long`: 430–570 words). Relaxing the lower bound to e.g.
   400 words is a tooling change that would let more thin-source
   articles pass the deterministic gate, but it changes the public
   surface of the summary corpus and should not be done without
   explicit approval.
4. **Model-swap diagnostic.** Test an alternative primary generator
   on a controlled sample (`--limit 50`, outside-repo summaries
   directory, no metadata apply). The dual-verifier AUTO_APPROVE
   gate must remain intact in any model-swap diagnostic. Use a
   tooling PR to add the provider, run the diagnostic, decide based
   on the same metrics in the stop conditions above.

### Pipeline components reference

- Generator: MiniMax-M2 via `tools/build_summaries.py`.
- Generator-side retries: corrective JSON retry and undersize retry,
  bounded.
- Long-undersize fallback: DeepSeek (`_is_long_undersize_only`
  predicate gates activation).
- Repair loop: `_call_repair_once` with `REPAIR_SYSTEM_PROMPT` and a
  sanitized feedback packet; re-runs the deterministic gate and
  both verifiers after each repair attempt.
- Deterministic gate: `tools/summary_quality.check_summaries` with
  hard word bands 40–60 / 170–230 / 430–570.
- Verifiers: OpenAI primary + Anthropic secondary. Dual-verifier
  AUTO_APPROVE required for any metadata write.
- Metadata application: `--apply-auto-approved` flag; atomic writes;
  no draft-status review file is ever applied.

### What the sprint did not change

These boundaries were preserved across every batch and every
intervention and remain the production contract:

- Deterministic gate hard bands (40–60 / 170–230 / 430–570).
- JSON envelope and required-keys rules.
- DeepSeek fallback activation predicate (`_is_long_undersize_only`).
- Verifier rubric.
- Dual-verifier AUTO_APPROVE requirement for any metadata write.
- `--apply-auto-approved` flag as the explicit metadata-write gate.
- Article body files. No article markdown was edited by automation.
