#!/usr/bin/env python3
"""Repo-local enforcement for identifier-namespaces.yaml.

This archive was adopted into the Portfolio Identifier Integrity Factory
(First-AI-Movers/agent-toolkit#1848) as a **no-op**: every namespace is already safe
and no migration was warranted. A no-op adoption is only worth the guard that keeps it
true, so nothing here trusts the manifest's own wording:

* the manifest's structural claims are checked against the tree it describes;
* the allocator guard re-derives the "no branch-local allocation" claim from the
  producers, and is proven two-sided — it fires on seeded allocators and stays quiet on
  the benign arithmetic this repo genuinely contains;
* the parallel-authoring canary proves the archive's own identity convention survives
  concurrent authoring in either merge order, and is likewise proven able to FAIL.

Deliberately dependency-free apart from PyYAML (a pinned requirement — see
tools/requirements.txt, which warns against importorskip for exactly this reason).
The portfolio scanner is NOT imported: this repository must be able to defend its own
manifest without another repository being checked out.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "identifier-namespaces.yaml"

# The identity classes this archive is allowed to declare. `branch-local-sequential`
# is absent on purpose: if one ever appears here, this test should fail rather than
# quietly widen to accommodate it.
SAFE_IDENTITY_CLASSES = {"semantic-self-contained", "legacy-frozen"}


@pytest.fixture(scope="module")
def manifest():
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# 1. The manifest describes THIS tree
# --------------------------------------------------------------------------------------


def test_manifest_exists_and_is_wellformed(manifest):
    assert manifest["schema"] == "identifier-namespace-manifest/v1"
    assert manifest["schema_version"] == 1
    assert manifest["repository"] == "First-AI-Movers/articles"
    assert manifest["namespaces"], "a manifest with no namespaces proves nothing"


def test_namespace_ids_are_unique_and_repo_scoped(manifest):
    ids = [ns["namespace_id"] for ns in manifest["namespaces"]]
    assert len(ids) == len(set(ids)), f"duplicate namespace_id: {ids}"
    for nsid in ids:
        assert nsid.startswith("NS:articles:"), nsid


def test_every_declared_path_exists(manifest):
    """A manifest that names a path this repo does not have is not describing this repo.

    This is the check that catches a manifest going stale after a refactor: the
    declaration keeps asserting coverage of a producer that has since moved or gone.
    """
    missing = []
    for ns in manifest["namespaces"]:
        for key in ("producer_paths", "consumer_paths", "proof_refs"):
            for rel in ns.get(key) or []:
                if not (REPO_ROOT / rel).exists():
                    missing.append(f"{ns['namespace_id']}.{key}: {rel}")
    assert not missing, "declared paths that do not exist:\n  " + "\n  ".join(missing)


def test_no_namespace_is_unsafe_or_needs_migration(manifest):
    """The no-op claim, stated as an assertion instead of a sentence."""
    offenders = []
    for ns in manifest["namespaces"]:
        if ns["safety"] != "safe":
            offenders.append(f"{ns['namespace_id']}: safety={ns['safety']}")
        if ns["identity_class"] not in SAFE_IDENTITY_CLASSES:
            offenders.append(f"{ns['namespace_id']}: identity_class={ns['identity_class']}")
    assert not offenders, "no-op adoption contradicted:\n  " + "\n  ".join(offenders)


def test_ordering_is_never_identity(manifest):
    """identity != ordering != display number — the factory's whole invariant.

    Several namespaces here legitimately HAVE an ordering (publication date, series
    reading order, roadmap sequence). None may use it as identity.
    """
    for ns in manifest["namespaces"]:
        ordering = ns["ordering_semantics"]
        assert ordering["ordering_is_identity"] is False, ns["namespace_id"]


def test_no_numeric_alias_is_declared_primary(manifest):
    for ns in manifest["namespaces"]:
        alias = ns.get("alias_policy") or {}
        if alias.get("has_numeric_alias"):
            assert alias.get("never_primary") is True, ns["namespace_id"]
            assert alias.get("minimum_display_width", 0) >= 5, ns["namespace_id"]


def test_immutable_legacy_examples_are_still_resolvable(manifest):
    """`adr-001` is cited from four docs and pinned in five tests; it must stay put."""
    adr = next(ns for ns in manifest["namespaces"]
               if ns["namespace_id"] == "NS:articles:decision-record")
    assert adr["legacy_policy"]["immutable"] is True
    assert (REPO_ROOT / "docs/decisions/adr-001-c2pa-content-credentials.md").exists(), (
        "the one legacy decision record moved; the manifest promises it never would"
    )


# --------------------------------------------------------------------------------------
# 2. The allocator guard — the no-op claim, re-derived
# --------------------------------------------------------------------------------------

# The two HIGH-confidence branch-local allocation forms the portfolio factory gates on.
# Kept deliberately narrow: a broad `\bmax\b.*\+\s*1` matcher was measured against a real
# repository during this campaign and produced 111 false positives, which would make the
# guard useless by making it unpassable. Narrow-and-true beats broad-and-ignored.
#
# The `next-free` boundaries are not the obvious `\b...\b`, because `_` and a following
# letter are both word characters. A plain trailing `\b` misses
# `next_free_number` and `nextFreeSlot`,   # identifier-integrity-allow: named, not used
# and a leading `\b` misses
# `allocate_next_free_number`,              # identifier-integrity-allow: named, not used
# which are the three most natural ways to actually NAME this allocator. Both boundaries
# are therefore spelled out: any non-alphanumeric neighbour, or a camelCase hump.
# `(?-i:...)` keeps the case-sensitive parts case-sensitive under the outer `(?i)`, which
# is what stops `next freedom` and `next availability` from matching.
_PRE = r"(?:(?<![A-Za-z0-9])|(?-i:(?<=[a-z])(?=[A-Z])))"
_SUF = r"(?:\b|(?-i:[_A-Z0-9]))"

ALLOCATOR_PATTERNS = (
    ("max-plus-one", re.compile(
        r"(?i)\b(max|highest|last)\w*\s*\([^)]*(id|num|seq|adr|aor|row|record|entry|item)"
        r"[^)]*\)\s*\+\s*1")),
    # identifier-integrity-allow: this is the detector itself, not an allocator
    ("next-free", re.compile(rf"(?i){_PRE}next[\s_-]*(free|available|unused){_SUF}")),
)

# Producers of a repo-minted identity. Consumers that only READ an identity cannot mint a
# colliding one, so they are out of scope by construction rather than by omission.
PRODUCER_FILES = (
    "tools/ingest_airtable.py",
    "tools/ingest_article.py",
    "tools/recover_airtable_backlog.py",
    "tools/rebuild_local.py",
    "tools/normalize_tags.py",
    "tools/check_series.py",
)


def _find_allocators(text: str) -> list[str]:
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        # Strip trailing comments: a comment describing an allocator is prose, not an
        # allocator. This campaign hit that inversion four separate times.
        code = line.split("#", 1)[0]
        for name, pattern in ALLOCATOR_PATTERNS:
            if pattern.search(code):
                hits.append(f"{name} @ line {line_no}: {line.strip()}")
    return hits


def test_no_producer_allocates_from_a_maximum():
    """The claim the manifest makes, checked against the code rather than believed."""
    offenders = {}
    for rel in PRODUCER_FILES:
        path = REPO_ROOT / rel
        assert path.exists(), f"declared producer vanished: {rel}"
        hits = _find_allocators(path.read_text(encoding="utf-8"))
        if hits:
            offenders[rel] = hits
    assert not offenders, (
        "branch-local identifier allocation appeared in a producer. Article identity is "
        "YYYY-MM-DD-<slug> with idempotent-skip on collision; minting from a maximum "
        "reintroduces the merge-collision class this repo was adopted as free of:\n"
        + "\n".join(f"  {k}: {v}" for k, v in offenders.items())
    )


#
# Every string below is INERT TEST DATA the guard is pointed at, never code this repo
# runs. The portfolio scanner reads literals as live mechanisms and cannot tell the
# difference, so each line carries the scanner's own reason-bearing allowance rather
# than being obfuscated past it — a fixture spelled out and explicitly allowed stays
# readable and greppable; one disguised to slip past a detector teaches the next author
# the wrong lesson and silently rots.
@pytest.mark.parametrize("seeded", [
    'return max(existing_ids) + 1',                 # identifier-integrity-allow: inert fixture
    'next_number = max(record_numbers) + 1',        # identifier-integrity-allow: inert fixture
    'n = highest_entry_id(rows) + 1',               # identifier-integrity-allow: inert fixture
    '    slug = allocate_next_free_number(rows)',   # identifier-integrity-allow: inert fixture
    'def getNextAvailableId(self):',                # identifier-integrity-allow: inert fixture
    'idx = self._next_unused_index()',              # identifier-integrity-allow: inert fixture
    'return the next available article number',     # identifier-integrity-allow: inert fixture
])
def test_allocator_guard_fires_on_seeded_allocations(seeded):
    """POSITIVE CONTROL.

    A guard that has never been shown to fire is indistinguishable from one that is
    switched off. Every pattern above must be demonstrably reachable, or removing it
    would silently cost nothing.
    """
    assert _find_allocators(seeded), f"guard failed to detect a real allocator: {seeded!r}"


@pytest.mark.parametrize("benign", [
    'folder = f"2026-04-{i + 1:02d}-article-{i}"',   # date formatting, not allocation
    'max_retries = max_retries + 1',                  # a bound, not an identity
    'expected = list(range(1, len(sorted_orders) + 1))',  # check_series.py gap VALIDATOR
    'timeout = max(timeout_seconds, 1) + 1',          # a bound again
    '# take the max id and add 1  -- describing the anti-pattern, not doing it',
    'the next freedom to consider',                   # `free` continuing into a word
    'check the next availability window',             # ditto for `available`
])
def test_allocator_guard_stays_quiet_on_benign_arithmetic(benign):
    """NEGATIVE CONTROL.

    Both directions matter. A guard that fires on `max_retries + 1` gets suppressed by
    the first engineer it inconveniences, and a suppressed guard protects nothing. The
    last case is the comment-stripping rule: prose ABOUT an allocator is not one.
    """
    assert not _find_allocators(benign), f"false positive on benign code: {benign!r}"


def test_no_producer_carries_a_scanner_allowance():
    """The suppression mechanism must not become the hole.

    `identifier-integrity-allow:` tells the portfolio scanner to ignore a line. That is
    correct on the inert fixtures above and indefensible on a producer, where it would
    silence a live allocator with a comment. Allowances are legal here only in tests.
    """
    token = "identifier-integrity" + "-allow:"   # split so this line is not itself one
    offenders = [
        rel for rel in PRODUCER_FILES
        if token in (REPO_ROOT / rel).read_text(encoding="utf-8")
    ]
    assert not offenders, (
        "a producer suppressed the identifier-integrity scanner; an allocator can hide "
        f"behind that comment: {offenders}"
    )


# --------------------------------------------------------------------------------------
# 3. The parallel-authoring canary
# --------------------------------------------------------------------------------------


def _author_article(published_date: str, slug: str) -> dict:
    """This archive's real identity rule, in miniature.

    Mirrors tools/ingest_airtable.py `_build_folder_name`: identity is chosen from
    content the author already has, never from repository state.
    """
    return {"id": f"{published_date}-{slug}", "touches": {f"articles/{published_date}-{slug}/"}}


def _author_by_max_plus_one(existing_ids: list[int]) -> dict:
    """The unsafe counterfactual, for the canary's own negative control."""
    nxt = (max(existing_ids) if existing_ids else 0) + 1
    return {"id": f"{nxt:05d}", "touches": {f"articles/{nxt:05d}/", "articles/_index_counter"}}


