# Multi-Property Archive Pattern

## Executive answer

**Do not merge other brand or property archives into this First AI Movers article archive. Do not mix unrelated properties in one archive.**

Each property gets its own repository, domain, and archive. Reuse the tooling pattern; do not share a single archive across unrelated brands.

## Why separate archives matter

| Concern | Risk of merging | Benefit of separation |
|---|---|---|
| **Topical authority** | Search engines and AI citation systems see diluted focus | Each archive owns a clear topic cluster |
| **Reader trust** | Visitors expect one voice per archive | Brand-aligned editorial identity |
| **Canonical clarity** | Mixed canonical domains confuse crawlers | One canonical policy per property |
| **LLM ingestion clarity** | `llms-full.txt` and embeddings mix unrelated corpora | Clean, property-specific training datasets |
| **License / citation cleanliness** | CC BY 4.0 attribution gets muddled across authors | Clear attribution per property and author |
| **Analytics clarity** | GoatCounter / GSC data blends unrelated traffic | Actionable, property-specific metrics |
| **Search Console / Bing isolation** | One property's penalties affect another | Independent verification and indexing |
| **Operational rollback** | One property's issue requires archive-wide deploy | Per-property deploy and rollback |

## When to create a separate archive

Create a new archive when content differs in any of these dimensions:

- **Different brand** — Vos & Nos, Desapega, Core Ventures, etc.
- **Different audience** — dental professionals vs. AI executives vs. marketplace sellers
- **Different canonical domain** — `articles.vosenos.nl` vs. `articles.firstaimovers.com`
- **Different license or author/publisher** — CC BY vs. proprietary; different ORCID
- **Different SEO topic cluster** — dental AI vs. SME AI strategy vs. circular economy

## When content belongs in this archive

Content belongs in the First AI Movers archive when it is:

- Authored by Dr. Hernani Costa / First AI Movers
- Aligned with this archive's scope: AI strategy, EU AI Act, AI governance, agentic systems, responsible AI adoption for European businesses
- Published under the First AI Movers editorial brand

## Reference architecture

```
┌─────────────────────────────────────────┐
│     Shared tooling pattern (Apache-2.0)  │
│  (fork from First-AI-Movers/articles)   │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │ FAIM   │  │ Vos &  │  │ Desa-  │
   │ Archive│  │ Nos    │  │ pepa   │
   │        │  │ Archive│  │ Archive│
   │ .com   │  │ .nl    │  │ .nl    │
   └────────┘  └────────┘  └────────┘
   Separate    Separate    Separate
   repo        repo        repo
   Domain      Domain      Domain
   Sitemap     Sitemap     Sitemap
   Analytics   Analytics   Analytics
   llms files  llms files  llms files
```

Each property is a fork of the archive pattern with its own:

- GitHub repository
- Custom domain (or subdomain)
- `CNAME` and DNS
- Google Search Console / Bing Webmaster property
- `robots.txt` and AI-training policy
- GoatCounter site (or equivalent analytics)
- `llms.txt`, `llms-full.txt`, `CITATION.cff`
- Issue templates and governance docs

## Fork-and-customize checklist

1. **Repository**
   - [ ] Create new repo from `cookiecutter-archive-template/`
   - [ ] Update `README.md` with property name and description
   - [ ] Update `ABOUT.md` with author bio
   - [ ] Update `CITATION.cff` with author, publisher, and DOI placeholder

2. **Domain**
   - [ ] Register or configure subdomain (e.g. `articles.example.com`)
   - [ ] Add `CNAME` file
   - [ ] Configure DNS A/AAAA or CNAME records
   - [ ] Enable HTTPS (Cloudflare or GitHub Pages)

3. **Brand**
   - [ ] Replace `{{cookiecutter.project_name}}` in templates and docs
   - [ ] Update `site_url` in build config
   - [ ] Update footer, nav, and social links
   - [ ] Add brand favicon and manifest if desired

