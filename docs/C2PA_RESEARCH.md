# C2PA Content Credentials — Research Note (E32)

> **Status:** Research stub. No implementation commitment.  
> **Last reviewed:** 2026-04-27  
> **Revisit trigger:** CLI tooling for signing Markdown or HTML manifests stabilises; or EU AI Act Article 50 enforcement guidance (2 Aug 2026) clarifies obligations for static text archives.

---

## 1. What is C2PA?

The **Coalition for Content Provenance and Authenticity (C2PA)** is an open technical standard that embeds cryptographically signed metadata (a "manifest") into digital media files to record origin, edit history, and authorship. It was formed in 2021 from the merger of Adobe's Content Authenticity Initiative and Microsoft/BBC's Project Origin. The standard is maintained as a Joint Development Foundation project.

- **Official site:** <https://c2pa.org/>
- **Specification portal:** <https://spec.c2pa.org/>
- **Content Authenticity Initiative:** <https://contentauthenticity.org/>

A C2PA manifest (also called a **Content Credential**) contains:

- **Assertions** — claims about the asset (creator identity, tools used, edits made, AI-generation flags).
- **Cryptographic signature** — an X.509 PKI signature binding the manifest to the asset.
- **Hard or soft binding** — the manifest is either embedded in the file (hard) or referenced externally/watermarked (soft).

---

## 2. Current Specification State (April 2026)

| Version | Date | Key changes relevant to this archive |
|---|---|---|
| 2.2 | May 2025 | Baseline provenance for images, video, audio, PDF. |
| 2.3 | Jan 2026 | Live/broadcast video support (CMAF segment signing); no new document formats. |
| **2.4** | **Apr 2026** | New asset format support, new assertions, **JSON-based serialization** for Content Credentials. |

Sources:

- C2PA Technical Specification 2.4 landing page: <https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html>
- C2PA Explainer: <https://spec.c2pa.org/specifications/specifications/2.4/explainer/Explainer.html>

### 2.1 Supported file formats (as of 2.4)

- **Images:** JPEG, PNG, WebP, AVIF, HEIC/HEIF, TIFF, DNG, SVG, GIF
- **Video:** MP4, MOV, AVI
- **Audio:** WAV, MP3, M4A
- **Documents:** PDF
- **In development:** WebM, additional formats

**Notably absent:** Plain Markdown (`.md`), HTML (`.html`), JSON (`.json`), and XML (`.xml`). C2PA is fundamentally designed for *media assets* (binary files with defined box/container structures), not for static text documents served over HTTP.

Source: C2PA Wiki FAQ — <https://c2pa.wiki/getting-started/faq/>

---

## 3. EU AI Act Article 50 — Transparency Obligations

### 3.1 What Article 50 requires

**Regulation (EU) 2024/1689**, Article 50 (transparency obligations for AI systems), entered into force 1 August 2024. The key obligations for providers and deployers are:

1. **AI interaction disclosure** (§1) — Inform users they are interacting with an AI system, unless obvious.
2. **Synthetic content marking** (§2) — Providers of AI systems generating synthetic audio, image, video, **or text** must mark outputs in a **machine-readable format** detectable as artificially generated or manipulated.
3. **Deepfake disclosure** (§4) — Deployers generating or manipulating image/audio/video content must disclose it is artificial.
4. **Text disclosure** (§4, second subparagraph) — Deployers of AI systems generating or manipulating text published to inform the public on matters of public interest must disclose the text is artificially generated or manipulated. **Exemptions apply** if the content has undergone human review/editorial control and a natural or legal person holds editorial responsibility.

Source: <https://artificialintelligenceact.eu/article/50/> (annotated; see official EUR-Lex for authoritative text).

### 3.2 Enforcement timeline

- **2 August 2026** — General applicability of AI Act provisions, including Article 50 transparency obligations for GPAI providers and high-risk systems.
- The EU AI Office is tasked with encouraging codes of practice for detection and labelling (§7).

Source: AI Act Service Desk — <https://ai-act-service-desk.ec.europa.eu/>

### 3.3 Relevance to this archive

The First AI Movers article archive is a **static, human-edited, human-authored text corpus**. Key facts:

