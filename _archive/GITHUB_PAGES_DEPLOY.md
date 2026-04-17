# 🌐 GitHub Pages로 FWA 대시보드 배포하기

## 왜 GitHub Pages?
- ✅ **완전 무료** (AWS 비용 없음!)
- ✅ **커스텀 도메인** 지원
- ✅ **HTTPS** 자동 제공
- ✅ **CDN** 빠른 속도
- ✅ **Git 통합** 쉬운 업데이트

---

## 🚀 5분 배포 가이드

### Step 1: 파일 이름 변경
```bash
# fwa_dashboard.html을 index.html로 복사
copy fwa_dashboard.html index.html

# Git에 추가
git add index.html
git commit -m "Add dashboard as index.html for GitHub Pages"
git push
```

### Step 2: GitHub Pages 활성화
```
1. GitHub 저장소 접속:
   https://github.com/sechan9999/FWAdetection

2. "Settings" 탭 클릭

3. 왼쪽 메뉴에서 "Pages" 클릭

4. Source 설정:
   Branch: main
   Folder: / (root)

5. "Save" 클릭

6. 1-2분 대기...

7. URL 나타남:
   https://sechan9999.github.io/FWAdetection/
```

### Step 3: 확인!
```
브라우저에서 열기:
https://sechan9999.github.io/FWAdetection/

✅ 대시보드가 보이면 성공!
```

---

## 📋 README에 라이브 데모 링크 추가

```markdown
## 📊 Live Demo

🔗 **[View Interactive Dashboard](https://sechan9999.github.io/FWAdetection/)**

![Dashboard Preview](screenshots/dashboard_preview.png)

### Features:
- Interactive Chart.js visualizations
- Real-time filtering
- 5,000 insurance claims analyzed
- 10 FWA detection patterns
```

---

##🎨 커스텀 도메인 (선택사항)

원하는 도메인이 있다면:

```
1. 도메인 구매 (Namecheap, GoDaddy 등)
   예: fwa-dashboard.com

2. DNS 설정:
   Type: CNAME
   Name: www
   Value: sechan9999.github.io

3. GitHub Pages 설정에서:
   Custom domain: www.fwa-dashboard.com
   ☑️ Enforce HTTPS

4. 완료!
   https://www.fwa-dashboard.com
```

---

## 🔄 업데이트 방법

대시보드 수정 후:

```bash
# 대시보드 재생성
python generate_dashboard.py

# index.html 업데이트
copy fwa_dashboard.html index.html

# Git 푸시
git add index.html
git commit -m "Update dashboard"
git push

# 자동으로 배포됨! (1-2분 소요)
```

---

## 💡 Pro Tips

### Tip 1: README에 배지 추가
```markdown
[![Live Demo](https://img.shields.io/badge/Demo-Live-success?style=for-the-badge)](https://sechan9999.github.io/FWAdetection/)
```

### Tip 2: 스크린샷 추가
```markdown
## Preview
![Dashboard](https://sechan9999.github.io/FWAdetection/screenshots/dashboard.png)
```

### Tip 3: Google Analytics 추가
```html
<!-- index.html의 <head> 안에 추가 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

---

## 🆚 비교: S3 vs GitHub Pages

| 항목 | S3 Static Website | GitHub Pages |
|------|-------------------|--------------|
| 비용 | ~$0.50/month | **무료** |
| HTTPS | CloudFront 필요 ($) | **자동 포함** |
| 커스텀 도메인 | 가능 | **무료 포함** |
| CDN | CloudFront 필요 ($) | **자동 포함** |
| 업데이트 | 수동 업로드 | **Git push** |
| 설정 난이도 | 중간 | **쉬움** |

**결론: GitHub Pages 추천! ⭐⭐⭐⭐⭐**

---

## ✅ 체크리스트

- [ ] index.html 생성
- [ ] Git push
- [ ] GitHub Pages 활성화
- [ ] URL 확인
- [ ] README에 링크 추가
- [ ] 스크린샷 추가
- [ ] LinkedIn에 공유
- [ ] 포트폴리오에 추가

---

**배포 시간**: 5분  
**비용**: $0  
**난이도**: ⭐ (매우 쉬움)
