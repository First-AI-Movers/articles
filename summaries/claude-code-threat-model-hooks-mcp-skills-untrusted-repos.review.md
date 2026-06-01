# Summary Review — The Claude Code Threat Model: Hooks, MCP, Skills, and Untrusted Repos

Article folder: 2026-04-08-claude-code-threat-model-hooks-mcp-skills-untrusted-rep
Canonical URL: https://radar.firstaimovers.com/claude-code-threat-model-hooks-mcp-skills-untrusted-repos
Generated at: 2026-06-01
Model: minimax (MiniMax-M2)

## 50-word summary

Claude Code requires a threat model that goes beyond code generation mistakes. The key surfaces are untrusted repositories (which can inject prompts), hooks (which customize workflow behavior), MCP servers (which expand tool access), and skills/plugins (which shape agent behavior). Teams must move from assistant thinking to infrastructure thinking, treating these as one connected operating surface.

## 200-word summary

The security model for Claude Code needs to evolve from treating it as a chat interface to recognizing it as an agentic coding tool that executes code, accesses files, and integrates with external services. A proper threat model must cover five interconnected surfaces. First, untrusted repositories represent the most critical risk because repository content can influence agent behavior through prompt injection, as demonstrated by Check Point Research in February 2026 showing how malicious project configurations could abuse hooks and MCP integrations to trigger shell execution and exfiltrate API credentials. Second, hooks allow teams to customize behavior at workflow moments but also create risk if scope and data destinations are not controlled. Third, MCP servers connect Claude Code to hundreds of external tools but expand the attack surface significantly. Fourth, skills and plugins extend the agent with specialized knowledge and workflows, creating behavior-shaping layers that can bundle hooks, subagents, and MCP servers together. Fifth, permissions and policy controls determine whether critical security settings are managed centrally or left to ad hoc local configuration. The practical takeaway is that technical leaders should treat hooks, MCP, skills, plugins, and repository trust as one connected operating surface and use Anthropic's documented controls like allowManagedHooksOnly and allowedMcpServers to enforce governance.

## 500-word summary

Claude Code, Anthropic's agentic coding tool, requires a fundamentally different security approach than treating it as a chat interface. The tool reads codebases, edits files, runs commands, and integrates with development tools across terminal, IDE, desktop app, and browser. Once a tool can do all of that, the security question shifts from is the model accurate? to what can influence the model, what can it reach, and what can it do if it gets steered the wrong way? Anthropic's secure deployment guide recommends the same principles used for semi-trusted code: isolation, least privilege, and defense in depth. The trust boundary extends beyond the model provider to include the repository opened, hooks allowed to run, MCP servers connected, skills and plugins installed, and permissions and settings sources trusted. A comprehensive threat model for Claude Code must address five interconnected surfaces. First, untrusted repositories remain the most critical risk. Check Point Research documented in February 2026 that malicious project configurations in Claude Code could abuse hooks, MCP integrations, and environment variables to trigger shell execution and exfiltrate API credentials when users cloned and opened untrusted repositories. Anthropic remediated the disclosed issues before publication, but the strategic lesson persists: repository configuration now sits much closer to execution than many teams assume. Anthropic's secure deployment guide explicitly warns that repository content can influence agent behavior, using a README example to demonstrate how prompt injection can shape actions in unexpected ways. Second, hooks represent a significant risk surface because they let teams customize behavior at specific workflow moments. Anthropic documents user, project, plugin, and managed hook behavior, with settings like allowManagedHooksOnly to block user, project, and plugin hooks while allowing only managed hooks, and allowedHttpHookUrls to allowlist HTTP hook destinations. Third, MCP servers dramatically expand functionality but also the attack surface. Claude Code can connect to hundreds of external tools through MCP, including issue trackers, GitHub, databases, Slack, Gmail, and webhook channels. However, Anthropic explicitly states that third-party MCP servers should be used at your own risk, especially servers that fetch untrusted content, which can expose users to prompt injection. Settings like allowedMcpServers and allowManagedMcpServersOnly let organizations shift MCP access into managed policy. Fourth, skills and plugins represent behavior-shaping layers. Skills, available in beta, extend Claude with specialized knowledge and workflows that affect agent behavior across tasks. Plugins can bundle skills, hooks, subagents, and MCP servers into a single installable unit, making them a supply-chain surface that should be reviewed like infrastructure, not harmless add-ons. Fifth, permissions and policy controls determine whether security settings are centrally managed or left to local improvisation. Claude Code supports allow, ask, and deny rules through /permissions, with settings like allowManagedPermissionRulesOnly to enforce managed rules exclusively. Anthropic's settings model distinguishes managed settings from user, project, local, and plugin scopes, and the secure deployment guide explicitly recommends network controls and proxy patterns for hardened environments. For technical leaders, the practical shift is from assistant thinking to infrastructure thinking.

## Review status

Status: approved
Reviewer:
Reviewed at:

## Notes

- Gate status: PASS
- Retries used: 0
- Corrective JSON retries used: 0
- Termination: PASS
- Estimated cost (USD): 0.007642
- Word counts: short=55, medium=205, long=487

## Verification

Verification status: AUTO_APPROVE
Deterministic gate: PASS
Primary verifier: openai/gpt-5.4-mini — AUTO_APPROVE
Secondary verifier: anthropic/claude-haiku-4-5-20251001 — AUTO_APPROVE
Fallback verifier: not-used
Single verifier: false
Estimated verifier cost (USD): 0.007365
Verified at: 2026-06-01

### Verification notes

- Merge rationale: both verifiers AUTO_APPROVE
- openai/gpt-5.4-mini: Covers the source's main thesis and all major threat surfaces.
- openai/gpt-5.4-mini: No invented sections, vendors, or unsupported claims.
- openai/gpt-5.4-mini: Some source-specific controls are named, but they are consistent with the article.
- anthropic/claude-haiku-4-5-20251001: All three summaries accurately reflect source claims with proper attribution to Anthropic docs and Check Point Research findings.
- anthropic/claude-haiku-4-5-20251001: Durable facts preserved: CVE-2025-59536, February 2026 Check Point research, specific Anthropic settings (allowManagedHooksOnly, allowedMcpServers, etc.), and regulatory/technical guidance remain stable.
- anthropic/claude-haiku-4-5-20251001: No volatile pricing, version numbers, or time-sensitive metrics embedded; threat model principles are architecture-level and enduring.
