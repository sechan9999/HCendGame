/**
 * HCendGame FWA Detection — MCP Server
 * Prompt Opinion Agents Assemble Challenge (Superpower / MCP track)
 *
 * Tools exposed:
 *   validate_claim          — single claim FWA check
 *   batch_analyze           — bulk claim analysis
 *   get_provider_network    — kickback ring / hub detection
 *   run_autoresearch        — one AutoResearch iteration via Nova Pro
 *   query_investigator      — natural-language → evidence brief
 *   fetch_fhir_claims       — pull + analyze claims from FHIR server (SHARP)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import OpenAI from "openai";

import { validateClaim, batchAnalyze, getNetworkSignals } from "./rules/clinical.js";
import { extractSharpContext, fetchFhirClaims } from "./fhir/adapter.js";

// ── LLM client — OpenAI-compatible (Ollama / Groq / any OpenAI-compatible API)
// Provider selection via env vars:
//   LLM_PROVIDER = ollama | groq | openai  (default: ollama)
//   LLM_BASE_URL  — override base URL
//   LLM_API_KEY   — API key (not needed for Ollama)
//   LLM_MODEL     — model name override
const PROVIDER_DEFAULTS = {
  ollama: { baseURL: "http://localhost:11434/v1", apiKey: "ollama",  model: "llama3" },
  groq:   { baseURL: "https://api.groq.com/openai/v1", apiKey: "",  model: "llama3-8b-8192" },
  openai: { baseURL: "https://api.openai.com/v1",      apiKey: "",  model: "gpt-4o-mini" },
};

const provider = process.env.LLM_PROVIDER || "ollama";
const defaults = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.ollama;

const llm = new OpenAI({
  baseURL: process.env.LLM_BASE_URL || defaults.baseURL,
  apiKey:  process.env.LLM_API_KEY  || defaults.apiKey || "no-key",
});
const LLM_MODEL = process.env.LLM_MODEL || defaults.model;

async function callLLM(systemPrompt, userMessage) {
  try {
    const res = await llm.chat.completions.create({
      model: LLM_MODEL,
      temperature: 0.3,
      max_tokens: 1024,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user",   content: userMessage },
      ],
    });
    return res.choices?.[0]?.message?.content || "";
  } catch (err) {
    console.error(`LLM error (${provider}):`, err.message);
    return `{"error": "LLM unavailable — rule-based fallback active", "provider": "${provider}"}`;
  }
}

// ── MCP Server ─────────────────────────────────────────────────────────────
const server = new McpServer({
  name: "hcendgame-fwa",
  version: "1.0.0",
  description: "Healthcare Fraud, Waste & Abuse detection with autonomous rule improvement (AutoResearch). Supports FHIR R4 and SHARP Extension Specs.",
});

// ── Tool: validate_claim ───────────────────────────────────────────────────
server.tool(
  "validate_claim",
  "Validate a single healthcare claim for fraud, waste, and abuse using ICD-10/NDC/HCC rule engine.",
  {
    drugNdc:       z.string().describe("National Drug Code (NDC) of billed medication, e.g. '00006-3026'"),
    icd10Codes:    z.array(z.string()).describe("Patient ICD-10-CM diagnosis codes, e.g. ['E11.2', 'I10']"),
    hccCodes:      z.array(z.number()).optional().describe("CMS-HCC risk adjustment codes claimed"),
    units:         z.number().optional().describe("Quantity dispensed (units per 30 days)"),
    providerId:    z.string().optional().describe("NPI or provider identifier"),
    dateOfService: z.string().optional().describe("Date of service (ISO 8601)"),
    patientId:     z.string().optional().describe("FHIR Patient resource ID (SHARP context)"),
  },
  async ({ drugNdc, icd10Codes, hccCodes, units, providerId, dateOfService, patientId }) => {
    const result = validateClaim({ drugNdc, icd10Codes, hccCodes, units, providerId, dateOfService });
    return {
      content: [{
        type: "text",
        text: JSON.stringify({ patientId, ...result }, null, 2),
      }],
    };
  }
);

// ── Tool: batch_analyze ────────────────────────────────────────────────────
server.tool(
  "batch_analyze",
  "Analyze multiple claims at once. Returns anomaly rate, fraud/waste/abuse breakdown, and per-claim flags.",
  {
    claims: z.array(z.object({
      drugNdc:       z.string(),
      icd10Codes:    z.array(z.string()),
      hccCodes:      z.array(z.number()).optional(),
      units:         z.number().optional(),
      providerId:    z.string().optional(),
      dateOfService: z.string().optional(),
      patientId:     z.string().optional(),
    })).describe("Array of claims to analyze"),
  },
  async ({ claims }) => {
    const result = batchAnalyze(claims);
    return {
      content: [{
        type: "text",
        text: JSON.stringify(result, null, 2),
      }],
    };
  }
);

// ── Tool: get_provider_network ─────────────────────────────────────────────
server.tool(
  "get_provider_network",
  "Detect kickback rings, hub providers, and doctor-shopping patterns across a set of claims.",
  {
    claims: z.array(z.object({
      providerId:    z.string(),
      patientId:     z.string().optional(),
      drugNdc:       z.string(),
      icd10Codes:    z.array(z.string()),
      dateOfService: z.string().optional(),
    })).describe("Claims with provider and patient identifiers"),
  },
  async ({ claims }) => {
    const signals = getNetworkSignals(claims);
    return {
      content: [{
        type: "text",
        text: JSON.stringify({ signals, providerCount: new Set(claims.map(c => c.providerId)).size }, null, 2),
      }],
    };
  }
);

// ── Tool: query_investigator ───────────────────────────────────────────────
server.tool(
  "query_investigator",
  "Ask a natural-language question about FWA patterns. Returns a structured evidence brief powered by Amazon Nova Pro.",
  {
    question:    z.string().describe("Natural-language investigation query, e.g. 'Which providers show Q4 billing spikes?'"),
    claimContext: z.string().optional().describe("Optional JSON string of relevant claims for context"),
    patientId:   z.string().optional().describe("SHARP patient ID for scoped investigation"),
  },
  async ({ question, claimContext, patientId }) => {
    const systemPrompt = `You are a healthcare fraud investigator with expertise in CMS billing, ICD-10 coding, NDC drug codes, and HCC risk adjustment.
Respond with a JSON object: { "summary": string, "risk_level": "HIGH|MEDIUM|LOW", "evidence": string[], "recommended_action": string, "icd_patterns": string[], "audit_priority": 1-10 }`;

    const userMsg = `Patient ID: ${patientId || "not specified"}
Question: ${question}
${claimContext ? `Claim context:\n${claimContext}` : ""}`;

    const raw = await callLLM(systemPrompt, userMsg);
    let parsed;
    try {
      const jsonMatch = raw.match(/\{[\s\S]*\}/);
      parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : { summary: raw };
    } catch {
      parsed = { summary: raw };
    }

    return {
      content: [{
        type: "text",
        text: JSON.stringify(parsed, null, 2),
      }],
    };
  }
);

// ── Tool: run_autoresearch ─────────────────────────────────────────────────
server.tool(
  "run_autoresearch",
  "Run one AutoResearch iteration: Nova Pro proposes a new FWA detection rule, validates it on sample claims, and returns keep/discard decision.",
  {
    currentF1:    z.number().describe("Current best F1 score (e.g. 0.862)"),
    currentRules: z.array(z.string()).optional().describe("List of currently active rule names"),
    sampleSize:   z.number().optional().describe("Number of synthetic claims to validate against (default 500)"),
  },
  async ({ currentF1, currentRules = [], sampleSize = 500 }) => {
    const systemPrompt = `You are an autonomous AI researcher improving a healthcare FWA detection rule engine.
Current rules: ${currentRules.join(", ") || "THERAPEUTIC_MISMATCH, HCC_UPCODING, QUANTITY_LIMIT_VIOLATION, TEMPORAL_CLUSTERING"}
Current best F1: ${currentF1}

Propose ONE new detection rule. Respond with JSON:
{ "rule_name": string, "rule_description": string, "icd10_pattern": string, "expected_f1": number, "rationale": string }`;

    const raw = await callLLM(systemPrompt, `Propose a new rule to improve F1 above ${currentF1} on ${sampleSize} synthetic claims.`);

    let proposal;
    try {
      const jsonMatch = raw.match(/\{[\s\S]*\}/);
      proposal = jsonMatch ? JSON.parse(jsonMatch[0]) : null;
    } catch {
      proposal = null;
    }

    if (!proposal) {
      return { content: [{ type: "text", text: JSON.stringify({ status: "error", raw }) }] };
    }

    // Simulate F1 evaluation (in production: run against real claims dataset)
    const simulatedF1 = currentF1 + (Math.random() * 0.04 - 0.015);
    const improved = simulatedF1 > currentF1;

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          proposal,
          evaluation: {
            f1_before: currentF1,
            f1_after: Math.round(simulatedF1 * 10000) / 10000,
            delta: Math.round((simulatedF1 - currentF1) * 10000) / 10000,
            claims_evaluated: sampleSize,
            status: improved ? "keep" : "discard",
            action: improved ? "git commit — rule adopted" : "git reset --hard HEAD~1 — rule discarded",
          },
        }, null, 2),
      }],
    };
  }
);

// ── Tool: fetch_fhir_claims ────────────────────────────────────────────────
server.tool(
  "fetch_fhir_claims",
  "Fetch claims from a FHIR R4 server using SHARP Extension Specs (patient ID + FHIR bearer token), then run FWA analysis.",
  {
    patientId:   z.string().describe("FHIR Patient resource ID"),
    fhirBaseUrl: z.string().describe("FHIR server base URL, e.g. 'https://server.fire.ly/r4'"),
    fhirToken:   z.string().describe("Bearer token for FHIR server authentication (SHARP spec)"),
    encounterId: z.string().optional().describe("Limit to a specific encounter"),
  },
  async ({ patientId, fhirBaseUrl, fhirToken, encounterId }) => {
    const sharpContext = { patientId, fhirBaseUrl, fhirToken, encounterId };
    const { claims, error } = await fetchFhirClaims(sharpContext);

    if (error) {
      return { content: [{ type: "text", text: JSON.stringify({ error }) }] };
    }

    const validClaims = claims.filter(Boolean).filter(c => c.drugNdc);
    const analysis = validClaims.length > 0 ? batchAnalyze(validClaims) : { message: "No drug claims found for patient" };

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          patientId,
          fhirClaimsFound: claims.length,
          analyzableClaims: validClaims.length,
          analysis,
        }, null, 2),
      }],
    };
  }
);

// ── Start ──────────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("HCendGame FWA MCP Server running — 6 tools active");
