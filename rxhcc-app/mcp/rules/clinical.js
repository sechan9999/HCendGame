/**
 * Clinical Rule Engine — ported from RXHCCnva.jsx
 * ICD-10 / NDC / HCC cross-validation for FWA detection
 */

// High-cost drugs requiring specific oncology/metabolic diagnoses
const DRUG_DIAGNOSIS_REQUIREMENTS = {
  "00006-3026": { drug: "Keytruda (Pembrolizumab)", requiredICD: ["C18","C34","C43","C50","C67","C73","C80"], category: "oncology" },
  "00169-4175": { drug: "Ozempic (Semaglutide)",   requiredICD: ["E11","E13","Z68.3","Z68.4"],             category: "metabolic" },
  "00310-0600": { drug: "Humira (Adalimumab)",      requiredICD: ["M05","M06","K50","K51","L40"],           category: "autoimmune" },
  "59148-0006": { drug: "Harvoni (Ledipasvir)",     requiredICD: ["B18.2","B19.2"],                        category: "hepatitis" },
  "00078-0661": { drug: "Cosentyx (Secukinumab)",   requiredICD: ["L40","M07","M45"],                      category: "autoimmune" },
};

// HCC codes that require corroborating ICD-10 diagnoses
const HCC_VALIDATION = {
  18:  { name: "Diabetes with Chronic Complications", requiredICD: ["E11.2","E11.3","E11.4","E11.5","E11.6"] },
  85:  { name: "Congestive Heart Failure",            requiredICD: ["I50","I11.0","I13.0","I13.2"] },
  111: { name: "COPD",                                requiredICD: ["J44","J43","J41","J42"] },
  22:  { name: "Morbid Obesity",                      requiredICD: ["E66.01","E66.09","Z68.4","Z68.5"] },
  108: { name: "Vascular Disease",                    requiredICD: ["I70","I71","I72","I73","I74","I77"] },
};

// Quantity limits per 30 days (units)
const QUANTITY_LIMITS = {
  "00169-4175": 4,   // Ozempic: 4 pens/30 days
  "00006-3026": 2,   // Keytruda: 2 vials/30 days
  "00310-0600": 4,   // Humira: 4 syringes/30 days
};

export function validateClaim({ drugNdc, icd10Codes, hccCodes, units = 1, providerId, dateOfService }) {
  const flags = [];
  const diagnosticsCodes = icd10Codes || [];
  const hccs = hccCodes || [];

  // Rule 1: Therapeutic mismatch (drug vs diagnosis)
  const drugRule = DRUG_DIAGNOSIS_REQUIREMENTS[drugNdc];
  if (drugRule) {
    const hasMatch = drugRule.requiredICD.some(req =>
      diagnosticsCodes.some(icd => icd.startsWith(req))
    );
    if (!hasMatch) {
      flags.push({
        type: "FRAUD",
        rule: "THERAPEUTIC_MISMATCH",
        severity: "HIGH",
        detail: `${drugRule.drug} billed without qualifying ${drugRule.category} diagnosis. Required ICD prefix: ${drugRule.requiredICD.slice(0,3).join(", ")}`,
        confidence: 0.94,
      });
    }
  }

  // Rule 2: HCC upcoding detection
  for (const hccCode of hccs) {
    const hccRule = HCC_VALIDATION[hccCode];
    if (hccRule) {
      const hasSupport = hccRule.requiredICD.some(req =>
        diagnosticsCodes.some(icd => icd.startsWith(req))
      );
      if (!hasSupport) {
        flags.push({
          type: "ABUSE",
          rule: "HCC_UPCODING",
          severity: "MEDIUM",
          detail: `HCC ${hccCode} (${hccRule.name}) claimed without supporting ICD-10 diagnosis`,
          confidence: 0.81,
        });
      }
    }
  }

  // Rule 3: Quantity limit violation
  const qLimit = QUANTITY_LIMITS[drugNdc];
  if (qLimit && units > qLimit) {
    flags.push({
      type: "WASTE",
      rule: "QUANTITY_LIMIT_VIOLATION",
      severity: "MEDIUM",
      detail: `Quantity ${units} exceeds 30-day limit of ${qLimit} for NDC ${drugNdc}`,
      confidence: 0.88,
    });
  }

  // Rule 4: Temporal clustering (multiple high-cost claims same date/provider)
  // Evaluated at batch level — placeholder for single-claim context
  const riskScore = flags.reduce((acc, f) => acc + f.confidence, 0) / Math.max(flags.length, 1);

  return {
    claimId: `CLM-${Date.now()}`,
    providerId,
    dateOfService,
    drugNdc,
    flags,
    flagCount: flags.length,
    riskScore: flags.length ? Math.round(riskScore * 100) / 100 : 0,
    recommendation: flags.length === 0 ? "APPROVE" : flags.some(f => f.type === "FRAUD") ? "DENY" : "REVIEW",
  };
}

export function batchAnalyze(claims) {
  const results = claims.map(c => validateClaim(c));
  const flagged = results.filter(r => r.flagCount > 0);
  const byType = { FRAUD: 0, WASTE: 0, ABUSE: 0 };
  flagged.forEach(r => r.flags.forEach(f => byType[f.type]++));

  return {
    total: results.length,
    flagged: flagged.length,
    anomalyRate: Math.round((flagged.length / results.length) * 1000) / 10,
    byType,
    results,
  };
}

export function getNetworkSignals(providerClaims) {
  // Group by provider, detect hub patterns
  const providerMap = {};
  for (const claim of providerClaims) {
    const pid = claim.providerId;
    if (!providerMap[pid]) providerMap[pid] = { claims: [], patients: new Set() };
    providerMap[pid].claims.push(claim);
    if (claim.patientId) providerMap[pid].patients.add(claim.patientId);
  }

  const signals = [];
  for (const [pid, data] of Object.entries(providerMap)) {
    const flaggedClaims = data.claims.filter(c => validateClaim(c).flagCount > 0);
    const flagRate = flaggedClaims.length / data.claims.length;
    if (flagRate > 0.3) {
      signals.push({
        providerId: pid,
        claimCount: data.claims.length,
        uniquePatients: data.patients.size,
        flagRate: Math.round(flagRate * 100),
        signal: flagRate > 0.6 ? "KICKBACK_RING_CANDIDATE" : "ELEVATED_RISK",
      });
    }
  }
  return signals;
}
