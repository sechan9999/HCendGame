# MCP SHARP Extension — Prompt Opinion FHIR Context

**Tags**: mcp, sharp, fhir, prompt-opinion, capabilities

## What SHARP Extension Does

Prompt Opinion's SHARP Extension Specs allow MCP servers to declare FHIR R4 data access requirements. When registered, Prompt Opinion injects FHIR context headers into every tool call.

## FHIR Context Headers (injected by Prompt Opinion)

```
X-FHIR-Server-URL    — FHIR base URL
X-FHIR-Access-Token  — Bearer token
X-Patient-ID         — Current patient resource ID
```

Also accepts SHARP-prefixed variants: `x-sharp-fhir-base-url`, `x-sharp-fhir-token`, `x-sharp-patient-id`

## Required Response Format

The extension declaration MUST appear in `result.capabilities.extensions` (not `serverInfo`):

```js
// Correct (low-level Server class)
const server = new Server(
  { name: "hcendgame-fwa", version: "1.0.0" },
  {
    capabilities: {
      tools: {},
      extensions: {
        "ai.promptopinion/fhir-context": {
          scopes: [
            { name: "patient/Patient.rs", required: true },
            { name: "patient/MedicationStatement.rs" },
            { name: "patient/Condition.rs" },
            { name: "patient/Observation.rs" },
            { name: "patient/ExplanationOfBenefit.rs" },
            { name: "patient/Coverage.rs" },
          ],
        },
      },
    },
  }
);
```

## Critical SDK Gotcha

`McpServer` (high-level) puts custom capabilities in `serverInfo.capabilities` — Prompt Opinion's `initialize` check looks in `result.capabilities`. → **Must use low-level `Server` class.**

See [[mcpserver-vs-server]] for the full explanation.

## 6 FHIR R4 Scopes

| Scope | Required | Use |
|-------|:--------:|-----|
| patient/Patient.rs | Yes | Demographics |
| patient/MedicationStatement.rs | No | Active medications |
| patient/Condition.rs | No | Diagnoses (ICD-10) |
| patient/Observation.rs | No | Labs, vitals |
| patient/ExplanationOfBenefit.rs | No | Claims billing data |
| patient/Coverage.rs | No | Payer/plan info |

> Note: ExplanationOfBenefit is missing from Prompt Opinion's starter template but is essential for FWA/billing analysis.

**Related**: [[mcpserver-vs-server]], [[prompt-opinion]], [[rxhcc-app]]
