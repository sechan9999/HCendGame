-- ========================================
-- AWS Athena Table Creation for FWA Data
-- ========================================
-- This creates an external table in Athena that queries data directly from S3
-- No data movement required! Query S3 data with SQL.

CREATE EXTERNAL TABLE IF NOT EXISTS fwa_detection_data (
    claim_id string,
    claim_amount double,
    service_date timestamp,
    member_id string,
    provider_id string,
    specialty string,
    state string,
    city string,
    diagnosis_code string,
    diagnosis_name string,
    cpt_code string,
    service_name string,
    ndc_code string,
    drug_name string,
    fwa_risk_score double,
    is_fwa int,
    fwa_type string,
    fwa_explanation string,
    risk_category string,
    service_rendered int
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
    'serialization.format' = ',',
    'field.delim' = ','
) 
LOCATION 's3://fwa-detection-demo/'
TBLPROPERTIES (
    'has_encrypted_data'='false', 
    'skip.header.line.count'='1'
);

-- ========================================
-- Sample Queries
-- ========================================

-- Query 1: Get total claims and FWA summary
SELECT 
    COUNT(*) as total_claims,
    SUM(is_fwa) as fwa_claims,
    ROUND(SUM(is_fwa) * 100.0 / COUNT(*), 2) as fwa_rate_pct,
    SUM(claim_amount) as total_amount,
    SUM(CASE WHEN is_fwa = 1 THEN claim_amount ELSE 0 END) as fwa_amount
FROM fwa_detection_data;

-- Query 2: FWA by type
SELECT 
    fwa_type,
    COUNT(*) as count,
    ROUND(AVG(fwa_risk_score), 3) as avg_risk_score,
    SUM(claim_amount) as total_amount
FROM fwa_detection_data
WHERE is_fwa = 1
GROUP BY fwa_type
ORDER BY count DESC;

-- Query 3: High-risk providers
SELECT 
    provider_id,
    specialty,
    COUNT(*) as total_claims,
    SUM(is_fwa) as fwa_claims,
    ROUND(AVG(fwa_risk_score), 3) as avg_risk_score,
    SUM(claim_amount) as total_amount
FROM fwa_detection_data
GROUP BY provider_id, specialty
HAVING AVG(fwa_risk_score) > 0.7
ORDER BY avg_risk_score DESC
LIMIT 20;

-- Query 4: State-wise FWA analysis
SELECT 
    state,
    COUNT(*) as total_claims,
    SUM(is_fwa) as fwa_claims,
    ROUND(SUM(is_fwa) * 100.0 / COUNT(*), 2) as fwa_rate_pct,
    SUM(claim_amount) as total_amount
FROM fwa_detection_data
GROUP BY state
ORDER BY fwa_rate_pct DESC;

-- Query 5: Monthly trend
SELECT 
    DATE_TRUNC('month', service_date) as month,
    COUNT(*) as total_claims,
    SUM(is_fwa) as fwa_claims,
    ROUND(SUM(is_fwa) * 100.0 / COUNT(*), 2) as fwa_rate_pct
FROM fwa_detection_data
GROUP BY DATE_TRUNC('month', service_date)
ORDER BY month;

-- Query 6: Risk category distribution
SELECT 
    risk_category,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM fwa_detection_data
GROUP BY risk_category
ORDER BY count DESC;

-- Query 7: Specialty analysis
SELECT 
    specialty,
    COUNT(*) as claims,
    SUM(is_fwa) as fwa_cases,
    ROUND(AVG(fwa_risk_score), 3) as avg_risk,
    ROUND(SUM(is_fwa) * 100.0 / COUNT(*), 2) as fwa_pct
FROM fwa_detection_data
GROUP BY specialty
ORDER BY fwa_pct DESC;

-- Query 8: Top expensive FWA claims
SELECT 
    claim_id,
    provider_id,
    specialty,
    claim_amount,
    fwa_type,
    fwa_risk_score,
    fwa_explanation
FROM fwa_detection_data
WHERE is_fwa = 1
ORDER BY claim_amount DESC
LIMIT 50;

-- Query 9: Opioid prescription analysis
SELECT 
    provider_id,
    specialty,
    COUNT(*) as opioid_prescriptions,
    SUM(CASE WHEN is_fwa = 1 THEN 1 ELSE 0 END) as suspicious_cases,
    AVG(fwa_risk_score) as avg_risk
FROM fwa_detection_data
WHERE drug_name LIKE '%Hydrocodone%' OR drug_name LIKE '%Oxycodone%'
GROUP BY provider_id, specialty
ORDER BY suspicious_cases DESC;

-- Query 10: Compare fraud types by state
SELECT 
    state,
    fwa_type,
    COUNT(*) as count,
    SUM(claim_amount) as total_loss
FROM fwa_detection_data
WHERE is_fwa = 1
GROUP BY state, fwa_type
ORDER BY state, count DESC;
