# 🔍 AWS Athena + QuickSight 완벽 가이드

## 왜 Athena를 사용하나요?

**Athena**는 S3 데이터를 SQL로 직접 쿼리할 수 있는 서버리스 서비스입니다.

### 💡 장점:
- ✅ **서버리스** - 인프라 관리 불필요
- ✅ **쿼리 당 과금** - 사용한 만큼만 지불 (~$5/TB)
- ✅ **S3 직접 쿼리** - 데이터 이동 불필요
- ✅ **표준 SQL** - 익숙한 문법
- ✅ **QuickSight 통합** - 완벽한 조합!

---

## 🚀 5단계 설정 가이드

### Step 1: S3 데이터 확인 (완료!)

당신의 데이터는 이미 여기에 있습니다:
```
s3://fwa-detection-demo/insurance_fwa_data.csv
```

✅ 준비 완료!

---

### Step 2: Athena 콘솔 열기

```
1. AWS 콘솔 로그인
2. 서비스 → "Athena" 검색
3. "Query editor" 선택
```

또는 직접 접속:
```
https://console.aws.amazon.com/athena/
```

---

### Step 3: Athena 초기 설정

#### 3.1 Query Result Location 설정 (처음만!)

```
1. Athena 콘솔에서 "Settings" 클릭
2. "Manage" 클릭
3. Query result location:
   s3://fwa-detection-demo/athena-results/
4. "Save" 클릭
```

이 폴더에 쿼리 결과가 저장됩니다.

#### 3.2 Database 생성

```sql
-- Athena Query Editor에서 실행:
CREATE DATABASE IF NOT EXISTS fwa_analytics;
```

실행: "Run" 버튼 클릭

---

### Step 4: External Table 생성

#### 4.1 Database 선택
```
왼쪽 "Database" 드롭다운 → "fwa_analytics" 선택
```

#### 4.2 Table 생성 SQL 실행

`athena_queries.sql` 파일의 CREATE TABLE 문을 복사해서 실행:

```sql
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
```

✅ "Run" 클릭!

#### 4.3 테이블 확인

```sql
-- 테이블 목록 확인
SHOW TABLES;

-- 스키마 확인
DESCRIBE fwa_detection_data;

-- 샘플 데이터 조회
SELECT * FROM fwa_detection_data LIMIT 10;
```

---

### Step 5: 데이터 분석 쿼리 실행!

이제 SQL로 자유롭게 분석할 수 있습니다!

#### 📊 기본 통계
```sql
SELECT 
    COUNT(*) as total_claims,
    SUM(is_fwa) as fwa_claims,
    ROUND(SUM(is_fwa) * 100.0 / COUNT(*), 2) as fwa_rate_pct,
    SUM(claim_amount) as total_amount,
    SUM(CASE WHEN is_fwa = 1 THEN claim_amount ELSE 0 END) as fwa_amount
FROM fwa_detection_data;
```

**예상 결과:**
```
total_claims: 5000
fwa_claims: 1029
fwa_rate_pct: 20.58%
total_amount: $895,425
fwa_amount: $184,201
```

#### 🔍 고위험 제공자
```sql
SELECT 
    provider_id,
    specialty,
    COUNT(*) as total_claims,
    ROUND(AVG(fwa_risk_score), 3) as avg_risk_score
FROM fwa_detection_data
GROUP BY provider_id, specialty
HAVING AVG(fwa_risk_score) > 0.7
ORDER BY avg_risk_score DESC
LIMIT 20;
```

#### 🗺️ 주별 FWA 비율
```sql
SELECT 
    state,
    COUNT(*) as total_claims,
    SUM(is_fwa) as fwa_claims,
    ROUND(SUM(is_fwa) * 100.0 / COUNT(*), 2) as fwa_rate_pct
FROM fwa_detection_data
GROUP BY state
ORDER BY fwa_rate_pct DESC;
```

더 많은 쿼리는 `athena_queries.sql` 파일 참고!

---

## 🎨 QuickSight와 Athena 연결

이제 QuickSight에서 Athena 테이블을 데이터 소스로 사용할 수 있습니다!

### Step 1: QuickSight에서 New Dataset 생성

```
1. QuickSight 콘솔 → "Datasets"
2. "New dataset" 클릭
3. 데이터 소스: "Athena" 선택
```

### Step 2: Athena 연결 설정

```
1. Data source name: "FWA-Athena-Connection"
2. Athena workgroup: [primary] (기본값)
3. "Create data source" 클릭
```

### Step 3: 테이블 선택

```
1. Database: fwa_analytics
2. Table: fwa_detection_data
3. "Select" 클릭
```

### Step 4: 데이터 가져오기 방식 선택

두 가지 옵션:

#### Option A: Direct Query (추천!)
```
✅ 장점:
- 항상 최신 데이터
- S3 데이터 변경 시 자동 반영
- 스토리지 비용 없음

❌ 단점:
- 쿼리마다 Athena 비용 발생 (~$0.01/query)
- 약간 느릴 수 있음
```

#### Option B: SPICE (QuickSight 캐시)
```
✅ 장점:
- 매우 빠른 성능
- Athena 쿼리 비용 절약

❌ 단점:
- 수동 새로고침 필요
- SPICE 용량 제한 (10GB 무료)
```

**추천:** 개발/테스트 시 Direct Query, 프로덕션에서 SPICE

### Step 5: 시각화 생성!

이제 QuickSight에서 차트를 만들 수 있습니다!

---

## 💰 비용 계산

### Athena 비용
```
쿼리당 스캔 데이터량 기준:
$5 / TB

우리 데이터 (970KB CSV):
- 한 번 쿼리: ~$0.000005 (거의 무료!)
- 1000번 쿼리: ~$0.005 (0.5센트)

월 예상 비용: < $1
```

