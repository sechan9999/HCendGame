# Decision: McpServer vs Server (low-level)

**Tags**: mcp, sdk, decision, prompt-opinion, sharp

## Problem

Prompt Opinion's `initialize` check validates that `result.capabilities.extensions["ai.promptopinion/fhir-context"]` exists. The error thrown: "Current MCP server does not support PromptOpinion's FHIR extension."

## Root Cause

`McpServer` (high-level `@modelcontextprotocol/sdk/server/mcp.js`) places custom capabilities inside `serverInfo.capabilities`, not in `result.capabilities`. This is a structural mismatch — the two locations are different fields in the MCP initialize response.

## Decision

Use the low-level `Server` class (`@modelcontextprotocol/sdk/server/index.js`) for the Vercel production endpoint (`api/mcp.js`).

```js
// WRONG — McpServer (high-level):
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
const server = new McpServer({ name, version, capabilities: { extensions: {...} } });
// → capabilities end up in serverInfo, NOT result.capabilities

// CORRECT — Server (low-level):
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
const server = new Server({ name, version }, { capabilities: { tools: {}, extensions: {...} } });
// → capabilities appear in result.capabilities ✅
```

## Trade-offs

- Low-level `Server` requires manual `setRequestHandler` for `ListToolsRequestSchema` and `CallToolRequestSchema`
- More boilerplate, but full control over the MCP response structure
- Local server (`mcp/server.js`) still uses `McpServer` — acceptable for stdio/Claude Desktop where Prompt Opinion's check doesn't run

## Verification

```bash
curl -X POST https://hcendgame-fwa.vercel.app/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
# result.capabilities.extensions["ai.promptopinion/fhir-context"] must be present
```

**Related**: [[mcp-sharp-extension]], [[prompt-opinion]], [[rxhcc-app]]
