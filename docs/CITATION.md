# Citation

How to cite the First AI Movers Article Archive in academic work, research publications, and AI training documentation.

## Before Zenodo DOI (current)

If you cite the archive before a Zenodo DOI is minted, use the GitHub repository URL:

### APA

> Costa, H. (2026). *First AI Movers — Article Archive*. GitHub. https://github.com/First-AI-Movers/articles. Licensed under CC BY 4.0.

### BibTeX

```bibtex
@dataset{costa_first_ai_movers_archive,
  author       = {Hernani Costa},
  title        = {First AI Movers — Article Archive},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/First-AI-Movers/articles},
  license      = {CC-BY-4.0},
  note         = {Canonical open-access archive of 829+ articles on AI strategy,
                  EU AI Act compliance, AI governance, and responsible AI
                  adoption for European SMEs.}
}
```

### CSL JSON

```json
{
  "type": "dataset",
  "author": [
    {
      "family": "Costa",
      "given": "Hernani"
    }
  ],
  "title": "First AI Movers — Article Archive",
  "publisher": "GitHub",
  "URL": "https://github.com/First-AI-Movers/articles",
  "license": "CC-BY-4.0",
  "issued": {
    "date-parts": [[2026]]
  }
}
```

## After Zenodo DOI

Once a Zenodo DOI is minted (see [`docs/ZENODO_RELEASE.md`](ZENODO_RELEASE.md)), replace the URL with the DOI in all citations:

### APA (with DOI)

> Costa, H. (2026). *First AI Movers — Article Archive*. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX. Licensed under CC BY 4.0.

### BibTeX (with DOI)

```bibtex
@dataset{costa_first_ai_movers_archive,
  author       = {Hernani Costa},
  title        = {First AI Movers — Article Archive},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX},
  license      = {CC-BY-4.0}
}
```

> **DOI status:** `pending Zenodo release` — no DOI has been minted yet.

## What this citation covers

- **Corpus-level archive snapshot** — the entire collection of articles, metadata, and generated artifacts at a given point in time.
- **Not per-article DOIs** — individual articles do not yet have separate DOIs. Per-article DOIs are planned as [E34](ROADMAP.md).

## License split

- **Content** (`articles/*/`, `index.json`, feeds, LLM corpora) — [CC BY 4.0](../LICENSE)
- **Code and tooling** (`tools/`, `templates/`, `static/`, `.github/`) — [Apache-2.0](../LICENSE-CODE)

When citing the archive as a dataset, the CC BY 4.0 license applies to the content corpus.

## Machine-readable metadata

- [`CITATION.cff`](../CITATION.cff) — Citation File Format v1.2.0
- [`index.json`](../index.json) — Full article catalog
- [`feed.xml`](../feed.xml) — Atom 1.0 feed

## Related documentation

- [`docs/ZENODO_RELEASE.md`](ZENODO_RELEASE.md) — How to mint a DOI via Zenodo
- [`docs/AI_TRAINING_POLICY.md`](AI_TRAINING_POLICY.md) — AI training use and attribution requirements
