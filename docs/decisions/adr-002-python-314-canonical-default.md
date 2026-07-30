# ADR-002: Python 3.14 as the Canonical Tooling Runtime

| Field | Value |
|---|---|
| **Status** | **Accepted** |
| **Date** | 2026-07-29 |
| **Deciders** | Archive maintainers |
| **Campaign** | `ARTICLES-PYTHON-314-CANONICAL-ADOPTION-A` |

---

## Context

The archive's Python tooling and workflows currently select a mixture of
Python 3.11 and 3.12. The repository has no root declaration, so local
validation can also select the ambient host interpreter. That makes dependency
resolution, test behavior, and CI evidence depend on where a command happens
to run.

The operator toolchain and the active First AI Movers Python portfolio are
converging on Python 3.14. The archive's full tool suite is compatible with the
current Python 3.14 patch and current dependency releases. The NumPy `<2.5`
constraint and matching Dependabot ignore existed only to preserve the former
Python 3.11 baseline.

## Decision

Adopt Python 3.14 as the canonical default for local tooling and every active
GitHub Actions Python setup.

- `.python-version` contains the minor series `3.14`.
- Every `actions/setup-python` step reads that declaration through
  `python-version-file`; workflows do not carry independent default pins.
- The cookiecutter archive template ships the same declaration and reads it the
  same way, so a repository generated from it does not start on a retired
  default.
- The full pytest suite fails when its process is not Python 3.14. That test is
  the explicit declaration of the 3.14-only truth; `tools/` is not a
  distributable package and no `pyproject.toml` is introduced to carry a
  `requires-python` that nothing would consume.
- The obsolete NumPy `<2.5` cap and Dependabot suppression are removed.
- `tools/check_python_runtime_drift.py` rejects a returning active default.
  Historical evidence, dependency release-note text, and article prose are not
  active selectors and are out of its scope by construction.

Python 3.11, 3.12 or 3.13 may be restored only as an explicit rollback lane
carrying a named owner and an expiry date, after a demonstrated
incompatibility. The guard treats an expired rollback as a violation, so the
exception cannot silently become permanent. None of them remains an ordinary
default lane.

## Consequences

### Positive

- Local and CI validation resolve the same interpreter series.
- New workflows inherit runtime upgrades from one reviewed declaration.
- Current NumPy releases can flow through normal Dependabot review.
- Wrong-runtime failures occur before their output is accepted as canonical
  evidence.

### Negative

- Contributors need Python 3.14 or a compatible version manager.
- A dependency without Python 3.14 wheels may require a bounded upgrade or
  replacement before CI can pass.
- Changing the declaration restarts every Python workflow, increasing one-time
  migration compute.

### Non-functional impact

- **Cost:** one canonical test path replaces mixed-version repetition; no new
  hosted service or runner is added.
- **Latency:** dependency installation may change with 3.14 wheels, but the
  validation topology is unchanged.
- **Observability:** the declaration and runtime contract test make the selected
  version visible in both repository state and test failures.
- **Security:** action pinning, least-privilege permissions, and dependency
  review remain unchanged.
- **Scalability:** additional Python workflows consume the same declaration
  without adding another version-edit surface.
- **Maintainability:** one selector replaces per-workflow version literals and
  a version-specific dependency exception.

## Alternatives Considered

### Keep Python 3.11

Rejected. It preserves the dependency cap, conflicts with the portfolio
default, and leaves the operator's current toolchain on a different runtime
from CI.

### Move only to Python 3.12

Rejected. It is an unnecessary intermediate migration and would immediately
recreate the same drift against the authorized Python 3.14 target.

### Pin `3.14` independently in every workflow

Rejected. Repeated literals are easy to drift and require broad workflow edits
for every future patch-series decision.

## Validation

Acceptance requires:

1. the root declaration and runtime contract tests to pass under Python 3.14;
2. every workflow selector to read `.python-version`, in this repository and in
   the cookiecutter template;
3. the full repository pytest suite and required CI to pass on the exact PR
   head;
4. a clean active-selector sweep for 3.11, 3.12 and 3.13 outside historical
   evidence;
5. a dependency-install proof from a clean Python 3.14 environment, showing that
   every native dependency resolves to a prebuilt wheel rather than a source
   build;
6. negative controls proving the drift guard actually fails when a retired
   default returns — a guard never observed failing proves nothing;
7. exact-head merge and post-merge equality proof.

## Rollback

Revert the adoption commit, restoring the previous workflow selectors and the
NumPy `<2.5` compatibility cap together. Then run the full test suite and
required workflows on that exact rollback head. A rollback is incident
recovery, not a supported parallel default.
