---
trigger: always_on
description: "Enforce explicit MCP denylist and direct to mcp-policy.md before using MCP servers."
---

# MCP Denylist Guard

- Strictly forbidden to invoke `apify` or `colab-mcp`.
- Before calling any allowed MCP server (`tavily`, `firecrawl`, `api-anything`, `chrome-devtools`, `github`, `supabase_mcp`, `gemini-api-docs`), follow `.agents/rules/mcp-policy.md`.
