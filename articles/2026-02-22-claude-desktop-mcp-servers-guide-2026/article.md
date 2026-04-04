---
title: "10 MCP Servers to 10x Your Claude Desktop Workflow"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/claude-desktop-mcp-servers-guide-2026"
published_date: "2026-02-22"
license: "CC BY 4.0"
---
# 10 MCP Servers to 10x Your Claude Desktop Workflow

## A Practical Guide to Installing and Configuring Essential Local AI Tools

Using Claude Desktop without the right **Claude Desktop MCP servers** leaves 90% of its potential on the table. The Model Context Protocol (MCP) transforms Claude from a simple chatbot into a productivity powerhouse for effective **Business Process Optimization**, giving it local access to your filesystem, GitHub repos, databases, and more.

This guide walks you through setting up Claude Desktop with 10 essential MCP servers that will 10x your workflow.

## Quick Setup: How MCP Servers Work

MCP servers run locally on your machine and expose tools, resources, and prompts to Claude Desktop through a standardized protocol. Think of them as plugins that give Claude new capabilities — except they're privacy-first (everything runs locally) and work across any MCP-compatible client.

Installation is simple: Add a server config to your `claude_desktop_config.json` file, restart Claude, and you're done.

Where to find your config file:
-   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
-   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

## The 10 Must-Have Claude Desktop MCP Servers

### 1. Filesystem Server — Read & Write Files Locally

**What it does:** Lets Claude read, write, search, and edit files on your computer. Essential for coding, writing, or working with local documents.

**Install:**
```
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    }
  }
}
```
Replace `/path/to/allowed/directory` with the folder you want Claude to access (e.g., `~/projects`).

### 2. GitHub Server — Manage Repos, Issues, and PRs

**What it does:** Search repos, create issues, comment on PRs, fetch file contents, and more — all without leaving Claude.

**Install:**
```
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```
Get a GitHub PAT [read](https://github.com/settings/tokens).

### 3. Brave Search Server — Real-Time Web Search

**What it does:** Lets Claude search the web in real time. Crucial for research, fact-checking, and staying current.

**Install:**
```
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```
Get a free Brave API key [read](https://brave.com/search/api).

### 4. PostgreSQL Server — Query Databases Directly

**What it does:** Run SQL queries, inspect schemas, and analyze data in your PostgreSQL databases.

**Install:**
```
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/dbname"]
    }
  }
}
```
Replace the connection string with your actual database credentials.

### 5. Memory Server — Persistent Knowledge Graph

**What it does:** Creates a local knowledge graph so Claude remembers context across conversations. Game-changer for long-term projects.

**Install:**
```
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### 6. Puppeteer Server — Browser Automation

**What it does:** Control a headless Chrome browser — scrape websites, fill forms, take screenshots, run end-to-end tests.

**Install:**
```
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### 7. Slack Server — Send Messages & Read Channels

**What it does:** Post to Slack channels, read message history, search conversations — great for team automation.

**Install:**
```
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token"
      }
    }
  }
}
```
Create a Slack app and bot token [read](https://api.slack.com/apps).

### 8. Google Maps Server — Geocoding & Directions

**What it does:** Geocode addresses, calculate routes, find nearby places — useful for logistics, travel planning, or location-aware apps.

**Install:**
```
{
  "mcpServers": {
    "google-maps": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-google-maps"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```
Get a Google Maps API key [read](https://console.cloud.google.com).

### 9. Sequential Thinking Server — Extended Reasoning

**What it does:** Gives Claude access to a sequential thinking tool for complex multi-step reasoning. Particularly useful for debugging or strategic planning.

**Install:**
```
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### 10. Time Server — Current Date & Time

**What it does:** Provides Claude with the current date and time. Simple but essential — Claude otherwise has no concept of "today."

**Install:**
```
{
  "mcpServers": {
    "time": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-time"]
    }
  }
}
```

## Putting It All Together

Your final `claude_desktop_config.json` should look like this:

```
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/projects"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_api_key_here"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/dbname"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token"
      }
    },
    "google-maps": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-google-maps"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_api_key_here"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "time": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-time"]
    }
  }
}
```
**Important:** Replace all placeholder tokens and credentials with your actual API keys. Restart Claude Desktop after saving the config.

## Troubleshooting Common Issues

**Claude doesn't see the new servers**
-   Restart Claude Desktop completely (quit and reopen)
-   Check the config file for JSON syntax errors (use a JSON validator)
-   Make sure the file path is correct for your OS

**Server fails to start**
-   Run the `npx` command manually in your terminal to see the error
-   Check that all required environment variables are set
-   Ensure Node.js 18+ is installed (`node --version`)

**Permission errors**
-   For filesystem server: make sure the path exists and is readable
-   For database servers: verify connection strings are correct
-   For API-based servers: confirm API keys are valid

## What's Next?

This is just the beginning. The MCP ecosystem has 100+ servers and growing — from specialized tools like Obsidian integration and Linear project management to custom servers you can build yourself. This level of customization is a key component of a modern **Digital Transformation Strategy**, allowing teams to tailor AI to their specific needs.

Browse the full catalog [read](https://getmcpapps.com) to discover more servers, read reviews, and see what the community is building.

Claude Desktop + MCP isn't just a better chatbot. It's your AI-powered operating system.

## Further Reading

- [Claude Browser Agent SEO Workflows 2026](https://radar.firstaimovers.com/claude-browser-agent-seo-workflows-2026)
- [AI Workflow Automation Maturity Ladder for SMEs](https://radar.firstaimovers.com/ai-workflow-automation-maturity-ladder-smes)
- [Harpa AI vs Competition: Best Browser Extensions for Business](https://www.linkedin.com/pulse/harpa-ai-vs-competition-best-browser-extensions-business-costa-q1swe)

---

_Written by [Dr Hernani Costa](https://drhernanicosta.com), Founder and CEO of [First AI Movers](https://www.firstaimovers.com). Providing AI Strategy & Execution for Tech Leaders since 2016._

Subscribe to [First AI Movers](https://firstaimovers.com) for practical and measurable business strategies for Business Leaders. [First AI Movers](https://www.linkedin.com/company/first-ai-movers/) is part of [Core Ventures](https://coreventures.xyz).

**Ready to increase your business revenue?**
Book a [call](https://calendar.app.google/RJnKGg3b8ZRfhect5) today!

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://radar.firstaimovers.com/claude-desktop-mcp-servers-guide-2026) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*