# HCendGame FWA — MCP Server

**Prompt Opinion Agents Assemble Challenge — Superpower (MCP) Track**

An MCP server exposing 6 healthcare fraud detection tools, powered by Amazon Nova Pro and a clinical ICD-10/NDC/HCC rule engine. Supports FHIR R4 and SHARP Extension Specs.

## Tools

| Tool | Description |
|------|-------------|
| `validate_claim` | Single claim FWA check — ICD-10/NDC/HCC cross-validation |
| `batch_analyze` | Bulk analysis with anomaly rate + fraud/waste/abuse breakdown |
| `get_provider_network` | Kickback ring and hub provider detection |
| `query_investigator` | Natural-language → structured evidence brief (Nova Pro) |
| `run_autoresearch` | One AutoResearch iteration — Nova Pro proposes rule, keep/discard |
| `fetch_fhir_claims` | Pull FHIR R4 claims via SHARP context, run FWA analysis |

## SHARP Extension Specs

Pass healthcare context via MCP request metadata:

```
x-sharp-patient-id:    <FHIR Patient resource ID>
x-sharp-fhir-token:    <Bearer token>
x-sharp-fhir-base-url: <FHIR server base URL>
x-sharp-encounter-id:  <optional encounter scope>
```

## Quick Start

```bash
cd mcp
npm install
node server.js
```

### Environment Variables

```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

No AWS credentials → rule-based mode only (Nova Pro tools return mock responses).

## Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hcendgame-fwa": {
      "command": "node",
      "args": ["/path/to/rxhcc-app/mcp/server.js"],
      "env": {
        "AWS_ACCESS_KEY_ID": "...",
        "AWS_SECRET_ACCESS_KEY": "...",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

## Example: validate_claim

```json
{
  "tool": "validate_claim",
  "arguments": {
    "drugNdc": "00006-3026",
    "icd10Codes": ["I10", "E78.5"],
    "hccCodes": [18],
    "units": 2,
    "providerId": "NPI-1234567890"
  }
}
```

**Response:**
```json
{
  "claimId": "CLM-1713300000000",
  "flags": [{
    "type": "FRAUD",
    "rule": "THERAPEUTIC_MISMATCH",
    "severity": "HIGH",
    "detail": "Keytruda billed without qualifying oncology diagnosis",
    "confidence": 0.94
  }],
  "recommendation": "DENY",
  "riskScore": 0.94
}
```

## Live Demo

**React app:** [hcendgame-fwa.vercel.app](https://hcendgame-fwa.vercel.app/)  
**Repo:** [github.com/sechan9999/HCendGame](https://github.com/sechan9999/HCendGame)
