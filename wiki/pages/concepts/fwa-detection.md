# Healthcare FWA Detection

**Tags**: fwa, fraud, waste, abuse, icd10, ndc, hcc, cms

## Definitions

- **Fraud**: Intentional deception for financial gain (e.g., Keytruda billed without cancer diagnosis)
- **Waste**: Overutilization without intent (e.g., Ozempic for hypertension-only patients)
- **Abuse**: Inconsistent practices (e.g., HCC upcoding to inflate CMS risk scores)

Scale: $100–300 billion annually in the US.

## Core Rule Engine (clinical.js)

Four primary detection rules:

| Rule | Trigger | Example |
|------|---------|---------|
| THERAPEUTIC_MISMATCH | Drug NDC doesn't match any patient ICD-10 | Keytruda with no oncology code |
| HCC_UPCODING | HCC codes claimed don't match ICD-10 diagnoses | HCC19 (diabetes+CKD) without E11.22 |
| QUANTITY_LIMIT_VIOLATION | Units > 30-day supply threshold | >120 units/30 days for GLP-1 |
| TEMPORAL_CLUSTERING | Multiple claims in same 30-day window | 3+ prescriptions in one month |

## NDC / ICD-10 Mapping

Selected high-risk drugs:
- `00006-3026` — Keytruda (pembrolizumab) → requires C-series ICD-10
- `00169-4060` — Ozempic (semaglutide) → requires E11.x or E13.x
- `00002-1433` — Mounjaro (tirzepatide) → requires E11.x
- `57894-0023` — Trulicity (dulaglutide) → requires E11.x

## 5 Hackathon Fraud Scenarios

1. GLP-1 off-label (Ozempic for hypertension-only) — WASTE
2. HCC upcoding (fake diabetes+CKD complexity) — ABUSE
3. Oncology drug diversion (Keytruda, no cancer dx) — FRAUD
4. Normal diabetic care — CONTROL (no flag)
5. Duplicate billing (same drug, same patient, 3×/month) — FRAUD

## Network Detection

- Hub providers: NPI appearing in >3 patient claims
- Doctor-shopping: Patient visiting >2 providers for same drug
- Kickback rings: Provider pairs sharing >2 patients

## AutoResearch F1

Best rule configuration achieves F1=0.878 on 500 synthetic claims (15% anomaly rate).

**Related**: [[autoresearch]], [[mcp-sharp-extension]], [[rxhcc-app]]
