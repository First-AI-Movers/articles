# {{cookiecutter.project_name}} — Cookiecutter Template

A minimal starter template for property-specific article archives.

## What this is

This template scaffolds a new article archive repository for a specific brand, audience, or topic cluster. It is based on the First AI Movers archive pattern but stripped to essentials so new archives start simple.

## What is intentionally omitted

The template does **not** include advanced features from the mature First AI Movers archive:

- MCP server / chatbot (E21/E33)
- Embedding index (E22)
- Zenodo DOI pipeline (E23)
- Analytics (E24)
- Wayback snapshots (E25)
- Giscus comments (E26)
- PWA offline mode (E27)
- GEO audit CI (E28)
- AI training manifest (E29)
- Article quality CI (E30)
- Series metadata (E31)
- Errata protocol (E37)

Add these only when your archive needs them.

## Quick start

```bash
# Install cookiecutter
pip install cookiecutter

# Generate your archive
cookiecutter cookiecutter-archive-template/

# Answer the prompts, then:
cd {{cookiecutter.repo_slug}}

# Install Python dependencies
pip install -r tools/requirements.txt
pip install pytest

# Build the site
python3 tools/rebuild_local.py

# Run tests
python3 -m pytest tools/tests -v
```

## License split

- **Content** (articles, topic intros): {{cookiecutter.content_license}}
- **Code / tooling / templates / static assets**: {{cookiecutter.code_license}}

## Do not mix unrelated properties

Each archive should serve one brand, one audience, and one canonical domain. See `docs/MULTI_PROPERTY_PATTERN.md` for the full rationale.