def test_canary_two_branches_author_without_collision():
    """Two authors, one common base, no coordination."""
    branch_a = _author_article("2026-08-01", "designing-for-merge-safety")
    branch_b = _author_article("2026-08-01", "what-a-slug-is-worth")

    assert branch_a["id"] != branch_b["id"], "same-day articles must not share identity"
    assert not (branch_a["touches"] & branch_b["touches"]), (
        "the branches touched a common path — that is the shared-allocator failure"
    )


def test_canary_either_merge_order_yields_the_same_archive():
    """Merge order must not be load-bearing. If it is, the identity is really a counter."""
    base = {"2026-07-01-first"}
    a = _author_article("2026-08-01", "designing-for-merge-safety")["id"]
    b = _author_article("2026-08-01", "what-a-slug-is-worth")["id"]

    a_then_b = (base | {a}) | {b}
    b_then_a = (base | {b}) | {a}

    assert a_then_b == b_then_a
    assert len(a_then_b) == 3, "an identity was lost or overwritten by merge order"


def test_canary_ordering_survives_without_being_identity():
    """Publication order is derived at read time and never renumbers anything."""
    archive = [
        _author_article("2026-08-01", "what-a-slug-is-worth")["id"],
        _author_article("2026-07-01", "first")["id"],
        _author_article("2026-08-01", "designing-for-merge-safety")["id"],
    ]
    ordered = sorted(archive)
    # Ordering changed; identities did not.
    assert set(ordered) == set(archive)
    assert ordered[0] == "2026-07-01-first"


def test_canary_would_detect_the_unsafe_form():
    """NEGATIVE CONTROL on the canary itself.

    A canary that cannot fail certifies nothing. Run the identical two-branch scenario
    against `max + 1` and it must collide AND contend on a shared allocator — proving
    the passing cases above are passing for a reason.
    """
    base_ids = [1, 2, 96]
    branch_a = _author_by_max_plus_one(base_ids)
    branch_b = _author_by_max_plus_one(base_ids)

    assert branch_a["id"] == branch_b["id"] == "00097", (
        "the unsafe form failed to collide; the canary is not exercising what it claims"
    )
    assert branch_a["touches"] & branch_b["touches"], "expected shared-allocator contention"