### QuickSight 비용
```
Standard Edition:
- 60일 무료 체험
- 이후: $12/월/사용자

Enterprise Edition:
- $18-24/월/사용자
- ML 인사이트 포함
```

**총 월 비용: ~$13 (체험 기간 후)**

---

## 🎯 Athena vs CSV 업로드 비교

| 항목 | CSV 직접 업로드 | Athena + S3 |
|------|----------------|-------------|
| **설정 난이도** | ⭐ 쉬움 | ⭐⭐ 중간 |
| **데이터 크기** | < 25MB | 무제한 |
| **쿼리 성능** | 빠름 (SPICE) | 빠름 (파티션 시) |
| **데이터 업데이트** | 수동 재업로드 | S3만 업데이트 |
| **비용** | QuickSight만 | QuickSight + Athena |
| **전문성** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**언제 Athena 사용?**
- ✅ 데이터가 이미 S3에 있음 (당신!)
- ✅ 데이터가 자주 업데이트됨
- ✅ 대용량 데이터 (> 1GB)
- ✅ 여러 도구에서 같은 데이터 사용
- ✅ 이력서에 "Athena" 추가하고 싶음! 💼

---

## 📚 고급 기능

### 1. Partitioning (대용량 데이터 최적화)

데이터가 커지면 파티션 추가:

```sql
CREATE EXTERNAL TABLE fwa_detection_partitioned (
    claim_id string,
    claim_amount double,
    -- ... 기타 컬럼
)
PARTITIONED BY (
    year int,
    month int
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES ('field.delim' = ',')
LOCATION 's3://fwa-detection-demo/partitioned/';

-- 파티션 추가
ALTER TABLE fwa_detection_partitioned ADD
PARTITION (year=2024, month=1) LOCATION 's3://fwa-detection-demo/partitioned/year=2024/month=01/';
```

### 2. Parquet 변환 (비용 절감!)

CSV → Parquet으로 변환하면 쿼리 비용 90% 절감:

```sql
-- CTAS (Create Table As Select)
CREATE TABLE fwa_detection_parquet
WITH (
    format = 'PARQUET',
    parquet_compression = 'SNAPPY'
) AS
SELECT * FROM fwa_detection_data;
```

### 3. Views 생성

자주 사용하는 쿼리를 View로 저장:

```sql
CREATE VIEW high_risk_providers AS
SELECT 
    provider_id,
    specialty,
    COUNT(*) as claims,
    AVG(fwa_risk_score) as avg_risk,
    SUM(claim_amount) as total_amount
FROM fwa_detection_data
GROUP BY provider_id, specialty
HAVING AVG(fwa_risk_score) > 0.7;

-- View 사용
SELECT * FROM high_risk_providers
ORDER BY avg_risk DESC;
```

---

## 🛠️ 트러블슈팅

### 문제 1: "HIVE_CANNOT_OPEN_SPLIT" 오류
```
원인: CSV 파일 형식 문제
해결:
1. CSV가 UTF-8 인코딩인지 확인
2. 콤마(,)가 필드 구분자인지 확인
3. 헤더가 첫 번째 줄에만 있는지 확인
```

### 문제 2: timestamp 파싱 오류
```
원인: 날짜 형식 불일치
해결: service_date를 string으로 변경 후 CAST 사용

SELECT 
    CAST(service_date AS timestamp) as parsed_date
FROM fwa_detection_data;
```

### 문제 3: 쿼리 결과가 비어있음
```
확인 사항:
1. S3 버킷에 파일이 있는지 확인
2. LOCATION 경로가 정확한지 확인
3. IAM 권한 확인 (Athena → S3 읽기 권한)
```

### 문제 4: QuickSight에서 Athena 연결 실패
```
해결:
1. QuickSight → Manage QuickSight
2. Security & permissions
3. "Manage" under AWS Services
4. ☑️ Athena 체크
5. ☑️ S3 버킷 선택 (fwa-detection-demo)
6. Save
```

---

## 📖 추가 리소스

### AWS 공식 문서
- [Athena 사용 설명서](https://docs.aws.amazon.com/athena/)
- [QuickSight + Athena 통합](https://docs.aws.amazon.com/quicksight/latest/user/create-a-data-source-athena.html)

### SQL 레퍼런스
- [Athena SQL 레퍼런스](https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html)
- [Presto 함수](https://prestodb.io/docs/current/functions.html) (Athena는 Presto 기반)

---

## ✅ 완료 체크리스트

- [ ] Athena 콘솔 접속
- [ ] Query result location 설정
- [ ] Database 생성 (fwa_analytics)
- [ ] External Table 생성 (fwa_detection_data)
- [ ] 샘플 쿼리 실행
- [ ] QuickSight 가입
- [ ] QuickSight → Athena 연결
- [ ] 대시보드 생성
- [ ] 스크린샷 캡처
- [ ] 이력서에 "AWS Athena" 추가! 💼

---

## 🎓 이력서에 추가할 기술

✅ AWS Athena (SQL on S3)  
✅ AWS QuickSight (BI Dashboard)  
✅ AWS S3 (Data Lake)  
✅ Presto SQL  
✅ Big Data Analytics  
✅ Serverless Architecture  

**한 문장 요약:**
"S3 데이터 레이크를 Athena로 쿼리하고 QuickSight로 시각화하는 FWA 탐지 시스템 구축"

---

**난이도:** ⭐⭐⭐ (중급)  
**소요 시간:** 30분  
**비용:** ~$1/월 (체험 기간 제외)  
**전문성:** ⭐⭐⭐⭐⭐ (매우 높음!)
