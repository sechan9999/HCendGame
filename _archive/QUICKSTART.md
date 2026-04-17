# 🚀 QUICK START GUIDE - FWA Analysis Tools

## 📁 What You Have

Your RxHCC project now includes a complete FWA (Fraud, Waste & Abuse) analysis toolkit:

### ✅ Generated Files

| File | Purpose | Size |
|------|---------|------|
| `insurance_fwa_data.csv` | Full dataset (5,000 claims) | 970 KB |
| `insurance_fwa_data_sample.csv` | Sample (500 claims) | 97 KB |
| `fwa_dashboard.html` | **Interactive local dashboard** | Ready to view! |
| `quicksight_manifest.json` | QuickSight import helper | Auto-generated |

### 🛠️ Analysis Tools

| Script | Command | Purpose |
|--------|---------|---------|
| `fwa_data_generator.py` | `python engine/fwa_data_generator.py` | Generate new datasets |
| `preview_fwa_data.py` | `python preview_fwa_data.py` | View detailed statistics |
| `generate_dashboard.py` | `python generate_dashboard.py` | Create interactive HTML dashboard |
| `upload_to_quicksight.py` | `python upload_to_quicksight.py` | Upload to AWS QuickSight |

### 📚 Documentation

| Document | What's Inside |
|----------|---------------|
| `FWA_DATASET_README.md` | Complete QuickSight setup guide |
| `FWA_GENERATOR_SUMMARY.md` | Project overview & improvements |
| `QUICKSTART.md` | This file - your quick reference |

---

## ⚡ THREE WAYS TO ANALYZE YOUR DATA

### Option 1: 🌐 Local Dashboard (NO AWS NEEDED)
**Best for: Quick preview, offline analysis, sharing with team**

```bash
# Already done! Just open the file:
start fwa_dashboard.html
```

**What you'll see:**
- ✅ Executive KPI cards (Total Claims, FWA Amount, Rates)
- ✅ Interactive charts (Bar, Line, Doughnut, Heat maps)
- ✅ Top 20 high-risk providers table
- ✅ Monthly trends and state analysis

---

### Option 2: ☁️ AWS QuickSight (Cloud Analytics)
**Best for: Professional dashboards, sharing with stakeholders, advanced analytics**

#### If you have valid AWS credentials:
```bash
python upload_to_quicksight.py
```
This will:
1. ✅ Validate AWS credentials
2. ✅ Create S3 bucket
3. ✅ Upload CSV files
4. ✅ Generate manifest files
5. ✅ Show step-by-step QuickSight instructions

