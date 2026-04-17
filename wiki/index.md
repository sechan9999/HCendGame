# Wiki Index — HCendGame FWA Detection

Content-oriented catalog. One line per page. Update when adding pages.

---

## Concepts

| Page | Summary |
|------|---------|
| [[autoresearch]] | Karpathy LOOP FOREVER applied to FWA rule improvement; F1 0.821→0.878; useRef+useState pattern |
| [[fwa-detection]] | Healthcare Fraud/Waste/Abuse domain: ICD-10/NDC/HCC rules, 5 fraud scenarios, network detection |
| [[mcp-sharp-extension]] | Prompt Opinion FHIR context extension; 6 FHIR R4 scopes; SHARP headers; required capabilities location |

## Decisions

| Page | Summary |
|------|---------|
| [[mcpserver-vs-server]] | Why low-level Server class is required for Prompt Opinion; McpServer puts capabilities in wrong location |
| [[vercel-rootdirectory]] | How rootDirectory=rxhcc-app prevents Vercel from detecting Python and installing 2GB dependencies |

## Entities

| Page | Summary |
|------|---------|
| [[rxhcc-app]] | Main app entity; tech stack, 6 UI modules, key files, deploy status |
| [[prompt-opinion]] | MCP marketplace platform; integration requirements; feedback filed during hackathon |

## Lessons

| Page | Summary |
|------|---------|
| [[async-loop-stale-closure]] | useRef+useState dual pattern to prevent stale closure in React async loops |

---

## How to Add a Page

1. Create file in the appropriate `pages/` subfolder
2. Add one-line entry to this index under the right category
3. Append to `log.md`: `[date] ingest: <source> → <page>`