- **Not an AI system.** The archive does not generate synthetic text. It publishes original articles written by Dr. Hernani Costa.
- **Human editorial control.** All articles are authored by a natural person and published under editorial responsibility.
- **CC BY 4.0 licensed.** The archive already signals open use, including for AI training, with attribution requirements.

**Tentative assessment:** Article 50 §4's text-disclosure obligation likely **does not apply** to this archive because:

1. The archive is not an AI system generating text.
2. The exemption for human-reviewed content with editorial responsibility appears to cover original authored articles.

> ⚠️ **This is not legal advice.** The assessment is based on the published text of Article 50 as of April 2026. Formal legal review should be sought before August 2026 if the archive's status is ambiguous.

---

## 4. C2PA Tooling Landscape (April 2026)

### 4.1 Reference CLI: `c2patool`

The official C2PA Rust SDK ships with `c2patool`, a command-line utility for signing, reading, and verifying manifests.

Key capabilities:

- Sign assets with manifest definition JSON.
- Embed manifests or generate **sidecar** files (`.c2pa`).
- Generate **remote manifests** (embed a URL reference, host the `.c2pa` file separately).
- Validate signatures and extract certificate chains.

Example sidecar workflow:

```bash
# Generate an external manifest sidecar
c2patool sample/image.jpg -s -m manifest.json -o signed_image.jpg
# Produces signed_image.jpg + signed_image.c2pa
```

Source: `c2patool` docs — <https://opensource.contentauthenticity.org/docs/c2patool/docs/usage/>

### 4.2 SDKs

- **Rust:** `c2pa-rs` (reference implementation)
- **Python:** `c2pa-python` (bindings)
- **Node.js:** `c2pa-node-v2`
- **Java:** `c2pa-java`
- **C:** `c2pa-c`

### 4.3 Verification tools

- **Browser (no install):** <https://c2paviewer.com/> — drag-and-drop, WebAssembly-based local processing.
- **Official verify:** <https://contentcredentials.org/verify>
- **Browser extension:** Chrome/Edge Content Credentials extension.
- **CLI:** `c2patool <file>`

---

## 5. Gap Analysis — Why We Are Not Implementing Yet

### 5.1 No native text-document support

C2PA's embeddable formats (JPEG, PNG, MP4, PDF, etc.) do not include plain text formats. A static HTML site generated from Markdown has no "file" to sign at the point of consumption — the content is served over HTTP and rendered by a browser.

Potential workarounds and their problems:

| Approach | Problem |
|---|---|
| Sign the source `.md` files | Consumers never see the `.md`; the signed artifact is not what they read. |
| Sign the generated `.html` files | One manifest per HTML file; 800+ files to sign; manifests are stripped by any downstream scraping or re-encoding. |
| Sidecar `.c2pa` files alongside HTML | No browser or crawler knows to fetch them; no standard HTTP linking mechanism. |
| Remote manifest with URL embedded in HTML | C2PA spec supports remote references for *media* files, not HTML documents. No defined embedding method for HTML. |
| PDF export with embedded C2PA | PDF is supported, but the archive's primary output is HTML, not PDF. |

### 5.2 Static-site architecture mismatch

The archive is a **static site** (Markdown + JSON → Jinja2 → HTML). C2PA signing is designed for *assets* that travel as discrete files through production pipelines (camera → editor → platform → consumer). A static HTML page has no "file" lifecycle in the C2PA sense — it is generated, deployed, and consumed via HTTP.

### 5.3 Certificate and key management overhead

Production C2PA signing requires:

- An X.509 certificate from a trusted CA (DigiCert, GlobalSign, etc.) or self-signed for testing.
- Secure private-key storage (KMS or HSM recommended).
- Annual certificate costs (~$50–500/year).

For a research-only archive with no commercial distribution of media files, this overhead is disproportionate.

### 5.4 Maturity and security concerns

A January 2026 security analysis (arXiv:2604.24890v1, "Why the C2PA Specifications Fall Short") identified critical issues:

- Signed media can expire and become unverifiable when certificates lapse.
- Certificate revocation checking is inconsistent across validators.
- Timestamps are not always securely bound.
- Validation tools produce inconsistent results.
- The Pixel 10 Pro and C2PA 2.3 incorporated some fixes; version 2.4 (April 2026) did not address all concerns.

