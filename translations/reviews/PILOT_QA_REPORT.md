# E39b Pilot — Multilingual QA Report (Gate 2.5)

**Date:** 2026-04-30  
**Scope:** 1 article × 5 languages (ES, FR, DE, NL, PT)  
**Status:** Draft review files audited, edits applied, awaiting human approval

---

## 1. Executive verdict

**Approve with edits.**

All five translations are structurally sound, factually faithful to the original, and free of invented claims. The edits applied during this QA pass resolved terminology inconsistencies, grammatical errors, and formatting issues. No language requires regeneration.

However, **native review is still recommended** for all five languages before final approval, particularly for:
- Legal register precision (all languages)
- SME acronym conventions (ES "pyme" vs "PYME", NL "kmo" vs "KMO")
- Heading style guide compliance (PT sentence case confirmed; others should be checked)

---

## 2. Per-language verdict table

| Language | Verdict | Critical issues | Minor issues | Recommended action |
|---|---|---|---|---|
| **ES** | Approve with edits | 0 | 1 (repetition) | Apply edits ✅ Done; native review recommended |
| **FR** | Approve with edits | 0 | 2 (grammar, terminology inconsistency) | Apply edits ✅ Done; native review recommended |
| **DE** | Approve with edits | 0 | 1 (terminology inconsistency) | Apply edits ✅ Done; native review recommended |
| **NL** | Approve with edits | 0 | 1 (terminology confusion) | Apply edits ✅ Done; native review recommended |
| **PT** | Approve with edits | 0 | 1 (heading case) | Apply edits ✅ Done; native review recommended |

---

## 3. Per-language detailed notes

### Spanish (es)

**Terms checked:**
- ✅ Title: "Evaluación de conformidad con el Reglamento de Inteligencia Artificial de la UE"
- ✅ SME: "PYME" in title; "pyme" (7×) and "PYME" (2×) in body — natural Spanish usage
- ✅ Provider: "proveedor" (28×)
- ✅ Deployer: "implementador" (21×)
- ✅ Conformity assessment: "evaluación de conformidad" (4×)
- ✅ High-risk AI system: "sistema de IA de alto riesgo" (4×)
- ✅ Human oversight: "supervisión humana" (5×)
- ✅ CE marking: "marcado CE" (4×)
- ✅ Declaration of Conformity: "Declaración de Conformidad" (3×)
- ✅ EU AI Act: "Reglamento de Inteligencia Artificial de la UE" / "Reglamento de IA"

**Title assessment:** Natural and legally precise. Uses "Reglamento" (Regulation) correctly.

**Body-flow assessment:** Fluent. The TL;DR block renders correctly after `&gt;` cleanup.

**Required edit applied:**
- "Esta guía guía a los responsables" → "Esta guía orienta a los responsables" (repetition/typo)

**Native review still recommended?** Yes — confirm "RR. HH." abbreviation and legal register.

---

### French (fr)

**Terms checked:**
- ✅ Title: "Évaluation de conformité au Règlement européen sur l'intelligence artificielle"
- ✅ SME: "PME" (7×)
- ✅ Provider: "fournisseur" (28×)
- ✅ Deployer: "déployeur" (16×, after normalization)
- ✅ Conformity assessment: "évaluation de conformité" (3×)
- ✅ High-risk AI system: "système d'IA à haut risque" (4×)
- ✅ Human oversight: "surveillance humaine" (1×)
- ✅ CE marking: "marquage CE" (4×)
- ✅ Declaration of Conformity: "déclaration de conformité" (4×, lowercase in prose)
- ✅ EU AI Act: "Règlement européen sur l'intelligence artificielle" / "Règlement sur l'IA"

**Title assessment:** Natural. "au Règlement" is grammatically correct (masculine).

**Body-flow assessment:** Fluent and precise. Legal register is appropriate.

**Required edits applied:**
- "à la Règlement" → "au Règlement" (×2) — grammar fix for masculine noun
- "exploitant" → "déployeur" (×3) — terminology consistency with EU AI Act French official term

**Native review still recommended?** Yes — confirm "surveillance humaine" vs "supervision humaine" and legal register consistency.

---

### German (de)

