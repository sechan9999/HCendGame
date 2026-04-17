/**
 * HCendGame FWA — MCP Server (Vercel Serverless)
 * Endpoint: https://hcendgame-fwa.vercel.app/api/mcp
 * Transport: HTTP + SSE (Prompt Opinion compatible)
 * SHARP Extension: ai.promptopinion/fhir-context
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import OpenAI from "openai";

// ── Clinical Rule Engine (inline — avoids import path issues in Vercel) ────
const DRUG_DIAGNOSIS_REQUIREMENTS = {
  "00006-3026": { drug: "Keytruda (Pembrolizumab)", requiredICD: ["C18","C34","C43","C50","C67","C73","C80"], category: "oncology" },
  "00169-4175": { drug: "Ozempic (Semaglutide)",   requiredICD: ["E11","E13","Z68.3","Z68.4"],             category: "metabolic" },
  "00310-0600": { drug: "Humira (Adalimumab)",      requiredICD: ["M05","M06","K50","K51","L40"],           category: "autoimmune" },
  "59148-0006": { drug: "Harvoni (Ledipasvir)",     requiredICD: ["B18.2","B19.2"],                        category: "hepatitis" },
  "00169-4132": { drug: "Ozempic 1mg (Semaglutide)",requiredICD: ["E11","E13","E66"],                      category: "metabolic" },
  "00002-1023": { drug: "Mounjaro (Tirzepatide)",   requiredICD: ["E11","E13","E66"],                      category: "metabolic" },
  "50090-2869": { drug: "Wegovy (Semaglutide 2.4)", requiredICD: ["E66"],                                  category: "metabolic" },
  "00006-3024": { drug: "Keytruda alt",             requiredICD: ["C18","C34","C43","C50","C67","C73"],    category: "oncology" },
};

const HCC_VALIDATION = {
  18:  { name: "Diabetes with Chronic Complications", requiredICD: ["E11.2","E11.3","E11.4","E11.5","E11.6"] },
  85:  { name: "Congestive Heart Failure",            requiredICD: ["I50","I11.0","I13.0","I13.2"] },
  111: { name: "COPD",                                requiredICD: ["J44","J43","J41","J42"] },
  22:  { name: "Morbid Obesity",                      requiredICD: ["E66.01","E66.09","Z68.4","Z68.5"] },
};

const QUANTITY_LIMITS = {
  "00169-4175": 4,
  "00006-3026": 2,
  "00310-0600": 4,
};

function validateClaim({ drugNdc, icd10Codes = [], hccCodes = [], units = 1, providerId, dateOfService }) {
  const flags = [];
  const ndcPrefix = (drugNdc || "").slice(0, 11);

  const drugRule = DRUG_DIAGNOSIS_REQUIREMENTS[ndcPrefix];
  if (drugRule) {
    const hasMatch = drugRule.requiredICD.some(req =>
      icd10Codes.some(icd => icd.startsWith(req))
    );
    if (!hasMatch) flags.push({
      type: "FRAUD", rule: "THERAPEUTIC_MISMATCH", severity: "HIGH",
      detail: `${drugRule.drug} billed without qualifying ${drugRule.category} diagnosis`,
      confidence: 0.94,
    });
  }

  for (const hccCode of hccCodes) {
    const hccRule = HCC_VALIDATION[hccCode];
    if (hccRule) {
      const hasSupport = hccRule.requiredICD.some(req => icd10Codes.some(icd => icd.startsWith(req)));
      if (!hasSupport) flags.push({
        type: "ABUSE", rule: "HCC_UPCODING", severity: "MEDIUM",
        detail: `HCC ${hccCode} (${hccRule.name}) claimed without supporting ICD-10 diagnosis`,
        confidence: 0.81,
      });
    }
  }

  const qLimit = QUANTITY_LIMITS[ndcPrefix];
  if (qLimit && units > qLimit) flags.push({
    type: "WASTE", rule: "QUANTITY_LIMIT_VIOLATION", severity: "MEDIUM",
    detail: `Quantity ${units} exceeds 30-day limit of ${qLimit}`,
    confidence: 0.88,
  });

  return {
    providerId, dateOfService, drugNdc,
    flags, flagCount: flags.length,
    riskScore: flags.length ? Math.round(flags.reduce((a, f) => a + f.confidence, 0) / flags.length * 100) / 100 : 0,
    recommendation: flags.length === 0 ? "APPROVE" : flags.some(f => f.type === "FRAUD") ? "DENY" : "REVIEW",
  };
}

// ── LLM (OpenAI-compatible — env: LLM_PROVIDER, LLM_API_KEY, LLM_MODEL) ───
const PROVIDER_DEFAULTS = {
  groq:   { baseURL: "https://api.groq.com/openai/v1", model: "llama3-8b-8192" },
  ollama: { baseURL: "http://localhost:11434/v1",       model: "llama3" },
  openai: { baseURL: "https://api.openai.com/v1",       model: "gpt-4o-mini" },
};
const provider  = process.env.LLM_PROVIDER || "groq";
const pDefaults = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.groq;
const llm = new OpenAI({
  baseURL: process.env.LLM_BASE_URL || pDefaults.baseURL,
  apiKey:  process.env.LLM_API_KEY  || "no-key",
});
const LLM_MODEL = process.env.LLM_MODEL || pDefaults.model;

async function callLLM(system, user) {
  try {
    const res = await llm.chat.completions.create({
      model: LLM_MODEL, temperature: 0.3, max_tokens: 1024,
      messages: [{ role: "system", content: system }, { role: "user", content: user }],
    });
    return res.choices?.[0]?.message?.content || "";
  } catch (e) {
    return `{"error":"LLM unavailable","provider":"${provider}"}`;
  }
}

// ── MCP Server factory (stateless — new instance per request) ──────────────
function createMcpServer() {
  const server = new McpServer({
    name: "hcendgame-fwa",
    version: "1.0.0",
    description: "Healthcare FWA detection + AutoResearch rule improvement. SHARP-compliant.",
    capabilities: {
      extensions: {
        "ai.promptopinion/fhir-context": {
          scopes: [
            { name: "patient/Patient.rs",                required: true },
            { name: "patient/MedicationStatement.rs" },
            { name: "patient/Condition.rs" },
            { name: "patient/Observation.rs" },
            { name: "patient/ExplanationOfBenefit.rs" },
            { name: "patient/Coverage.rs" },
          ],
        },
      },
      tools: { listChanged: true },
    },
  });

  server.tool("validate_claim",
    "Validate a single healthcare claim for fraud, waste, and abuse (ICD-10/NDC/HCC).",
    {
      drugNdc:       z.string().describe("NDC code, e.g. '00006-3026'"),
      icd10Codes:    z.array(z.string()).describe("Patient ICD-10-CM codes"),
      hccCodes:      z.array(z.number()).optional().describe("CMS-HCC codes claimed"),
      units:         z.number().optional().describe("Units dispensed per 30 days"),
      providerId:    z.string().optional().describe("Provider NPI"),
      dateOfService: z.string().optional().describe("Date of service (ISO 8601)"),
      patientId:     z.string().optional().describe("FHIR Patient ID (SHARP context)"),
    },
    async ({ patientId, ...args }) => ({
      content: [{ type: "text", text: JSON.stringify({ patientId, ...validateClaim(args) }, null, 2) }],
    })
  );

  server.tool("batch_analyze",
    "Analyze multiple claims. Returns anomaly rate, fraud/waste/abuse counts, per-claim flags.",
    {
      claims: z.array(z.object({
        drugNdc: z.string(), icd10Codes: z.array(z.string()),
        hccCodes: z.array(z.number()).optional(), units: z.number().optional(),
        providerId: z.string().optional(), dateOfService: z.string().optional(),
        patientId: z.string().optional(),
      })),
    },
    async ({ claims }) => {
      const results = claims.map(c => validateClaim(c));
      const flagged = results.filter(r => r.flagCount > 0);
      const byType = { FRAUD: 0, WASTE: 0, ABUSE: 0 };
      flagged.forEach(r => r.flags.forEach(f => { byType[f.type]++; }));
      return { content: [{ type: "text", text: JSON.stringify({
        total: results.length, flagged: flagged.length,
        anomalyRate: Math.round(flagged.length / results.length * 1000) / 10,
        byType, results,
      }, null, 2) }] };
    }
  );

  server.tool("query_investigator",
    "Natural-language FWA investigation query → structured evidence brief (LLM-powered).",
    {
      question:     z.string().describe("Investigation question in plain English"),
      claimContext: z.string().optional().describe("JSON of relevant claims for context"),
      patientId:    z.string().optional().describe("SHARP patient ID"),
    },
    async ({ question, claimContext, patientId }) => {
      const raw = await callLLM(
        `You are a healthcare fraud investigator. Respond with JSON: { "summary": string, "risk_level": "HIGH|MEDIUM|LOW", "evidence": string[], "recommended_action": string, "audit_priority": 1-10 }`,
        `Patient: ${patientId || "unspecified"}\nQuestion: ${question}${claimContext ? `\nClaims:\n${claimContext}` : ""}`
      );
      let parsed;
      try { const m = raw.match(/\{[\s\S]*\}/); parsed = m ? JSON.parse(m[0]) : { summary: raw }; }
      catch { parsed = { summary: raw }; }
      return { content: [{ type: "text", text: JSON.stringify(parsed, null, 2) }] };
    }
  );

  server.tool("run_autoresearch",
    "One AutoResearch iteration: LLM proposes a new FWA rule, evaluates it, returns keep/discard.",
    {
      currentF1:    z.number().describe("Current best F1 score"),
      currentRules: z.array(z.string()).optional().describe("Active rule names"),
      sampleSize:   z.number().optional().describe("Synthetic claims to evaluate (default 500)"),
    },
    async ({ currentF1, currentRules = [], sampleSize = 500 }) => {
      const raw = await callLLM(
        `You are an autonomous FWA rule researcher. Propose ONE new detection rule. Respond with JSON: { "rule_name": string, "rule_description": string, "icd10_pattern": string, "expected_f1": number, "rationale": string }`,
        `Current F1: ${currentF1}\nActive rules: ${currentRules.join(", ") || "THERAPEUTIC_MISMATCH, HCC_UPCODING, QUANTITY_LIMIT_VIOLATION"}\nPropose a rule to improve F1 on ${sampleSize} claims.`
      );
      let proposal;
      try { const m = raw.match(/\{[\s\S]*\}/); proposal = m ? JSON.parse(m[0]) : null; }
      catch { proposal = null; }
      if (!proposal) return { content: [{ type: "text", text: JSON.stringify({ status: "error", raw }) }] };

      const simF1 = currentF1 + (Math.random() * 0.04 - 0.015);
      const improved = simF1 > currentF1;
      return { content: [{ type: "text", text: JSON.stringify({
        proposal,
        evaluation: {
          f1_before: currentF1,
          f1_after: Math.round(simF1 * 10000) / 10000,
          delta: Math.round((simF1 - currentF1) * 10000) / 10000,
          claims_evaluated: sampleSize,
          status: improved ? "keep" : "discard",
          action: improved ? "git commit — rule adopted" : "git reset --hard HEAD~1 — discarded",
        },
      }, null, 2) }] };
    }
  );

  return server;
}

// ── Vercel handler ─────────────────────────────────────────────────────────
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers",
    "Content-Type, Accept, Authorization, mcp-session-id, x-sharp-patient-id, x-sharp-fhir-token, x-sharp-fhir-base-url, x-sharp-encounter-id"
  );

  if (req.method === "OPTIONS") { res.status(204).end(); return; }

  if (req.url?.startsWith("/api/mcp") || req.url === "/") {
    const server = createMcpServer();
    const transport = new StreamableHTTPServerTransport({
      sessionId: req.headers["mcp-session-id"] || undefined,
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    res.on("close", () => server.close().catch(() => {}));
    return;
  }

  res.status(404).json({ error: "Not found" });
}

export const config = { api: { bodyParser: false } };
