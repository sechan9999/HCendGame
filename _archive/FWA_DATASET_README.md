# 📊 FWA Data Analysis for QuickSight

## Overview
This dataset contains **5,000 synthetic insurance claims** with realistic Fraud, Waste, and Abuse (FWA) patterns designed for AWS QuickSight analysis.

## Dataset Statistics
- **Total Claims**: 5,000
- **Date Range**: January 1, 2025 - December 31, 2025
- **Providers**: 50 unique healthcare providers
- **Members**: 500 unique insurance members
- **States Covered**: 10 (CA, TX, FL, NY, PA, IL, OH, GA, NC, MI)

## FWA Patterns Included

### 🚨 Fraud Patterns (High Severity)
1. **Upcoding** (0.28%): Billing for higher-level services than provided
2. **Phantom Billing** (1.46%): Billing for services never rendered
3. **Unbundling** (2.14%): Splitting bundled procedures into separate bills
4. **Duplicate Claims** (0.26%): Billing same service multiple times
5. **Kickback Pattern** (0.16%): Suspicious referral patterns
6. **Time Fraud** (0.02%): Non-emergency services billed during unusual hours

### ⚠️ Abuse Patterns (Medium Severity)
7. **Off-Label Drug** (5.48%): GLP-1 prescribed without proper diagnosis
8. **Excessive Opioid** (0.58%): Early opioid refills
9. **PT Mill** (1.28%): Excessive physical therapy sessions

### 💸 Waste Patterns (Lower Severity)
10. **Unnecessary Service** (0.22%): High-cost imaging for routine exams

## File Structure

### Main Dataset: `insurance_fwa_data.csv`
| Column | Description | Example |
|--------|-------------|---------|
| `claim_id` | Unique claim identifier | CLM_000001 |
| `member_id` | Patient identifier | MEM_00145 |
| `provider_id` | Healthcare provider ID | PROV_0007 |
| `specialty` | Provider specialty | Primary Care |
| `state` | Service location state | CA |
| `city` | Service location city | Los Angeles |
| `diagnosis_code` | ICD-10 diagnosis code | E11.9 |
| `diagnosis_name` | Diagnosis description | Type 2 Diabetes |
| `cpt_code` | Procedure code | 99214 |
| `service_name` | Service description | Office Visit Level 4 |
| `claim_amount` | Billed amount in USD | 127.50 |
| `service_date` | Date and time of service | 2025-03-15 14:30:00 |
| `service_rendered` | Whether service was actually provided (0/1) | 1 |
| `ndc_code` | National Drug Code (if applicable) | 00169-7501-11 |
| `drug_name` | Medication name | Ozempic (GLP-1) |
| `fwa_risk_score` | Risk score 0.0-1.0 | 0.854 |
| `is_fwa` | FWA flag (0=clean, 1=suspicious) | 1 |
| `fwa_type` | Type of FWA pattern detected | UPCODING |
| `fwa_explanation` | Human-readable explanation | Office visit upcoded from Level 3 to Level 5 |
| `year_month` | Month of service | 2025-03 |
| `day_of_week` | Day of service | Monday |
| `risk_category` | Risk level | Critical |

## QuickSight Dashboard Ideas

### 📈 Recommended Visualizations

#### 1. **Executive Summary Dashboard**
- KPI Cards:
  - Total Claims Amount
  - FWA Amount Detected
  - FWA Rate %
  - High-Risk Claims Count
- Donut Chart: Risk Category Distribution
- Bar Chart: Top 10 FWA Types

#### 2. **Geographic Analysis**
- Heat Map: FWA Rate by State
- Map: Provider Locations with Risk Scores
- Table: City-Level FWA Statistics

#### 3. **Temporal Trends**
- Line Chart: Monthly FWA Trend
- Heat Map: Day of Week vs Hour (for time fraud detection)
- Area Chart: Claim Volume Over Time

#### 4. **Provider Analytics**
- Table: Top 20 High-Risk Providers
- Scatter Plot: Provider Specialty vs Avg Risk Score
- Funnel Chart: Provider Investigation Pipeline

#### 5. **Medical Code Analysis**
- Bar Chart: Diagnosis Codes with Highest FWA Rate
- Tree Map: CPT Codes by Total Amount
- Network Graph: Drug-Diagnosis Correlations

