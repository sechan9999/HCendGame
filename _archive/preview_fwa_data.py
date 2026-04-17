"""
📊 Quick Data Preview & Validation
Preview generated FWA data before uploading to QuickSight
"""

import pandas as pd
import sys

def preview_fwa_data(filepath='insurance_fwa_data.csv'):
    """Display comprehensive preview of FWA dataset."""
    
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"❌ Error: File '{filepath}' not found.")
        print("Run: python engine/fwa_data_generator.py first")
        return
    
    print("=" * 80)
    print("📊 FWA DATASET PREVIEW")
    print("=" * 80)
    
    # 1. Basic Info
    print(f"\n📁 Dataset: {filepath}")
    print(f"📝 Total Records: {len(df):,}")
    print(f"🗂️  Total Columns: {len(df.columns)}")
    print(f"💾 File Size: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    # 2. Column Summary
    print("\n" + "=" * 80)
    print("📋 COLUMN SUMMARY")
    print("=" * 80)
    df.info()
    
    # 3. FWA Statistics
    print("\n" + "=" * 80)
    print("🚨 FWA DETECTION SUMMARY")
    print("=" * 80)
    
    total_claims = len(df)
    fwa_claims = df['is_fwa'].sum()
    clean_claims = total_claims - fwa_claims
    
    print(f"✅ Clean Claims:     {clean_claims:5,} ({clean_claims/total_claims*100:5.2f}%)")
    print(f"🚨 FWA Claims:       {fwa_claims:5,} ({fwa_claims/total_claims*100:5.2f}%)")
    
    print("\n📊 FWA Type Breakdown:")
    fwa_dist = df['fwa_type'].value_counts()
    for fwa_type, count in fwa_dist.head(15).items():
        pct = (count / total_claims) * 100
        bar = "█" * int(pct * 2)
        print(f"  {fwa_type:25s}: {count:4,} ({pct:5.2f}%) {bar}")
    
    # 4. Financial Impact
    print("\n" + "=" * 80)
    print("💰 FINANCIAL IMPACT ANALYSIS")
    print("=" * 80)
    
    total_amount = df['claim_amount'].sum()
    fwa_amount = df[df['is_fwa'] == 1]['claim_amount'].sum()
    avg_claim = df['claim_amount'].mean()
    avg_fwa = df[df['is_fwa'] == 1]['claim_amount'].mean()
    
    print(f"Total Claim Amount:    ${total_amount:15,.2f}")
    print(f"FWA Claim Amount:      ${fwa_amount:15,.2f} ({fwa_amount/total_amount*100:.2f}%)")
    print(f"Clean Claim Amount:    ${total_amount - fwa_amount:15,.2f}")
    print(f"\nAvg Claim Amount:      ${avg_claim:15,.2f}")
    print(f"Avg FWA Claim Amount:  ${avg_fwa:15,.2f}")
    print(f"FWA Premium:           ${avg_fwa - avg_claim:15,.2f} (+{(avg_fwa/avg_claim - 1)*100:.1f}%)")
    
    # 5. Risk Score Distribution
    print("\n" + "=" * 80)
    print("⚠️  RISK SCORE DISTRIBUTION")
    print("=" * 80)
    
    risk_dist = df['risk_category'].value_counts().sort_index()
    for category, count in risk_dist.items():
        pct = (count / total_claims) * 100
        print(f"  {category:10s}: {count:4,} ({pct:5.2f}%)")
    
    print(f"\nAvg Risk Score:        {df['fwa_risk_score'].mean():.3f}")
    print(f"Max Risk Score:        {df['fwa_risk_score'].max():.3f}")
    print(f"High Risk (>0.7):      {(df['fwa_risk_score'] > 0.7).sum():,}")
    
    # 6. Geographic Distribution
    print("\n" + "=" * 80)
    print("🗺️  GEOGRAPHIC DISTRIBUTION")
    print("=" * 80)
    
    state_fwa = df.groupby('state').agg({
        'claim_id': 'count',
        'is_fwa': 'sum',
        'claim_amount': 'sum'
    }).sort_values('is_fwa', ascending=False)
    
    state_fwa.columns = ['Total Claims', 'FWA Claims', 'Total Amount']
    state_fwa['FWA Rate %'] = (state_fwa['FWA Claims'] / state_fwa['Total Claims'] * 100).round(2)
    print(state_fwa.head(10).to_string())
    
    # 7. Provider Analysis
    print("\n" + "=" * 80)
    print("👨‍⚕️ TOP 10 HIGH-RISK PROVIDERS")
    print("=" * 80)
    
    provider_analysis = df.groupby(['provider_id', 'specialty']).agg({
        'claim_id': 'count',
        'is_fwa': 'sum',
        'fwa_risk_score': 'mean',
        'claim_amount': 'sum'
    }).sort_values('fwa_risk_score', ascending=False).head(10)
    
    provider_analysis.columns = ['Claims', 'FWA Count', 'Avg Risk', 'Total $']
    print(provider_analysis.to_string())
    
    # 8. Temporal Analysis
    print("\n" + "=" * 80)
    print("📅 TEMPORAL PATTERNS")
    print("=" * 80)
    
    monthly = df.groupby('year_month').agg({
        'claim_id': 'count',
        'is_fwa': 'sum'
    }).head(12)
    monthly.columns = ['Claims', 'FWA']
    monthly['FWA %'] = (monthly['FWA'] / monthly['Claims'] * 100).round(1)
    print(monthly.to_string())
    
    # 9. Sample High-Risk Claims
    print("\n" + "=" * 80)
    print("🔍 SAMPLE HIGH-RISK CLAIMS (Top 5)")
    print("=" * 80)
    
    high_risk = df[df['fwa_risk_score'] > 0.85].nlargest(5, 'fwa_risk_score')[
        ['claim_id', 'provider_id', 'fwa_type', 'fwa_risk_score', 'claim_amount', 'fwa_explanation']
    ]
    
    for idx, row in high_risk.iterrows():
        print(f"\n🚨 {row['claim_id']} | Risk: {row['fwa_risk_score']:.3f} | ${row['claim_amount']:.2f}")
        print(f"   Provider: {row['provider_id']} | Type: {row['fwa_type']}")
        print(f"   ➜ {row['fwa_explanation']}")
    
    # 10. Data Quality Checks
    print("\n" + "=" * 80)
    print("✅ DATA QUALITY CHECKS")
    print("=" * 80)
    
    null_counts = df.isnull().sum()
    print(f"Null Values:           {null_counts.sum()} (in {(null_counts > 0).sum()} columns)")
    print(f"Duplicate Claims:      {df['claim_id'].duplicated().sum()}")
    print(f"Invalid Risk Scores:   {((df['fwa_risk_score'] < 0) | (df['fwa_risk_score'] > 1)).sum()}")
    print(f"Invalid Amounts:       {(df['claim_amount'] <= 0).sum()}")
    print(f"Date Range:            {df['service_date'].min()} to {df['service_date'].max()}")
    
    print("\n" + "=" * 80)
    print("✅ DATASET VALIDATION COMPLETE")
    print("=" * 80)
    print("\n🚀 Ready for AWS QuickSight upload!")
    print("📖 See FWA_DATASET_README.md for QuickSight setup instructions")
    
    # Optional: Export summary
    summary_file = filepath.replace('.csv', '_summary.txt')
    print(f"\n💾 Exporting summary to: {summary_file}")


if __name__ == "__main__":
    file_path = 'insurance_fwa_data.csv'
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    preview_fwa_data(file_path)
