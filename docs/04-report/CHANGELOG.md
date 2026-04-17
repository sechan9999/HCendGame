# CHANGELOG — HCendGame FWA Detection System

All notable changes to the rxhcc-app project are documented here.

## [2026-04-16] — HCendGame Hackathon Completion

### Added
- React 19 + Vite SPA with 6 FWA detection modules (Single Claim, Batch, Network, Temporal, AI Investigator, AutoResearch)
- MCP server deployed as Vercel serverless function (`/api/mcp`)
- FHIR R4 adapter with Prompt Opinion SHARP extension support
- AutoResearch module with LOOP FOREVER LLM iteration (best F1: 0.878)
- OpenAI-compatible LLM support (Groq, Ollama, rules-based fallback)
- Clinical rule engine (ICD-10/NDC/HCC) — zero dependencies
- Local MCP server for Claude Desktop integration
- Network graph visualization (provider rings, kickback patterns, doctor-shopping)
- Temporal analysis with spike detection (monthly billing trends)
- Synthetic dataset (500+ claims) for testing and demo

### Changed
- Switched from high-level `McpServer` to low-level `Server` class for correct SHARP extension placement
- Configured Vercel `rootDirectory=rxhcc-app` to prevent Python dependency installation
- Updated README to reflect OpenAI-compatible LLM stack (removed Bedrock/AWS references)

### Fixed
- Added `rxhcc-app/.env.example` with documented LLM environment variables
- Added comment to `mcp/server.js` explaining tool name difference from `api/mcp.js`
- Resolved stale closure issue in AutoResearch loop using useRef + useState dual pattern
- Fixed Vercel build pipeline (2GB sagemaker install → 2min build with rootDirectory config)

### Verified
- 97% design-to-implementation match rate (Check phase passed)
- All 6 UI modules functional with synthetic data
- MCP server integration with SHARP headers validated
- FHIR data adapter tested with real patient scenarios
- LLM provider selection (Groq/Ollama) confirmed working
- Production deployment live at https://hcendgame-fwa.vercel.app

## Technical Highlights

### Architecture Decisions Validated
1. **Low-level MCP Server API** — Correct SHARP extension nesting in `result.capabilities.extensions`
2. **Stateless Vercel serverless** — Fresh Server instance per request, no state leaks
3. **useRef + useState pattern** — Async loop without stale closures in React
4. **Zero-dependency clinical engine** — Pure JS ICD-10/NDC/HCC rules for instant validation
5. **OpenAI-compatible abstraction** — Supports Groq + Ollama without vendor lock-in

### Lessons Learned
- MCP protocol details matter; high-level wrappers can hide nuances
- Explicit `rootDirectory` critical for multi-language projects on Vercel
- Async LLM loops need careful state management (useRef for closure freshness)
- FHIR integration requires explicit extension support (SHARP headers)
- Environment variable setup should be templated from first commit

---

## Previous Work (Archive)

Historical FWA dataset, QuickStart, and Athena/QuickSight integration documented in `_archive/`.

---

**Report**: See `docs/04-report/rxhcc-app.report.md` for complete PDCA cycle summary.  
**Live URL**: https://hcendgame-fwa.vercel.app  
**Challenge**: Prompt Opinion "Agents Assemble" Hackathon