#### If you DON'T have AWS credentials yet:
**Manual Upload Method:**
1. Log in to [AWS QuickSight](https://quicksight.aws.amazon.com/)
2. Click **Datasets** → **New dataset** → **Upload a file**
3. Select `insurance_fwa_data.csv`
4. Follow the wizard to create analysis

📖 **Detailed instructions**: See `FWA_DATASET_README.md`

---

### Option 3: 📊 Python Analysis (Custom Scripts)
**Best for: Data scientists, custom analysis, automation**

```bash
python preview_fwa_data.py
```

**What you'll get:**
- Column summaries
- FWA pattern breakdown
- Financial impact analysis
- Risk score distribution
- Geographic patterns
- Provider rankings
- Temporal trends
- Data quality checks

---

## 🎯 COMMON TASKS

### Task 1: Generate Fresh Data
```bash
cd rxhcc_risk_adjustment
python engine/fwa_data_generator.py
```
**Customization:**
- Edit line 291: `num_records=10000` for 10K claims
- Change `seed=42` for different random data

### Task 2: View Quick Stats
```bash
python preview_fwa_data.py
```

### Task 3: Create Interactive Dashboard
```bash
python generate_dashboard.py
start fwa_dashboard.html
```

### Task 4: Upload to QuickSight
```bash
# First configure AWS (one-time)
aws configure
# Enter your Access Key, Secret Key, Region (us-east-2)

# Then upload
python upload_to_quicksight.py
```

---

## 🎨 QUICKSIGHT DASHBOARD IDEAS

Once uploaded to QuickSight, create these visuals:

### 📊 Dashboard 1: Executive Summary
```
┌─────────────────────────────────────────┐
│  KPI Cards:                             │
│  💰 Total: $895K  🚨 FWA: $184K  📊 20.5% │
├─────────────────────────────────────────┤
│  📊 Bar: FWA Type Distribution          │
│  🥧 Pie: Risk Categories                │
│  🗺️  Geo: State Heat Map                │
└─────────────────────────────────────────┘
```

### 📈 Dashboard 2: Trends & Patterns
```
┌─────────────────────────────────────────┐
│  📈 Line: Monthly FWA Trend             │
│  📊 Stacked: Specialty Analysis         │
│  🔥 Heat: Day of Week × Hour            │
└─────────────────────────────────────────┘
```

### 🔍 Dashboard 3: Investigation
```
┌─────────────────────────────────────────┐
│  📋 Table: Top 50 High-Risk Claims      │
│  🔍 Detail: Provider deep-dive          │
│  📊 Waterfall: Financial Impact         │
└─────────────────────────────────────────┘
```

**Pro Tips:**
- Use filters: State, Risk Category, FWA Type
- Add drill-downs: Click provider → See all claims
- Set up alerts: Email when high-risk claims > 100

---

## 🔧 TROUBLESHOOTING

### Issue: "AWS credentials not found"
**Solution:**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Region: us-east-2
# Output: json
```

### Issue: "File not found: insurance_fwa_data.csv"
**Solution:**
```bash
python engine/fwa_data_generator.py
```

### Issue: "Module not found: pandas"
**Solution:**
```bash
pip install pandas numpy
```

### Issue: Dashboard charts not showing
**Solution:**
- Check internet connection (Chart.js loads from CDN)
- Open in modern browser (Chrome, Firefox, Edge)
- Check browser console for errors (F12)

---

## 📊 DATA DICTIONARY

### Key Fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `claim_id` | String | Unique claim ID | CLM_000123 |
| `provider_id` | String | Provider identifier | PROV_0007 |
| `diagnosis_code` | String | ICD-10 code | E11.9 |
| `cpt_code` | String | Procedure code | 99214 |
| `ndc_code` | String | Drug code | 00169-7501-11 |
| `claim_amount` | Decimal | Bill amount ($) | 127.50 |
| `fwa_risk_score` | Decimal | Risk 0-1 | 0.854 |
| `is_fwa` | Integer | FWA flag (0/1) | 1 |
| `fwa_type` | String | Pattern type | UPCODING |
| `risk_category` | String | Risk tier | Critical |

---

## 🎯 NEXT STEPS

### For Demo/Presentation:
1. ✅ Open `fwa_dashboard.html` 
2. ✅ Walk through KPIs and charts
3. ✅ Show high-risk provider table
4. ✅ Explain FWA patterns

### For Production:
1. ⬜ Upload to AWS QuickSight
2. ⬜ Create dashboards (use templates in README)
3. ⬜ Set up scheduled data refreshes
4. ⬜ Configure email alerts
5. ⬜ Share with stakeholders

### For Further Development:
1. ⬜ Add more FWA patterns (see generator code)
2. ⬜ Integrate with real claims data
3. ⬜ Build ML models for prediction
4. ⬜ Create alerting system
5. ⬜ Develop investigation workflows

---

## 📚 LEARNING RESOURCES

### CMS Fraud Prevention
- https://www.cms.gov/medicare/fraud-abuse
- NHCAA: ~$68B lost annually to healthcare fraud

### AWS QuickSight Guides
- QuickSight User Guide: https://docs.aws.amazon.com/quicksight/
- Video Tutorials: Search "AWS QuickSight Tutorial"

### FWA Detection Best Practices
- OIG Audit Findings: https://oig.hhs.gov/
- AHLA Compliance Resources: https://www.americanbar.org/

---

## ⭐ QUICK WINS

Try these to impress stakeholders:

1. **Show ROI Calculation**
   ```
   FWA Detected: $184,201
   Audit Cost: ~$50K
   ROI: 368% (3.68x return)
   ```

2. **Identify Top Risk Provider**
   - Open dashboard → Scroll to provider table
   - Note provider with highest risk score
   - Show their claim patterns

3. **Demonstrate Trend**
   - Point to monthly trend chart
   - "FWA increasing in Q2" or similar insight

4. **Geographic Pattern**
   - Show state heat map
   - "TX and FL have higher FWA rates"

---

## 🆘 SUPPORT

**Documentation:**
- `FWA_DATASET_README.md` - Complete guide
- `FWA_GENERATOR_SUMMARY.md` - Technical details

**Code:**
- All scripts have extensive comments
- Run with `--help` for options

**Questions?**
- Check the README files first
- Review code comments
- Test with sample data first

---

## ✅ CHECKLIST

Before presenting/uploading:

- [x] Data generated (5,000 records)
- [x] Dashboard created (fwa_dashboard.html)
- [ ] Dashboard reviewed in browser
- [ ] AWS credentials configured (if using QuickSight)
- [ ] Data uploaded to S3/QuickSight
- [ ] QuickSight analysis created
- [ ] Visualizations built
- [ ] Dashboard shared with team

---

**Created**: 2026-02-09  
**Version**: 1.0  
**Status**: ✅ Ready for Analysis

🎉 **You're all set! Start with the local dashboard, then move to QuickSight when ready.**
