/**
 * FHIR → FWA Claim Adapter
 * SHARP Extension Specs: handles patient IDs and FHIR tokens
 * Converts FHIR R4 ExplanationOfBenefit / MedicationRequest → claim format
 */

/**
 * Extract SHARP context from MCP request metadata
 * SHARP Extension Specs pass patient context via MCP headers/extensions
 */
export function extractSharpContext(requestMeta = {}) {
  return {
    patientId:   requestMeta["x-sharp-patient-id"]   || requestMeta.patientId   || null,
    fhirToken:   requestMeta["x-sharp-fhir-token"]   || requestMeta.fhirToken   || null,
    fhirBaseUrl: requestMeta["x-sharp-fhir-base-url"] || requestMeta.fhirBaseUrl || null,
    encounterId: requestMeta["x-sharp-encounter-id"] || requestMeta.encounterId || null,
  };
}

/**
 * Fetch FHIR ExplanationOfBenefit for a patient and convert to claim array
 */
export async function fetchFhirClaims(sharpContext) {
  const { patientId, fhirToken, fhirBaseUrl } = sharpContext;
  if (!fhirBaseUrl || !fhirToken || !patientId) {
    return { error: "Missing SHARP context: fhirBaseUrl, fhirToken, patientId required", claims: [] };
  }

  const url = `${fhirBaseUrl}/ExplanationOfBenefit?patient=${patientId}&_count=50`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${fhirToken}`,
      Accept: "application/fhir+json",
    },
  });

  if (!res.ok) {
    return { error: `FHIR fetch failed: ${res.status} ${res.statusText}`, claims: [] };
  }

  const bundle = await res.json();
  return { claims: (bundle.entry || []).map(e => fhirEobToClaim(e.resource)) };
}

/**
 * Convert FHIR R4 ExplanationOfBenefit → internal claim format
 */
export function fhirEobToClaim(eob) {
  if (!eob || eob.resourceType !== "ExplanationOfBenefit") return null;

  // Extract NDC from item.productOrService coding
  const ndcCode = eob.item?.[0]?.productOrService?.coding
    ?.find(c => c.system === "http://hl7.org/fhir/sid/ndc")?.code || null;

  // Extract ICD-10 diagnosis codes
  const icd10Codes = (eob.diagnosis || [])
    .filter(d => d.diagnosisCodeableConcept?.coding
      ?.some(c => c.system === "http://hl7.org/fhir/sid/icd-10-cm"))
    .map(d => d.diagnosisCodeableConcept.coding
      .find(c => c.system === "http://hl7.org/fhir/sid/icd-10-cm")?.code)
    .filter(Boolean);

  // Extract HCC codes (CMS-HCC extension)
  const hccCodes = (eob.extension || [])
    .filter(e => e.url?.includes("cms-hcc"))
    .map(e => e.valueInteger || e.valueCode)
    .filter(Boolean);

  const providerId = eob.provider?.reference?.split("/").pop()
    || eob.careTeam?.[0]?.provider?.reference?.split("/").pop()
    || "UNKNOWN";

  return {
    patientId: eob.patient?.reference?.split("/").pop(),
    providerId,
    drugNdc: ndcCode,
    icd10Codes,
    hccCodes,
    units: eob.item?.[0]?.quantity?.value || 1,
    dateOfService: eob.billablePeriod?.start || eob.created,
    fhirId: eob.id,
  };
}

/**
 * Convert FHIR R4 MedicationRequest → claim format (for prior auth workflows)
 */
export function fhirMedRequestToClaim(medReq, patientDiagnoses = []) {
  const ndcCode = medReq.medicationCodeableConcept?.coding
    ?.find(c => c.system === "http://hl7.org/fhir/sid/ndc")?.code || null;

  return {
    patientId: medReq.subject?.reference?.split("/").pop(),
    providerId: medReq.requester?.reference?.split("/").pop() || "UNKNOWN",
    drugNdc: ndcCode,
    icd10Codes: patientDiagnoses,
    hccCodes: [],
    units: medReq.dispenseRequest?.quantity?.value || 1,
    dateOfService: medReq.authoredOn,
    fhirId: medReq.id,
  };
}