**Terms checked:**
- ✅ Title: "Konformitätsbewertung nach der EU-KI-Verordnung"
- ✅ SME: "KMU" (7×)
- ✅ Provider: "Anbieter" (28×)
- ✅ Deployer: "Betreiber" (17×, after normalization)
- ✅ Conformity assessment: "Konformitätsbewertung" (11×)
- ✅ High-risk AI system: "Hochrisiko-KI-System" (2×) / "KI-System mit hohem Risiko" (5×)
- ✅ Human oversight: "menschliche Aufsicht" (1×) / "menschliche Überwachung" (1×)
- ✅ CE marking: "CE-Kennzeichnung" (4×)
- ✅ Declaration of Conformity: "Konformitätserklärung" (5×)
- ✅ EU AI Act: "EU-KI-Verordnung" (7×)

**Title assessment:** Natural German legal phrasing. "nach der EU-KI-Verordnung" is correct.

**Body-flow assessment:** Fluent. Compound nouns are well-formed.

**Required edit applied:**
- "Anwender" → "Betreiber" (×6) — standardized to the official EU AI Act German term for deployer

**Native review still recommended?** Yes — confirm "Betreiber" vs "Anwender" nuance in specific contexts, and verify "menschliche Aufsicht" vs "menschliche Überwachung" consistency.

---

### Dutch (nl)

**Terms checked:**
- ✅ Title: "Conformiteitsbeoordeling onder de EU AI-verordening"
- ✅ SME: "kmo" (7×) / "KMO" (1×) — natural Dutch usage
- ✅ Provider: "aanbieder" (26×)
- ✅ Deployer: "gebruiker" (12×, after normalization)
- ✅ Conformity assessment: "conformiteitsbeoordeling" (10×)
- ✅ High-risk AI system: "AI met een hoog risico" (1×)
- ✅ Human oversight: "menselijk toezicht" (5×)
- ✅ CE marking: "CE-markering" (4×)
- ✅ Declaration of Conformity: "conformiteitsverklaring" (5×)
- ✅ EU AI Act: "EU AI-verordening" (7×)

**Title assessment:** Natural. "onder de EU AI-verordening" is correct Dutch legal phrasing.

**Body-flow assessment:** Fluent. "compliance officer" is retained as a loanword, which is common in Dutch business Dutch.

**Required edits applied:**
- "implementatiebedrijven" → "gebruikers" — "implementatie" means "implementation", not "deployer"
- "voor conformiteit voor implementatie" → "voor conformiteit voor gebruikers" — heading terminology consistency
- "het implementatietraject" → "het traject voor gebruikers" — terminology consistency

**Native review still recommended?** Yes — confirm "gebruiker" vs "implementator" / "afnemer" in legal context, and verify "kmo" vs "KMO" capitalization.

---

### Portuguese (pt)

**Terms checked:**
- ✅ Title: "Avaliação de conformidade com o Regulamento Europeu da Inteligência Artificial"
- ✅ SME: "PME" (7×)
- ✅ Provider: "fornecedor" (27×)
- ✅ Deployer: "implementador" (17×)
- ✅ Conformity assessment: "avaliação de conformidade" (5×)
- ✅ High-risk AI system: "sistema de IA de alto risco" (4×)
- ✅ Human oversight: "supervisão humana" (5×)
- ✅ CE marking: "marcação CE" (4×)
- ✅ Declaration of Conformity: "Declaração de Conformidade" (5×)
- ✅ EU AI Act: "Regulamento Europeu da Inteligência Artificial" / "Regulamento IA"

**Title assessment:** Natural. "Regulamento Europeu" is the correct Portuguese legal term for EU Regulations.

**Body-flow assessment:** Fluent. Uses European Portuguese forms ("orienta", "equipas").

**Required edits applied:**
- Heading case normalized to sentence case:
  - "As Obrigações do Fornecedor: Artigo 17.º e o Conjunto Completo de Requisitos de Conformidade" → "As obrigações do fornecedor: artigo 17.º e o conjunto completo de requisitos de conformidade"
  - "O Procedimento de Conformidade do Implementador em Quatro Passos" → "O procedimento de conformidade do implementador em quatro passos"
  - "Documentação Técnica: O Conjunto Mínimo" → "Documentação técnica: o conjunto mínimo"

**Native review still recommended?** Yes — confirm European vs Brazilian Portuguese choices, and verify "implementador" vs "utilizador" / "operador" in legal context.

---

## 4. Exact edit list

