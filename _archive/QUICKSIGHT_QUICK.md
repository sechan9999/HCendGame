# ⚡ QuickSight 빠른 시작 (5분 버전)

바쁘신 분들을 위한 초고속 가이드!

## 🚀 3단계로 끝내기

### 1️⃣ 가입 (2분)
```
1. https://aws.amazon.com/quicksight/ 접속
2. "Try QuickSight" 클릭
3. Edition: Standard (60일 무료)
4. Region: US East (N. Virginia)
5. "Finish"
```

### 2️⃣ 업로드 (1분)
```
1. "Datasets" → "New dataset"
2. "Upload a file"
3. 파일 선택: insurance_fwa_data.csv
4. "Save & visualize"
```

### 3️⃣ 차트 만들기 (2분)
```
필수 차트 3개만:

📊 Bar Chart: fwa_type
   - X-axis: fwa_type
   - Value: claim_id (Count)

🥧 Pie Chart: risk_category
   - Group: risk_category
   - Value: claim_id (Count)

📈 Line Chart: Monthly Trend
   - X-axis: year_month
   - Value: is_fwa (Sum)
```

**완료!** 🎉

대시보드 게시: "Share" → "Publish dashboard"

---

## 💡 한 줄 팁

- **필터 추가**: state, risk_category 필터 추가하면 인터랙티브!
- **KPI 카드**: claim_amount (Sum)으로 총액 표시
- **색상**: FWA는 빨간색 (#e74c3c) 추천
- **공유**: Email로 팀원 초대 가능

---

## 📸 스크린샷 잊지 마세요!

1. 전체 대시보드 한 장
2. 차트 상세 한 장
3. GitHub README에 추가!

---

**상세 가이드**: [QUICKSIGHT_GUIDE.md](QUICKSIGHT_GUIDE.md) 참고

**질문?** 
- AWS 문서: https://docs.aws.amazon.com/quicksight/
- 유튜브: "AWS QuickSight Tutorial"