#### 6. **Detailed Investigation**
- Pivot Table: Provider × FWA Type Matrix
- Waterfall Chart: FWA Financial Impact
- Combo Chart: Volume vs Amount by Category

## AWS QuickSight Setup Guide

### Step 1: Upload Dataset
```bash
1. Log in to AWS QuickSight Console
2. Click "Datasets" → "New dataset"
3. Select "Upload a file"
4. Upload: insurance_fwa_data.csv
5. Click "Next"
```

### Step 2: Configure Data Types
Ensure these field types are correct:
- `claim_amount`: Decimal
- `fwa_risk_score`: Decimal  
- `service_date`: DateTime
- `is_fwa`: Integer
- `state`, `city`, `fwa_type`: String
- `risk_category`: String (set as dimension)

### Step 3: Create Analysis
```bash
1. Click "Use in analysis"
2. Name your analysis: "FWA Detection Dashboard"
3. Start adding visualizations
```

### Step 4: Add Calculated Fields

**FWA Amount**:
```
ifelse({is_fwa} = 1, {claim_amount}, 0)
```

**FWA Rate %**:
```
sum({fwa_amount}) / sum({claim_amount}) * 100
```

**Risk Tier**:
```
ifelse({fwa_risk_score} > 0.8, "Critical",
       {fwa_risk_score} > 0.6, "High",
       {fwa_risk_score} > 0.3, "Medium",
       "Low")
```

## Sample Queries for Analysis

### High-Risk Providers
```sql
SELECT 
    provider_id,
    specialty,
    state,
    COUNT(*) as total_claims,
    SUM(CASE WHEN is_fwa = 1 THEN 1 ELSE 0 END) as fwa_claims,
    AVG(fwa_risk_score) as avg_risk,
    SUM(claim_amount) as total_amount
FROM insurance_fwa_data
GROUP BY provider_id, specialty, state
HAVING AVG(fwa_risk_score) > 0.5
ORDER BY avg_risk DESC
LIMIT 20;
```

### Monthly FWA Trend
```sql
SELECT 
    year_month,
    COUNT(*) as claims,
    SUM(CASE WHEN is_fwa = 1 THEN 1 ELSE 0 END) as fwa_count,
    SUM(CASE WHEN is_fwa = 1 THEN claim_amount ELSE 0 END) as fwa_amount
FROM insurance_fwa_data
GROUP BY year_month
ORDER BY year_month;
```

### FWA by Specialty
```sql
SELECT 
    specialty,
    fwa_type,
    COUNT(*) as occurrences,
    AVG(claim_amount) as avg_amount
FROM insurance_fwa_data
WHERE is_fwa = 1
GROUP BY specialty, fwa_type
ORDER BY occurrences DESC;
```

## Financial Impact Summary

Based on generated data:
- **Total Claims Value**: ~$895,000
- **FWA Claims Value**: ~$184,000 (20.57%)
- **Average FWA Claim**: $310
- **Estimated Annual Loss** (if representative): **$2.2M - $2.5M**

## Real-World Applications

This dataset can be used to:
1. **Train ML models** for FWA detection
2. **Test fraud detection algorithms** before production
3. **Demonstrate analytics capabilities** to stakeholders
4. **Prototype investigation workflows**
5. **Benchmark detection rules** against known patterns

## Next Steps

1. ✅ Upload to QuickSight
2. 📊 Create dashboards using suggested visualizations
3. 🔍 Add filters for interactive exploration
4. 📧 Set up alerts for high-risk claims
5. 🤖 Integrate with AWS SageMaker for ML-based detection
6. 📱 Share dashboards with audit team

## Technical Notes

- **Data Quality**: 100% synthetic, HIPAA-compliant
- **Realism Level**: Based on CMS fraud patterns
- **Update Frequency**: Re-generate monthly with new seed
- **Storage**: Can be moved to S3 for QuickSight SPICE refresh

## Support

For questions or issues:
- Check the generator code: `engine/fwa_data_generator.py`
- Regenerate with different parameters
- Adjust FWA pattern probabilities in `_apply_fwa_pattern()` method

---

**Generated**: 2026-02-09  
**Version**: 1.0  
**Records**: 5,000 claims | 500 members | 50 providers
