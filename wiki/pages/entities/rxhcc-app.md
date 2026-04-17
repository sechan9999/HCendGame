# rxhcc-app — HCendGame FWA Detection

**Tags**: rxhcc-app, hcendgame, react, vercel, hackathon, deployed

## Status

Live: https://hcendgame-fwa.vercel.app  
Repo: https://github.com/sechan9999/HCendGame  
MCP: https://hcendgame-fwa.vercel.app/api/mcp  
Match Rate: 97% (PDCA Check complete 2026-04-16)

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | React 19 + Vite 7 + Tailwind CSS 3 |
| LLM | OpenAI-compatible (Ollama / Groq / rule-based fallback) |
| Rules | ICD-10/NDC/HCC engine (zero dependencies) |
| MCP | @modelcontextprotocol/sdk, HTTP+SSE, SHARP extension |
| Deploy | Vercel (React SPA + serverless MCP API route) |

## 6 UI Modules

| Tab | Function |
|-----|----------|
| Single Claim | Real-time ICD-10/NDC/HCC validation, 5 fraud scenarios |
| Batch Analysis | 500 synthetic claims, 15% anomaly rate |
| Network Graph | Kickback rings, hub providers, doctor-shopping |
| Temporal | Monthly billing spike detection, inline SVG chart |
| AI Investigator | NL query → structured evidence brief |
| AutoResearch | LOOP FOREVER, F1: 0.821→0.878, 11 experiments |

## Key Files

```
rxhcc-app/
  src/RXHCCnva.jsx        — main React app (2282 lines)
  api/mcp.js              — Vercel MCP serverless handler (low-level Server)
  mcp/server.js           — local/Claude Desktop MCP (McpServer + stdio/HTTP)
  mcp/rules/clinical.js   — ICD-10/NDC/HCC rule engine
  mcp/fhir/adapter.js     — FHIR R4 adapter
  vercel.json             — deployment config (maxDuration:30, no runtime field)
  .env.example            — LLM_PROVIDER, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
```

## Critical Decisions

- [[mcpserver-vs-server]] — use low-level Server for correct SHARP extension placement
- [[vercel-rootdirectory]] — rootDirectory=rxhcc-app prevents Python detection

**Related**: [[fwa-detection]], [[autoresearch]], [[mcp-sharp-extension]], [[prompt-opinion]]
