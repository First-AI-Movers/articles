# ADR-001: C2PA Content Credentials for the Article Archive

| Field | Value |
|---|---|
| **Status** | **Deferred** |
| **Date** | 2026-04-27 |
| **Deciders** | Archive maintainers (research stub) |
| **Epic** | E32 |

---

## Context

The EU AI Act (Regulation (EU) 2024/1689) entered into force on 1 August 2024. Article 50 imposes transparency obligations on providers and deployers of AI systems that generate synthetic content, including text. General applicability for GPAI providers and high-risk systems begins **2 August 2026**.

The C2PA (Coalition for Content Provenance and Authenticity) standard provides cryptographically signed "Content Credentials" to certify the origin and history of digital media. Version 2.4 was released in April 2026.

This ADR records the decision whether to adopt C2PA signing for the First AI Movers article archive.

---

## Decision

**Defer C2PA adoption indefinitely.** No signing, no manifests, no cryptographic credentials, no new dependencies, and no changes to article metadata or templates.

The decision will be **revisited** no earlier than 2 August 2026 or when CLI tooling for signing Markdown/HTML manifests stabilises, whichever comes later.

---

## Consequences

### Positive

- **Zero engineering overhead.** No new dependencies, no certificate procurement, no key management, no CI changes.
- **No build-time impact.** The 800+ article static site build remains fast and simple.
- **No security surface area.** No private keys to protect, no certificate expiry to monitor, no revocation infrastructure.
- **Avoids premature standardisation.** C2PA's text/web support is immature; adopting now risks vendor lock-in to a moving target.
- **Avoids known validator issues.** Recent security research (arXiv:2604.24890v1) documents inconsistent validation, certificate expiry problems, and timestamp weaknesses in the C2PA ecosystem.

### Negative

- **No cryptographic provenance.** Readers cannot cryptographically verify that an article has not been tampered with since publication.
- **No C2PA badge.** The archive cannot display a Content Credentials indicator (e.g., "CR" icon) that some consumers may learn to trust.
- **Future regulatory risk.** If the EU AI Office's code of practice under Article 50 §7 mandates a specific technical standard for text, and that standard is C2PA, the archive may need to retrofit.
- **Platform risk.** If downstream platforms (LinkedIn, Medium, search engines) begin requiring or preferring C2PA-signed content, the archive's un-signed text may be deprioritised.

### Neutral / Accepted

- **Existing transparency signals remain.** Canonical URLs, JSON-LD, CC BY 4.0 license metadata, `<meta name="ai-training">`, and Git commit history continue to provide non-cryptographic provenance.
- **Research note lives on.** `docs/C2PA_RESEARCH.md` captures the current landscape and will be updated as the spec evolves.

---

## Alternatives Considered

### Alternative A: Sign generated HTML files with `c2patool` sidecar manifests

- **Approach:** Run `c2patool` during `rebuild_local.py` to generate a `.c2pa` sidecar for each HTML file.
- **Rejected:** Browsers do not fetch `.c2pa` sidecars for HTML documents. No standard `<link rel="c2pa">` or HTTP header exists. 800+ sidecar files would clutter the deployment with no consumer benefit.

### Alternative B: Embed C2PA manifests in PDF exports

- **Approach:** Generate a PDF version of each article and sign it with C2PA (PDF is a supported format).
- **Rejected:** The archive's primary output is HTML, not PDF. PDF generation would add significant build complexity (headless browser, typography, pagination) for a format that is not currently requested by readers.

### Alternative C: Add a C2PA-style JSON provenance block to article metadata

- **Approach:** Add a `provenance` field to `metadata.json` with assertions like `created_by`, `date_signed`, `tools_used`.
- **Rejected:** Without a cryptographic signature, this is just another metadata field. It does not provide tamper evidence and could create a false sense of security. The archive already has `author`, `published_date`, and `canonical_url`.

### Alternative D: Adopt W3C Verifiable Credentials or similar web-native standard

- **Approach:** Use W3C VC, DID, or similar for web-content provenance instead of C2PA.
- **Deferred:** These standards are even less mature than C2PA for this use case. Recorded as an open question in `docs/C2PA_RESEARCH.md` §8.

---

## Compliance Note

This ADR does **not** constitute legal advice. The assessment that Article 50 likely does not apply to this archive is based on:

1. The archive is not an AI system generating synthetic text.
2. The archive publishes original human-authored content under editorial responsibility (Article 50 §4, second subparagraph exemption).
3. The archive already signals openness and attribution through CC BY 4.0, canonical URLs, and machine-readable metadata.

**Recommendation:** Seek formal legal review before 2 August 2026 if the archive's regulatory status is uncertain.

---

## Links

- Research note: [`docs/C2PA_RESEARCH.md`](../C2PA_RESEARCH.md)
- Epic tracking: `ROADMAP.md` — E32
- EU AI Act Article 50: <https://artificialintelligenceact.eu/article/50/>
- C2PA Specification 2.4: <https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html>
