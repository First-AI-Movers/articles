# Identifier integrity — adoption evidence

This archive is enrolled in the Portfolio Identifier Integrity Factory
(root commission `First-AI-Movers/agent-toolkit#1848`). Adoption here is a **no-op**:
a manifest was added, and nothing was migrated.

A no-op is the easiest result to fake — "we looked and found nothing" and "we never
really looked" produce the same sentence. This document exists so the two can be told
apart. It records what was walked, what was not, and the seeded allocators that prove
the detector fires.

## The defect being governed

One failure class, and only one: an identifier whose uniqueness depends on a branch
reading the current maximum and incrementing locally (`max + 1`, "next free"). Two
branches read the same base, mint the same value, and collide **when the branches
merge**. The governing invariant:

```
identity  !=  ordering  !=  display number
```

An identifier issued at runtime by a datastore is *not* in this class — it is never
minted in the working tree, so no merge can collide on it. This archive has no
database at all.

## Why this archive is already safe

Article identity is the directory name `YYYY-MM-DD-<slug>`, built at ingest from the
publication date plus the publishing platform's slug
(`tools/ingest_airtable.py` `_build_folder_name`). It is chosen from content the author
already holds — never read back from repository state. Two authors ingesting
simultaneously cannot collide by consulting a shared counter, because there is no
counter to consult.

Collisions are handled by **idempotent skip**, not increment: `tools/ingest_airtable.py`
returns the existing folder when the folder, normalized title, or normalized canonical
URL already exists. Incrementing on collision is precisely the behaviour the factory
hunts; returning the existing record is its opposite.

| Namespace | Identity | Result |
|---|---|---|
| `article-identity` | `YYYY-MM-DD-<slug>` | already safe |
| `canonical-topic-vocabulary` | topic display-name string | already safe |
| `series-order` | kebab-case series slug; `series_order` is display-only | already safe |
| `decision-record` | `adr-001` frozen; future records use a semantic slug | already safe |
| `ingest-batch-label` | human workflow input, reaches no artifact | already safe |
| `roadmap-track-label` | hand-written planning label | already safe |

Several of these *have* an ordering — publication date, series reading order, roadmap
sequence. None uses it as identity, which is the distinction the invariant draws.

## Scan denominator — what was and was not walked

Evidence pinned at `61adcb85468d7f6a3fdbe22534ac06eb3a5ee5d6`.

**Walked:** every file git tracks. An untracked file cannot appear in a merge, so it is
outside the domain by construction rather than by omission.

**Result: zero allocation-class findings at any confidence.** Not "zero blocking
findings" — zero hits of `max-plus-one`, `next-free`, `shared-counter`, or
`unstable-uuid-input` anywhere on the tracked surface. The 48 advisory findings the
scanner does report are:

* 44 × `fixed-width-assumption`, all in `tools/`, all date formatting of the shape
  `f"2026-04-{i + 1:02d}"` in test fixtures — a month number, not an identity;
* 4 × `duplicate-primary-store`, auto-classified false-positive: one article's prose
  replicated across the four generated surfaces that are *supposed* to carry it
  (`metadata.json`, `index.json`, `llms-full.txt`, the summary).

**Not walked, stated rather than implied:**

* Article, summary and translation **bodies** (~1,250 content files) were covered by
  pattern match only, not read individually. An allocation rule written in prose inside
  an article body would not surface. Low consequence: article prose is not executable
  and is immutable once published.
* `embeddings.parquet` is binary; its schema was read from the producer
  (`tools/build_embeddings.py`) rather than from the file.
* Live GitHub state — branches, open PRs, issue bodies, workflow-run history — was not
  queried. A convention living only in a PR comment thread would be invisible.
  `.github/ISSUE_TEMPLATE/*` and the PR template *were* in scope and contain no
  allocation instruction.

### What the scan cannot find, even in principle

The scanner detects **tree-local allocation mechanisms**. It has no pattern for
`AUTOINCREMENT`, a SQL sequence, or an identity column — correct for the domain, since
a datastore-issued value is never minted in the tree. So:

> `undeclared_candidates: 0` means *no undeclared tree-local allocator on the tracked
> surface*. It does not mean a repository has no undeclared identity namespaces.

For this archive the distinction is moot — there is no database — but the claim is
worth stating at its true width rather than at a flattering one.

## Detection-power attestation

A detector that has never been shown to fire is indistinguishable from one that is
switched off. Synthetic allocators were seeded into a throwaway worktree at the pinned
SHA, staged so the scanner could see them, scanned, and discarded. **No seeded file was
committed and none appears in this branch.**

