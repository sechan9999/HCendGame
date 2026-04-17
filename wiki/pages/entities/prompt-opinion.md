# Prompt Opinion Platform

**Tags**: prompt-opinion, mcp, marketplace, fhir, hackathon

## What It Is

Prompt Opinion is an MCP-based AI agent marketplace. The "Agents Assemble" hackathon challenge asked builders to create MCP servers compatible with their platform, specifically supporting the SHARP Extension Specs for FHIR healthcare data.

## Key URLs

- Marketplace: https://app.promptopinion.ai/marketplace
- MCP server workspace: https://app.promptopinion.ai/workspaces/{id}/mcp-servers
- Reference MCP server: https://ts.fhir-mcp.promptopinion.ai/mcp

## Integration Requirements

1. HTTP+SSE transport (not stdio)
2. `StreamableHTTPServerTransport` from MCP SDK
3. SHARP Extension declared in `result.capabilities.extensions` (not `serverInfo`)
4. 6 FHIR R4 scopes declared
5. Handle `X-FHIR-Server-URL`, `X-FHIR-Access-Token`, `X-Patient-ID` headers

## Platform Feedback (filed during hackathon)

- Error messages should show exact JSON path mismatch, not just pass/fail
- `McpServer` SDK incompatibility should be explicitly documented
- Pre-registration validator ("test server" button) would save hours of debugging
- `ExplanationOfBenefit` scope missing from starter template — essential for billing/FWA use cases

## HCendGame Registration

- Endpoint: https://hcendgame-fwa.vercel.app/api/mcp
- Transport: HTTP + SSE
- Protocol: MCP 2024-11-05
- Status: Registered and passing SHARP extension check

**Related**: [[mcp-sharp-extension]], [[mcpserver-vs-server]], [[rxhcc-app]]