Source: <https://arxiv.org/html/2604.24890v1>

> "Premature adoption of C2PA could worsen the misinformation problem rather than solve it."

---

## 6. Existing Transparency Mechanisms in This Archive

The archive already implements several non-cryptographic transparency signals that partially address the goals of provenance and authenticity:

| Mechanism | What it does | Limitation |
|---|---|---|
| **Canonical URLs** | Every article points to its original publishing property. | Trust depends on the publisher, not cryptography. |
| **`robots.txt`** | Allows all crawlers; signals openness. | Does not certify authorship. |
| **`<meta name="ai-training">`** | Machine-readable AI-training permission signal. | Not a provenance standard; just a permission. |
| **JSON-LD structured data** | `author`, `datePublished`, `license` in every page. | Can be scraped and replayed without verification. |
| **`llms-full.txt` / `llms-recent.txt`** | Curated LLM-ingestion corpora with license headers. | Text can be copied without attribution. |
| **CC BY 4.0** | Legal license requiring attribution. | Enforcement is legal, not technical. |
| **Git commit history** | Immutable, signed Git commits for source changes. | Proves code history, not content provenance at consumption time. |

None of these are cryptographically tamper-evident at the point of reader consumption. However, they are **sufficient for the archive's current threat model**, which is:

- **Not** defending against state-level disinformation campaigns.
- **Not** distributing high-stakes media (video, images) where provenance is critical.
- **Is** making human-authored, editorially controlled text available for research, RAG, and reading.

---

## 7. Decision Register

| Date | Decision | Rationale | Status |
|---|---|---|---|
| 2026-04-27 | **Defer C2PA implementation.** | No supported text format; static-site architecture mismatch; disproportionate overhead; security concerns remain. | **Deferred** |
| 2026-04-27 | Revisit after 2 Aug 2026. | EU AI Act enforcement may clarify obligations for text archives; C2PA spec may add document/web support. | **Scheduled** |
| 2026-04-27 | Maintain existing transparency signals. | Canonical URLs, JSON-LD, license metadata, and AI-training manifest are sufficient for current use case. | **Active** |

Full ADR: [`docs/decisions/adr-001-c2pa-content-credentials.md`](decisions/adr-001-c2pa-content-credentials.md)

---

## 8. Open Questions

1. **Will C2PA 2.5+ add native HTML or Markdown support?** The spec has historically focused on media; document formats beyond PDF are not on the public roadmap.
2. **Will the EU AI Office's code of practice (Article 50 §7) recommend C2PA specifically for text?** As of April 2026, the code of practice is not final.
3. **Can a sidecar or HTTP header-based provenance standard emerge for web content?** The W3C Verifiable Credentials and related work may be more applicable to HTML than C2PA.
4. **Does the archive's AI-training permission posture (`llms-full.txt`, `<meta name="ai-training">`) satisfy any future "machine-readable format" requirement under Article 50 §2?** Unclear; the regulation does not specify formats.

---

## 9. References

1. C2PA Official Website — <https://c2pa.org/>
2. C2PA Technical Specification 2.4 — <https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html>
3. C2PA Explainer — <https://spec.c2pa.org/specifications/specifications/2.4/explainer/Explainer.html>
4. Content Authenticity Initiative — <https://contentauthenticity.org/>
5. `c2patool` Documentation — <https://opensource.contentauthenticity.org/docs/c2patool/docs/usage/>
6. EU AI Act Service Desk — <https://ai-act-service-desk.ec.europa.eu/>
7. EU AI Act Article 50 (annotated) — <https://artificialintelligenceact.eu/article/50/>
8. C2PA Wiki FAQ — <https://c2pa.wiki/getting-started/faq/>
9. "Why the C2PA Specifications Fall Short" — arXiv:2604.24890v1, 2026 — <https://arxiv.org/html/2604.24890v1>
10. Media Campus / C2PA Implementation Report (June 2025) — <https://mediacampus.nl/app/uploads/2025/06/Rapport-–-C2PA-nest-pas-une-pipe-–-Verkenning-implementatie-C2PA_jun25.pdf>

---

*This document is a living research note. Update it when new spec versions, tooling, or regulatory guidance are released. Do not treat it as legal advice.*