4. **Author / publisher metadata**
   - [ ] Update `author` and `publisher` in `metadata.json` defaults
   - [ ] Update JSON-LD Person/Organization in templates
   - [ ] Update ORCID and social profiles

5. **License**
   - [ ] Confirm content license (default: CC BY 4.0)
   - [ ] Confirm code license (default: Apache-2.0)
   - [ ] Update `LICENSE` and `LICENSE-CODE`

6. **Canonical URL policy**
   - [ ] Define primary publishing platform(s)
   - [ ] Update `CANONICAL_ALLOWED_HOSTS` in rebuild config
   - [ ] Configure `rel=canonical` strategy

7. **Search Console / Bing**
   - [ ] Add property in Google Search Console
   - [ ] Add property in Bing Webmaster Tools
   - [ ] Submit sitemap
   - [ ] Configure IndexNow key

8. **Analytics**
   - [ ] Create GoatCounter site (or equivalent)
   - [ ] Update analytics script in `templates/base.html.j2`
   - [ ] Configure `window.goatcounter.path` override

9. **Robots / AI training policy**
   - [ ] Customize `robots.txt`
   - [ ] Set AI-training meta tag policy
   - [ ] Document training-data clarity stance

10. **LLM files**
    - [ ] Update `llms.txt` discovery summary
    - [ ] Confirm `llms-full.txt` header license block

11. **Issue templates / governance**
    - [ ] Customize `.github/ISSUE_TEMPLATE/`
    - [ ] Update `CODEOWNERS`
    - [ ] Update `CONTRIBUTING.md` scope rules
    - [ ] Update `SECURITY.md`

12. **Deployment**
    - [ ] Configure GitHub Pages (or Cloudflare Pages)
    - [ ] Set up `build-and-deploy.yml`
    - [ ] Add required secrets (IndexNow, analytics, etc.)

## Examples

| Property | Scope | Decision |
|---|---|---|
| **First AI Movers** | AI strategy, EU AI Act, SME governance | **Stays here** — this is the canonical archive |
| **Vos & Nos** | Dental AI, oral health technology | **Separate archive** — different audience, brand, domain |
| **Desapega.nl** | Circular economy, marketplace sustainability | **Separate archive** — different industry, brand, domain |
| **Core Ventures** | Corporate AI investment, venture strategy | **Separate archive** — different content scope and voice |
| **Radar / Hashnode republications** | Same articles, different platform | **Not a new archive** — canonical stays here; republications point back |

## Starter template

A minimal cookiecutter-style starter is provided in `cookiecutter-archive-template/` at the repository root. It includes:

- Placeholder config (`cookiecutter.json`)
- One sample article with metadata
- Basic Jinja2 templates
- Minimal static assets
- Build tooling stubs
- License split (CC BY 4.0 content / Apache-2.0 code)
- README with customization instructions

The template is intentionally smaller than the mature First AI Movers archive. It omits advanced features (MCP server, chatbot, embeddings, PWA, comments, analytics, DOI, errata, series, quality CI) so new archives start simple and add complexity only when needed.

## How to generate a new archive

```bash
# Install cookiecutter if not already available
pip install cookiecutter

# Generate from the template
cookiecutter cookiecutter-archive-template/

# Follow the interactive prompts, then:
cd <your-new-archive-repo>
python3 tools/rebuild_local.py
npm run test:e2e
```

If you prefer not to install cookiecutter, you can copy the template directory manually and replace placeholders by hand.

## License note

The archive tooling is licensed under **Apache-2.0** (see `LICENSE-CODE`). Content in each archive is licensed under its own content license (default **CC BY 4.0**). Forking the template does not transfer First AI Movers branding or content rights.

## Rollback

If a property archive was incorrectly created or merged:

1. Separate the repositories (do not force-merge unrelated histories).
2. Redirect canonical URLs with 301 redirects if needed.
3. Update sitemaps and Search Console properties.
4. Keep the original archive intact — never delete published articles.
