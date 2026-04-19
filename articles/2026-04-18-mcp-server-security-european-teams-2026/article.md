---
title: "MCP Server Security: 5 Risks and an Audit Checklist for European Teams"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/mcp-server-security-european-teams-2026"
published_date: "2026-04-18"
license: "CC BY 4.0"
---
> **TL;DR:** Five MCP security risks European teams must audit before deploying AI tools. Includes a checklist and EU AI Act risk classification guide.

The Model Context Protocol (MCP) is one of the most consequential infrastructure decisions a technical team can make when deploying AI tools in 2026. MCP servers extend what AI assistants like Claude can do: they can browse the web, read files, query databases, execute code, and call third-party APIs on behalf of the user. This makes them genuinely useful and also genuinely dangerous if deployed without a security review. Why this matters: a single unsecured MCP server can expose credentials, file systems, and client data, creating both operational and regulatory liability that most engineering teams have not yet accounted for.

A tool description in an MCP server can instruct an AI model to perform actions the user did not request. A compromised or malicious MCP server can exfiltrate credentials, access file systems, or make API calls on behalf of authenticated users. For a 25-person engineering team in Warsaw or a professional services firm in Brussels relying on AI tools for sensitive client work, this is not a theoretical risk. It is an operational security gap that needs a structured response.

This guide covers five concrete MCP security risks and a checklist your team can act on before deployment.

## Risk 1: Tool Description Injection

The most serious and least understood MCP risk is tool description injection. When an MCP server registers its tools with an AI model, it provides a natural language description of what each tool does. The AI model reads these descriptions to decide when and how to call the tool. If a malicious MCP server (or a compromised one) provides a description that contains instructions to the model rather than a description of the tool's purpose, the model may follow those instructions.

A real-world example from research published in early 2026: an MCP server registered a "file search" tool with a description that included hidden instructions telling the model to read SSH key files and append them to the output of an unrelated command. Users who connected to this server and used the file search tool had their SSH keys silently exfiltrated to a remote endpoint.

The defence against tool description injection starts with provenance: only connect to MCP servers whose source code you have reviewed or whose publisher you trust completely. For enterprise teams, this means maintaining an approved MCP server list and prohibiting employees from connecting to arbitrary community-published servers.

**Checklist item 1:** Review the complete tool description text in every MCP server before connecting. This text should describe what the tool does, not how the model should behave. Any description that includes phrases like "you should", "always", "never tell the user", or instruction-format language is a red flag.

## Risk 2: Credential and Session Token Access

MCP servers that have access to the file system can potentially read credential stores, session tokens, and configuration files that contain secrets. If the MCP server is granted broad file system permissions, a compromised server can read `~/.ssh/`, `~/.aws/credentials`, `.env` files, or any local credential cache.

This risk is compounded when AI coding assistants are granted wide file access to be maximally helpful. A developer who connects Claude Code or a similar tool to an MCP server that provides filesystem browsing may be inadvertently giving that server a path to credential files stored in their home directory.

**Checklist item 2:** Scope MCP server file system access to the minimum required directory. For a coding assistant, this is typically the project root. Review the MCP server's declared permissions in its configuration file before connecting, and reject any server that requests home directory access unless there is a specific, understood reason for it. On macOS, use sandbox profiles or permission boundaries to enforce directory scope at the OS level.

## Risk 3: Unsanitised API Passthrough

MCP servers that proxy requests to third-party APIs may not sanitise the data they forward. If the model constructs a query containing user-provided data (such as a customer name or email address) and the MCP server forwards that data to an external API without validation, you have created a data pipeline that bypasses your normal data handling controls.

For European teams, this carries a specific GDPR implication. If personal data flows through an MCP server to a third-party API based outside the EU, that transfer requires appropriate safeguards under GDPR Chapter V. An MCP server that makes undocumented API calls to US-based services with personal data embedded in queries is a data breach waiting to happen.

**Checklist item 3:** For each MCP server connected to production systems or handling real data, document every external API endpoint the server can call. Verify that no personal data (names, emails, company names, IP addresses) can be embedded in API calls to services outside your approved data processing list. Where this cannot be guaranteed by code review, deploy the MCP server in a sandboxed environment with network egress restrictions.

## Risk 4: Overprivileged Execution Context

Some MCP servers execute code or shell commands on behalf of the AI model. If that execution happens with the privileges of the current user, a compromised server can do anything the user's account is authorised to do: delete files, modify configurations, make outbound network connections, or read data from connected services.

The principle of least privilege applies here as it does anywhere in security. An MCP server that executes shell commands should run as a restricted user with no access to production credentials, no outbound network access except to explicitly approved endpoints, and no write access to directories outside the task scope.

**Checklist item 4:** Run MCP servers that execute code or commands as a dedicated low-privilege service account. Use Docker containers or systemd sandboxing to restrict what the process can access at the OS level. Log all command executions to an append-only audit trail that the MCP server process itself cannot modify.

## Risk 5: Missing Update and Provenance Verification

MCP servers sourced from community repositories, npm packages, or GitHub can change after you have reviewed them. A server you audited last month may have received an update that introduced new tool descriptions, new external API calls, or new permission requests. Most teams do not re-audit their MCP dependencies after initial setup.

Additionally, for teams using package managers to install MCP servers, supply chain attacks are a live threat. A compromised package maintainer can publish a malicious update that passes basic functional testing while introducing a security exploit.

