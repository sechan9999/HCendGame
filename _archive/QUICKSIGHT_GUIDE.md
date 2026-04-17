# 🚀 AWS QuickSight 업로드 완벽 가이드

## 📋 목차
1. [QuickSight 가입하기](#1-quicksight-가입하기)
2. [데이터 업로드하기](#2-데이터-업로드하기)
3. [대시보드 만들기](#3-대시보드-만들기)
4. [스타일링 & 공유](#4-스타일링--공유)

---

## 1. QuickSight 가입하기 (5분)

### Step 1.1: AWS 콘솔 접속
```
URL: https://aws.amazon.com/quicksight/
```

**클릭 순서:**
1. "Start free trial" 또는 "Sign up" 버튼 클릭
2. AWS 계정으로 로그인 (없으면 생성)

### Step 1.2: QuickSight 에디션 선택
```
✅ Edition: Standard
   - 60일 무료 체험
   - 기본 기능 모두 포함
   - $12/month after trial

❌ Enterprise: 지금은 선택 안 함
   - ML 인사이트 필요할 때만
   - $18-24/month
```

### Step 1.3: 계정 설정
```
Account name: fwa-detection-demo
Region: US East (N. Virginia) 또는 US East (Ohio)
Email: [your-email]
```

### Step 1.4: S3 권한 설정 (선택사항)
- ☑️ Amazon S3 체크
- "Select S3 buckets" → "Select all" (나중에 S3 사용하려면)
- 지금은 스킵해도 됨 (CSV 직접 업로드할 거니까)

**완료!** ✅ "Finish" 버튼 클릭

---

## 2. 데이터 업로드하기 (2분)

### Step 2.1: QuickSight 콘솔 열기
```
QuickSight 홈페이지 → "Datasets" 메뉴 클릭
```

### Step 2.2: 새 데이터셋 생성
```
1. 우측 상단 "New dataset" 버튼 클릭
2. 데이터 소스 선택: "Upload a file" 클릭
```

### Step 2.3: CSV 파일 업로드
```
파일 경로:
C:\Users\secha\.gemini\antigravity\scratch\mcp_agents\
rxhcc_risk_adjustment\insurance_fwa_data.csv

또는 샘플 파일:
insurance_fwa_data_sample.csv (500 records)
```

**업로드 클릭!**

### Step 2.4: 데이터 미리보기 (중요!)
```
"Edit/Preview data" 클릭하여 데이터 타입 확인:

✅ 확인할 필드:
- claim_amount: Decimal ✓
- fwa_risk_score: Decimal ✓
- service_date: DateTime ✓
- is_fwa: Int ✓
- state, city, fwa_type: String ✓

잘못된 경우 왼쪽 열 이름 클릭 → 타입 변경
```

**"Save & visualize" 클릭!**

---

## 3. 대시보드 만들기 (15분)

### 📊 Visual 1: KPI Cards (총 4개)

#### KPI 1: Total Claims Amount
```
1. 좌측 "Visual types" → "KPI" 선택
2. "Value" → claim_amount 드래그
3. Aggregation: Sum
4. 상단 제목 클릭 → "Total Claims Amount" 입력
5. Format → Currency → USD
```

#### KPI 2: FWA Detected Count
```
1. "Add" → "Add visual" → "KPI"
2. "Value" → is_fwa 드래그
3. Aggregation: Sum
4. Title: "FWA Detected"
```

#### KPI 3: FWA Detection Rate
```
1. "Add" → "Add visual" → "KPI"
2. Filter 추가:
   - Fields list → is_fwa 우클릭 → "Add as filter"
   - Filter type: Custom filter
   - Formula: {is_fwa} / count({claim_id}) * 100
3. Title: "FWA Rate %"
```

#### KPI 4: High Risk Count
```
1. "Add" → "Add visual" → "KPI"
2. Filter: fwa_risk_score > 0.8
3. Value: claim_id (Count)
4. Title: "High Risk Claims"
```

---

### 📊 Visual 2: FWA Type Distribution (Bar Chart)

```
1. "Add" → "Add visual"
2. Visual type: Vertical bar chart
3. 설정:
   - X-axis: fwa_type
   - Value: claim_id (Count)
   - Sort: Descending by Value
   - Color: #e74c3c (빨간색)
4. Title: "FWA Type Distribution"
5. Legend: Hide
```

**꿀팁:** 
- Field wells → Value → Format → Show as: Number (with commas)
- Axis → Show grid lines: ☑️

---

### 🥧 Visual 3: Risk Category Pie Chart

```
1. "Add" → "Add visual"
2. Visual type: Pie chart
3. 설정:
   - Group by: risk_category
   - Value: claim_id (Count)
   - Colors:
     * Low: #27ae60 (녹색)
     * Medium: #3498db (파란색)
     * High: #f39c12 (주황색)
     * Critical: #e74c3c (빨간색)
4. Title: "Risk Category Distribution"
5. Show percentages: ☑️
```

---

### 📈 Visual 4: Monthly Trend (Line Chart)

```
1. "Add" → "Add visual"
2. Visual type: Line chart
3. 설정:
   - X-axis: year_month (Date hierarchy: Month)
   - Lines:
     * Line 1: claim_id (Count) - Blue #3498db
     * Line 2: is_fwa (Sum) - Red #e74c3c
   - Legend: Show (top)
4. Title: "Monthly Claims & FWA Trend"
5. Data markers: Show
6. Line style: Smooth
```

---

### 🗺️ Visual 5: State-wise FWA Rate (Horizontal Bar)

```
1. "Add" → "Add visual"
2. Visual type: Horizontal bar chart
3. 설정:
   - Y-axis: state
   - Value: Calculated field 생성
     Name: fwa_rate
     Formula: sum({is_fwa}) / count({claim_id}) * 100
   - Sort: Descending
   - Color: Gradient (Low: Yellow, High: Red)
4. Title: "State-wise FWA Rate (%)"
5. Show top 10 states
```

**Calculated Field 만들기:**
```
1. Fields → "Add calculated field"
2. Name: fwa_rate_percent
3. Formula: 
   sum({is_fwa}) / count({claim_id}) * 100
4. "Save"
```

---

### 🏥 Visual 6: Specialty Analysis (Horizontal Bar)

```
1. "Add" → "Add visual"
2. Visual type: Horizontal bar chart
3. 설정:
   - Y-axis: specialty
   - Value: fwa_risk_score (Average)
   - Sort: Descending
   - Color: #9b59b6 (보라색)
4. Title: "Average FWA Risk by Specialty"
```

---

### 📋 Visual 7: Top High-Risk Providers (Table)

```
1. "Add" → "Add visual"
2. Visual type: Table
3. Columns (순서대로):
   - provider_id
   - specialty
   - fwa_risk_score (Average)
   - claim_id (Count) → Rename: "Total Claims"
   - claim_amount (Sum) → Format: Currency
4. Filters:
   - fwa_risk_score > 0.7
5. Sort: fwa_risk_score Descending
6. Title: "High-Risk Providers"
7. Conditional formatting:
   - fwa_risk_score > 0.85 → Red background
   - fwa_risk_score > 0.70 → Orange text
```

**Conditional Formatting 설정:**
```
1. Table 우클릭 → "Conditional formatting"
2. Column: fwa_risk_score
3. Condition:
   - Greater than: 0.85
   - Background color: #ffcccc (연한 빨강)
4. "Apply"
```

---

## 4. 스타일링 & 공유 (5분)

### Step 4.1: 대시보드 레이아웃 정리

```
레이아웃 추천 (위에서 아래로):

┌─────────────────────────────────────────────────┐
│  [KPI 1] [KPI 2] [KPI 3] [KPI 4]              │  ← Row 1
├─────────────────────────────────────────────────┤
│  [FWA Type Bar]    [Risk Category Pie]         │  ← Row 2
├─────────────────────────────────────────────────┤
│  [Monthly Trend Line Chart - Full Width]       │  ← Row 3
├─────────────────────────────────────────────────┤
│  [State Bars]      [Specialty Bars]            │  ← Row 4
├─────────────────────────────────────────────────┤
│  [High-Risk Provider Table - Full Width]       │  ← Row 5
└─────────────────────────────────────────────────┘
```

**드래그 앤 드롭으로 위치 조정!**

### Step 4.2: 필터 추가

```
1. Filter pane (왼쪽) → "+" 클릭
2. 추가할 필터:
   
   Filter 1: state
   - Type: Multi-select dropdown
   - Apply to: All visuals
   
   Filter 2: risk_category
   - Type: Single-select dropdown
   - Apply to: All visuals
   
   Filter 3: specialty
   - Type: Multi-select list
   - Apply to: All visuals
   
   Filter 4: service_date
   - Type: Date range
   - Default: All dates
   - Apply to: All visuals
```

### Step 4.3: 테마 설정

```
1. 상단 "Themes" → "Edit"
2. 색상 팔레트 선택:
   - Palette: "Midnight" (어두운 테마)
   - 또는 "Minimal" (깔끔한 흰색)
3. Font: Helvetica 또는 Arial
4. Border: Minimal
5. "Apply"
```

### Step 4.4: 대시보드 게시!

```
1. 우측 상단 "Share" → "Publish dashboard"
2. Name: "FWA Detection Dashboard"
3. Description: 
   "Healthcare fraud detection system analyzing 5,000 claims
    with 10 sophisticated FWA patterns"
4. "Publish" 클릭

✅ 대시보드 URL이 생성됩니다!
예: https://us-east-1.quicksight.aws.amazon.com/...
```

### Step 4.5: 공유 설정

```
공유 옵션:

1. 팀원 초대:
   "Share" → "Share dashboard"
   → Email 입력 → "Share"

2. Public 링크 (조심!):
   "Share" → "Manage dashboard access"
   → "Enable public access"
   → Copy link

3. 임베드 코드:
   "Share" → "Embed"
   → Copy iframe code
```

---

## 📸 스크린샷 가이드

### GitHub README에 추가할 스크린샷:

1. **전체 대시보드**
   - 파일명: `quicksight_dashboard_full.png`
   - 캡처: 전체 화면

2. **KPI Cards**
   - 파일명: `quicksight_kpis.png`
   - 캡처: 상단 KPI 섹션만

3. **차트 상세**
   - 파일명: `quicksight_charts.png`
   - 캡처: FWA Type + Risk Category 차트

4. **필터 사용 예시**
   - 파일명: `quicksight_filters.png`
   - 캡처: 필터 적용된 상태

### GitHub에 추가하기:

```bash
# 프로젝트 폴더에 screenshots 폴더 생성
mkdir screenshots
cd screenshots

# 스크린샷 저장 (Windows: Win+Shift+S)
# 파일명: quicksight_dashboard_full.png 등

# Git 커밋
git add screenshots/
git commit -m "Add QuickSight dashboard screenshots"
git push
```

### README 업데이트:

```markdown
## 📊 QuickSight Dashboard Preview

### Full Dashboard
![QuickSight Dashboard](screenshots/quicksight_dashboard_full.png)

### KPI Cards
![KPI Cards](screenshots/quicksight_kpis.png)

### Interactive Charts
![Charts](screenshots/quicksight_charts.png)

### Live Demo
🔗 [View Live Dashboard](https://quicksight.aws.amazon.com/...)
```

---

## 🎯 체크리스트

완료하면 체크하세요!

- [ ] QuickSight 가입 완료
- [ ] CSV 파일 업로드 완료
- [ ] KPI Cards 4개 생성
- [ ] FWA Type Bar Chart 생성
- [ ] Risk Category Pie Chart 생성
- [ ] Monthly Trend Line Chart 생성
- [ ] State Analysis Bar Chart 생성
- [ ] Specialty Analysis 생성
- [ ] High-Risk Provider Table 생성
- [ ] Calculated Field (fwa_rate) 생성
- [ ] 필터 4개 추가
- [ ] 레이아�t 정리 완료
- [ ] 대시보드 게시 완료
- [ ] 스크린샷 캡처 완료
- [ ] GitHub README 업데이트 완료

---

## 🚨 트러블슈팅

### 문제 1: 데이터 타입이 잘못됨
```
해결: Edit/Preview data → 열 클릭 → Change data type
```

### 문제 2: 차트가 비어있음
```
해결: Field wells 확인 → 올바른 Aggregation 선택
```

### 문제 3: Calculated Field 오류
```
해결: 문법 확인
- sum({field_name}) ← 중괄호 필수!
- 나누기: /
- 곱하기: *
```

### 문제 4: 한글이 깨짐
```
해결: CSV 인코딩을 UTF-8로 변경 후 재업로드
```

### 문제 5: 비용 걱정
```
해결: 
- 60일 무료 체험 중에는 무료
- 체험 끝나기 전 알림 받음
- 언제든 취소 가능
```

---

## 💡 Pro Tips

### Tip 1: Auto-refresh 설정
```
Dataset → Schedule refresh
→ Daily at 6 AM
→ Data stays fresh!
```

### Tip 2: 모바일에서 보기
```
QuickSight 모바일 앱 다운로드
→ iOS/Android 지원
→ 이동 중에도 대시보드 확인!
```

### Tip 3: 이메일 리포트
```
Dashboard → Schedule email
→ PDF 첨부
→ 매주 월요일 8AM 발송
```

### Tip 4: 드릴다운
```
차트 클릭 → "Drill down" 옵션
→ 상세 데이터 탐색
→ provider_id까지 드릴다운 가능!
```

### Tip 5: 북마크
```
필터 조합 저장
→ "Bookmark this view"
→ 자주하는 분석 빠르게 접근
```

---

## 📚 다음 단계

### Level 2: 고급 기능
```
1. Amazon Q 통합
   - 자연어로 질문
   - "Show me providers with fraud rate > 50%"
   
2. ML Insights (Enterprise)
   - 자동 이상치 탐지
   - 예측 분석
   
3. Embedded Analytics
   - 자신의 웹사이트에 대시보드 삽입
   - iframe 또는 SDK 사용
```

### Level 3: 자동화
```
1. S3 자동 동기화
   - Lambda 함수로 CSV 자동 업로드
   - 매일 자동 갱신
   
2. API 통합
   - QuickSight API로 대시보드 관리
   - 프로그래밍 방식으로 제어
```

---

## 🎉 완료!

축하합니다! 이제 프로페셔널한 QuickSight 대시보드가 완성되었습니다!

**다음 할 일:**
1. ✅ 스크린샷 캡처
2. ✅ GitHub README 업데이트
3. ✅ 포트폴리오에 링크 추가
4. ✅ 이력서에 프로젝트 추가
5. ✅ LinkedIn에 게시!

---

**생성 날짜:** 2026-02-09  
**버전:** 1.0  
**난이도:** ⭐⭐ (쉬움)  
**소요 시간:** ~30분