| # | Seed | Placement | Outcome |
|---|---|---|---|
| S0 | none (control) | — | `undeclared_candidates=0`, 0 blockers |
| S1 | `max(existing_ids) + 1` | undeclared path | **detected — `unowned-allocator`, gates** |
| S2 | `max(existing) + 1` | undeclared path | not detected (see below) |
| S3 | `max(existing) + 1` | declared producer path | not detected (see below) |
| S4 | `next free` prose | undeclared path | **detected — `unowned-allocator`, gates** |
| — | control repeated after every seed | — | returns to 0/0 |

S1 and S4 are the attestation: a real allocator planted in this archive is caught and
blocks, and the gate returns to clean when it is removed.

S2 and S3 are the honest boundary, and they were found by running the matrix rather
than by reasoning about it. A `max + 1` is promoted to blocking only at *high*
confidence, which requires an identifier-ish token (`id`, `num`, `seq`, `row`,
`record`, `entry`, `item`) **inside the `max(...)` parentheses**. `max(existing) + 1`
carries no such token, stays at medium confidence, and medium-confidence findings never
reach the blocking gate. The boundary is a deliberate trade — a broader matcher was
measured against a live repository during this campaign and produced 111 false
positives, which would have denied every real repository. A gate nobody can pass
protects nothing. But the trade should be visible, not discovered later.

This does not weaken the result for *this* archive: with **zero** allocation-class hits
at any confidence, there is nothing sitting in the medium band to be missed.

### A detector hole found by this attestation

The positive control failed on first run, against a seed named
`allocate_next_free_number` — a thoroughly ordinary way to name the very function being
hunted. The `next-free` pattern required a word boundary on both sides, and `_` and a
following letter are both word characters, so `next_free_number`, `nextFreeSlot`,
`next_available_id` and `allocate_next_free_number` all escaped a *high-confidence,
blocking* detector. The boundaries are now spelled out explicitly on both sides
(`tools/tests/test_identifier_namespaces.py`), with negative controls keeping
`next freedom` and `next availability` from matching. The correction was reported
upstream to the factory, where the same gap existed.

That is the argument for attestations over assertions: the hole was invisible to every
test that only asked whether the detector stayed quiet.

### One consequence worth naming

Adding that guard made the portfolio scanner report five `unowned-allocator` blockers
against this repository — every one of them pointing at the guard's own fixture
strings. The scanner reads a literal as a live mechanism and cannot distinguish test
data from production code.

Those lines now carry the scanner's own inline allowance,
`# identifier-integrity-allow: inert fixture`, which is a genuine suppression and is
recorded here as such rather than left to be discovered in a diff. It was preferred to
the alternative — assembling the fixture strings at runtime so no literal appears —
because a fixture that is spelled out and explicitly allowed stays readable and
greppable, whereas one disguised to slip past a detector teaches the next author to
hide from the tooling. Every allowance in this repository is on a test fixture; none is
on a producer. `grep -rn "identifier-integrity-allow" .` is the audit.

## Keeping it true

`tools/tests/test_identifier_namespaces.py` runs in CI on every pull request and needs
no external tooling — this repository defends its own manifest without another
repository being checked out. It:

* checks the manifest's structural claims against the tree it describes, including that
  every declared path still exists (the check that catches a manifest gone stale after
  a refactor);
* re-derives the "no branch-local allocation" claim from the producers, **two-sided** —
  proven to fire on seeded allocators and proven quiet on the benign arithmetic this
  repo genuinely contains (`max_retries + 1`, `{i + 1:02d}` dates, and
  `check_series.py`'s gap *validator*, which reads ordinals rather than minting them);
* runs a parallel-authoring canary: two authors, one base, no coordination — distinct
  identities, no shared path touched, either merge order yielding the same archive. The
  canary carries its own negative control proving it collides when pointed at `max + 1`,
  because a canary that cannot fail certifies nothing.

## Revisit triggers

Re-run the assessment if any of these becomes true:

* an article, topic, or series acquires a numeric identity minted from repository state;
* a datastore is introduced (the `AUTOINCREMENT` blind spot above starts to matter);
* `series_order` or a roadmap label becomes a filename, URL component, or foreign key;
* the ingest path stops handling collisions by idempotent skip.

## The risk that is actually here

Worth recording plainly, because it is *not* the one this factory governs: the real
exposure in this archive is identity **stability**, not identity allocation. Feed GUIDs
(`tag:articles.firstaimovers.com,<date>:<folder>`), `/articles/<slug>/` paths, and
`/topics/<slug>/` hubs are all externally consumed and all derived from strings that
are, mechanically, editable. Renaming a canonical topic silently re-mints an indexed
URL, and no redirect surface was evidenced. Global slug uniqueness is asserted in
`tools/rebuild_local.py` but ungated, while `/articles/<slug>/` is the rendered path.

Neither is a branch-local allocator and neither justifies a migration child here. Any
future work in this area should protect **renames**, not replace the allocator — there
is no allocator to replace.