**Checklist item 5:** Pin MCP server dependencies to specific versions in your configuration, and review the diff before approving any version upgrade. For high-trust MCP servers (those with database or credential access), treat version upgrades with the same review process as a code change in your primary application. Subscribe to security advisories from MCP server publishers where available.

## EU AI Act Classification for MCP-Enabled Systems

Under Regulation (EU) 2024/1689, the EU AI Act, the AI component of a system is assessed for risk based on the system's purpose and the decisions it makes, not just the model itself. An AI system that includes MCP servers providing access to personnel records, financial data, or medical information may qualify as a high-risk system under Annex III depending on the deployment context.

High-risk classification triggers requirements including: conformity assessment, technical documentation, logging of system operation, human oversight mechanisms, and registration with the EU AI Act database. Teams deploying MCP-enabled AI systems in HR, financial services, or healthcare contexts should conduct a formal risk classification check before deployment.

For most internal operational deployments (coding assistance, document drafting, customer communication support), MCP-enabled systems will not reach high-risk classification. But the assessment is not optional. Documenting the classification decision and its rationale is a compliance requirement under Article 9 of the regulation for in-scope operators.

## Pre-Deployment Security Checklist

Before connecting an MCP server to a production AI deployment:

- [ ] Source code reviewed or publisher explicitly trusted
- [ ] All tool description text audited for injection-format language
- [ ] File system permissions scoped to minimum required directory
- [ ] External API endpoints documented and GDPR transfer basis confirmed
- [ ] MCP server runs as least-privilege account or in sandboxed container
- [ ] Command execution logged to tamper-evident audit trail
- [ ] Version pinned and upgrade review process defined
- [ ] EU AI Act risk classification documented for the overall system
- [ ] Personal data handling reviewed for GDPR Article 28 controller-processor requirements if using a third-party MCP server

A team that completes this checklist before connecting an MCP server to any AI tool used in a business context has addressed the primary attack surface. This does not require dedicated security staff. It requires a structured two-hour review session before deployment.

Ready to review your team's AI tool security posture in more detail? [Start with the First AI Movers AI Readiness Assessment.](https://radar.firstaimovers.com/page/ai-readiness-assessment)

## Frequently Asked Questions

### Are MCP servers safe if I only use official Anthropic-provided ones?

Anthropic publishes reference MCP server implementations for common integrations. These are more trustworthy than arbitrary community packages, but they still require the same deployment discipline: scope file system access, run as least-privilege accounts, and audit before each version update. Security posture is a property of how you deploy, not just of which server you use.

### What is the difference between MCP security and Claude Code's built-in permissions?

Claude Code has its own permission system for controlling what files and bash commands it can access, configured in `settings.json`. This is separate from MCP server permissions. An MCP server connected to Claude Code can potentially bypass the Claude Code permission layer if it is granted access at the OS level. The two permission systems must be configured consistently. Do not grant an MCP server more file system access than you would grant Claude Code directly.

### How does a small team without a security professional conduct this audit?

The checklist above is designed to be completed by a developer or technical lead without security specialisation. The most important steps are: read the MCP server source code before deployment (or use only publishers whose code you can read), restrict file system permissions in the MCP configuration file, and document what external APIs the server calls. Eighty percent of the risk reduction comes from these three actions.

## Further Reading

- [Claude Code Security and Data Privacy for European Teams](https://radar.firstaimovers.com/claude-code-security-data-privacy-european-teams-2026)
- [AI Vendor Evaluation Scorecard: 8 Criteria for European SMEs](https://radar.firstaimovers.com/ai-vendor-evaluation-scorecard-european-smes-2026)
- [Shadow AI Detection and Governance for European SMEs](https://radar.firstaimovers.com/shadow-ai-detection-governance-european-smes-2026)

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "MCP Server Security: 5 Risks and an Audit Checklist for European Teams",
  "description": "Five MCP security risks European teams must audit before deploying AI tools. Includes a checklist and EU AI Act risk classification guide.",
  "datePublished": "2026-04-18T04:17:45.542757+00:00",
  "dateModified": "2026-04-18T04:17:45.542757+00:00",
  "author": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://radar.firstaimovers.com/favicon.ico"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://radar.firstaimovers.com/mcp-server-security-european-teams-2026"
  },
  "image": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1200&h=630&fit=crop&q=80"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Are MCP servers safe if I only use official Anthropic-provided ones?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Anthropic publishes reference MCP server implementations for common integrations. These are more trustworthy than arbitrary community packages, but they still require the same deployment discipline: scope file system access, run as least-privilege accounts, and audit before each version update. S..."
      }
    },
    {
      "@type": "Question",
      "name": "What is the difference between MCP security and Claude Code's built-in permissions?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Claude Code has its own permission system for controlling what files and bash commands it can access, configured in `settings.json`. This is separate from MCP server permissions. An MCP server connected to Claude Code can potentially bypass the Claude Code permission layer if it is granted access..."
      }
    },
    {
      "@type": "Question",
      "name": "How does a small team without a security professional conduct this audit?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The checklist above is designed to be completed by a developer or technical lead without security specialisation. The most important steps are: read the MCP server source code before deployment (or use only publishers whose code you can read), restrict file system permissions in the MCP configura..."
      }
    }
  ]
}
</script>
-->

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/mcp-server-security-european-teams-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*