| # | File | Current phrase | Replacement phrase | Reason |
|---|---|---|---|---|
| 1 | `eu-ai-act...es.review.md` | "Esta guía guía a los responsables" | "Esta guía orienta a los responsables" | Repetition/typo |
| 2 | `eu-ai-act...fr.review.md` | "à la Règlement" | "au Règlement" | Grammar: masculine noun requires "au", not "à la" |
| 3 | `eu-ai-act...fr.review.md` | "exploitant" | "déployeur" | EU AI Act official French term for deployer |
| 4 | `eu-ai-act...fr.review.md" | "exploitants" | "déployeurs" | Plural consistency |
| 5 | `eu-ai-act...de.review.md` | "Anwender" | "Betreiber" | EU AI Act official German term for deployer |
| 6 | `eu-ai-act...de.review.md` | "Anwenders" | "Betreibers" | Genitive consistency |
| 7 | `eu-ai-act...nl.review.md` | "implementatiebedrijven" | "gebruikers" | "implementatie" means implementation, not deployer |
| 8 | `eu-ai-act...nl.review.md` | "voor conformiteit voor implementatie" | "voor conformiteit voor gebruikers" | Heading terminology consistency |
| 9 | `eu-ai-act...nl.review.md` | "het implementatietraject" | "het traject voor gebruikers" | Terminology consistency |
| 10 | `eu-ai-act...pt.review.md` | "As Obrigações do Fornecedor: Artigo 17.º e o Conjunto Completo de Requisitos de Conformidade" | "As obrigações do fornecedor: artigo 17.º e o conjunto completo de requisitos de conformidade" | Sentence-case consistency |
| 11 | `eu-ai-act...pt.review.md` | "O Procedimento de Conformidade do Implementador em Quatro Passos" | "O procedimento de conformidade do implementador em quatro passos" | Sentence-case consistency |
| 12 | `eu-ai-act...pt.review.md` | "Documentação Técnica: O Conjunto Mínimo" | "Documentação técnica: o conjunto mínimo" | Sentence-case consistency |

---

## 5. Approval readiness

### Can be approved now

None. All five languages received automated QA edits. While the edits are high-confidence, the user requested native review before approval.

### Need edits (applied ✅)

- **ES** — Repetition fix applied.
- **FR** — Grammar and terminology fixes applied.
- **DE** — Terminology standardization applied.
- **NL** — Terminology correction applied.
- **PT** — Heading case normalization applied.

### Need native review before approval

- **ES** — Recommended for legal register and "RR. HH." confirmation.
- **FR** — Recommended for "déployeur" vs "exploitant" nuance and legal register.
- **DE** — Recommended for "Betreiber" context confirmation and compound noun precision.
- **NL** — Recommended for "gebruiker" vs "afnemer" legal nuance.
- **PT** — Recommended for European Portuguese legal register confirmation.

---

## 6. Safety confirmation

- **metadata.json** — not touched.
- **article.md** — not touched.
- **translations.json** — no sidecars created.
- **article.<lang>.md** — no translated article files created.
- **templates/** — no changes.
- **tools/rebuild_local.py** — no changes.
- **Generated artifacts** — not regenerated or committed.
- **--apply-approved** — not run.
- **All review files** — remain `Status: draft`.
- **Reviewer / Reviewed at** — blank.

---

## 7. Recommendation for Gate 3

**Gate 3 readiness: conditional.**

The translations are now QA-clean and ready for human/native review. Two paths forward:

**Path A — Native review first (recommended):**
1. Assign a native speaker or domain expert per language.
2. Reviewer opens each `.review.md` file, reads the translation, ticks the terminology checkboxes, and adds notes in the "Reviewer notes" section.
3. If satisfied, reviewer changes `Status: draft` → `Status: approved` and fills in `Reviewer:` and `Reviewed at:`.
4. Run `--apply-approved` to create `article.<lang>.md` and `translations.json`.
5. Proceed to template/build integration (hreflang, canonical, `inLanguage`).

**Path B — Approve as-is (higher risk):**
1. Accept the automated QA as sufficient.
2. Mark all five review files as `Status: approved`.
3. Run `--apply-approved`.
4. Proceed to template/build integration.

**Recommendation:** Take Path A. The pilot is a controlled experiment; the extra day of native review is worth the confidence gain before the first published multilingual pages go live.
