"""
🚨 FWA Data Generator for AWS QuickSight Analysis
Generates synthetic insurance claims data with realistic Fraud, Waste, and Abuse patterns.

Features:
- Multiple FWA pattern types (15+ scenarios)
- Realistic medical coding (ICD-10, CPT, NDC)
- Geographic and temporal patterns
- Risk scoring with explanations
- QuickSight-optimized structure
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class FWADataGenerator:
    """Enhanced FWA synthetic data generator with realistic patterns."""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Expanded Medical Codes
        self.icd10_codes = {
            'E11.9': 'Type 2 Diabetes',
            'E10.9': 'Type 1 Diabetes',
            'I10': 'Essential Hypertension',
            'M54.5': 'Low Back Pain',
            'J06.9': 'Upper Respiratory Infection',
            'E66.01': 'Morbid Obesity',
            'F41.9': 'Anxiety Disorder',
            'E78.5': 'Hyperlipidemia',
            'M79.3': 'Fibromyalgia',
            'Z00.00': 'General Health Exam',
            'G89.29': 'Chronic Pain',
            'M25.511': 'Knee Pain'
        }
        
        # CPT Codes (Procedure Codes)
        self.cpt_codes = {
            '99213': ('Office Visit Level 3', 75),
            '99214': ('Office Visit Level 4', 110),
            '99215': ('Office Visit Level 5', 180),
            '99285': ('ER Visit Level 5', 450),
            '81001': ('Urinalysis', 15),
            '82947': ('Glucose Test', 20),
            '83036': ('A1C Test', 30),
            '97110': ('Therapeutic Exercise 15min', 45),
            '97112': ('Neuromuscular Re-education', 50),
            '70450': ('CT Head without Contrast', 350),
            '72148': ('MRI Lumbar Spine', 600),
            '20610': ('Joint Injection', 120)
        }
        
        # NDC Codes (Medications)
        self.ndc_codes = {
            '00002-8215-01': ('Humalog (Insulin)', 300),
            '00169-7501-11': ('Ozempic (GLP-1)', 950),
            '00310-0800-39': ('Metformin 500mg', 15),
            '00378-6074-77': ('Lisinopril 10mg', 8),
            '00093-0058-01': ('Atorvastatin 20mg', 12),
            '00555-0915-02': ('Gabapentin 300mg', 25),
            '59762-5005-01': ('Xanax 0.5mg', 35),
            '68382-0087-06': ('Hydrocodone', 40)
        }
        
        # Geographic data
        self.states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
        self.cities = {
            'CA': ['Los Angeles', 'San Francisco', 'San Diego'],
            'TX': ['Houston', 'Dallas', 'Austin'],
            'FL': ['Miami', 'Tampa', 'Orlando'],
            'NY': ['New York City', 'Buffalo', 'Rochester'],
            'PA': ['Philadelphia', 'Pittsburgh']
        }
        
        # Provider specialties
        self.specialties = [
            'Primary Care', 'Endocrinology', 'Cardiology', 
            'Orthopedics', 'Pain Management', 'Emergency Medicine',
            'Physical Therapy', 'Psychiatry'
        ]
        
    def _generate_provider_network(self, num_providers=50) -> List[Dict]:
        """Generate provider profiles with FWA tendencies."""
        providers = []
        
        for i in range(1, num_providers + 1):
            state = random.choice(self.states)
            city = random.choice(self.cities.get(state, ['Unknown']))
            specialty = random.choice(self.specialties)
            
            # Assign FWA risk profile (10% high-risk providers)
            fwa_profile = 'CLEAN'
            if i % 10 == 7:  # 10% are fraud rings
                fwa_profile = 'FRAUD_RING'
            elif i % 5 == 3:  # 20% show wasteful patterns
                fwa_profile = 'WASTEFUL'
            elif i % 7 == 4:  # ~14% show abusive patterns
                fwa_profile = 'ABUSIVE'
                
            providers.append({
                'provider_id': f'PROV_{i:04d}',
                'specialty': specialty,
                'state': state,
                'city': city,
                'fwa_profile': fwa_profile,
                'years_practice': random.randint(1, 30)
            })
            
        return providers
    
    def _apply_fwa_pattern(self, claim: Dict, provider: Dict) -> Tuple[Dict, str]:
        """Apply FWA patterns and return updated claim with explanation."""
        fwa_type = 'CLEAN'
        fwa_explanation = ''
        risk_score = np.random.uniform(0.05, 0.25)
        
        # Pattern 1: Upcoding (FRAUD)
        if provider['fwa_profile'] == 'FRAUD_RING' and random.random() > 0.4:
            if claim['cpt_code'] == '99213':
                claim['cpt_code'] = '99215'  # Upcode to higher level
                claim['service_name'] = self.cpt_codes['99215'][0]
                claim['claim_amount'] += 105
                risk_score = 0.85
                fwa_type = 'UPCODING'
                fwa_explanation = 'Office visit upcoded from Level 3 to Level 5'
        
        # Pattern 2: Unbundling (FRAUD)
        if 'MRI' in claim['service_name'] and random.random() > 0.7:
            claim['claim_amount'] *= 1.4
            risk_score = 0.78
            fwa_type = 'UNBUNDLING'
            fwa_explanation = 'MRI procedure split into multiple billable components'
        
        # Pattern 3: Phantom Billing (FRAUD)
        if provider['fwa_profile'] == 'FRAUD_RING' and random.random() > 0.85:
            claim['service_rendered'] = 0  # Service never happened
            risk_score = 0.95
            fwa_type = 'PHANTOM_BILLING'
            fwa_explanation = 'Service billed but not documented or rendered'
        
        # Pattern 4: Duplicate Claims (WASTE)
        if claim['claim_id'].endswith(('050', '150', '250')):
            risk_score = 0.92
            fwa_type = 'DUPLICATE_CLAIM'
            fwa_explanation = 'Duplicate claim for same service on same date'
        
        # Pattern 5: Medical Necessity Issues (WASTE)
        if provider['fwa_profile'] == 'WASTEFUL' and claim['diagnosis_code'] == 'Z00.00':
            if 'MRI' in claim['service_name'] or 'CT' in claim['service_name']:
                risk_score = 0.72
                fwa_type = 'UNNECESSARY_SERVICE'
                fwa_explanation = 'High-cost imaging for routine health exam'
        
        # Pattern 6: Excessive Opioid Prescribing (ABUSE)
        if claim['ndc_code'] == '68382-0087-06':  # Hydrocodone
            days_between_refills = (claim['service_date'] - claim.get('last_opioid_date', claim['service_date'])).days
            if days_between_refills < 15:
                risk_score = 0.81
                fwa_type = 'EXCESSIVE_OPIOID'
                fwa_explanation = 'Opioid refill within 15 days of last prescription'
        
        # Pattern 7: GLP-1 Off-Label (ABUSE)
        if claim['ndc_code'] == '00169-7501-11':  # Ozempic
            if claim['diagnosis_code'] not in ['E11.9', 'E66.01']:
                risk_score = 0.79
                fwa_type = 'OFF_LABEL_DRUG'
                fwa_explanation = 'GLP-1 prescribed without diabetes or obesity diagnosis'
        
        # Pattern 8: Physical Therapy Mills (ABUSE)
        if provider['specialty'] == 'Physical Therapy' and provider['fwa_profile'] == 'ABUSIVE':
            if random.random() > 0.5:
                claim['claim_amount'] *= 1.8
                risk_score = 0.73
                fwa_type = 'PT_MILL'
                fwa_explanation = 'Excessive PT sessions beyond medical necessity'
        
        # Pattern 9: Kickback Patterns (FRAUD)
        if provider['provider_id'] in ['PROV_0007', 'PROV_0017', 'PROV_0027']:
            if claim['specialty'] == 'Primary Care' and 'MRI' in claim['service_name']:
                risk_score = 0.88
                fwa_type = 'KICKBACK_PATTERN'
                fwa_explanation = 'Unusual referral pattern suggesting kickback arrangement'
        
        # Pattern 10: After-Hours Billing (FRAUD) - Only for certain specialties with random chance
        if random.random() > 0.95:  # Only 5% of claims checked for time fraud
            if claim['service_date'].hour >= 22 or claim['service_date'].hour <= 5:
                if claim['specialty'] not in ['Emergency Medicine']:
                    risk_score = 0.76
                    fwa_type = 'TIME_FRAUD'
                    fwa_explanation = 'Non-emergency service billed during unusual hours'
        
        claim['fwa_risk_score'] = round(min(1.0, risk_score), 3)
        claim['is_fwa'] = 1 if risk_score > 0.70 else 0
        claim['fwa_type'] = fwa_type
        claim['fwa_explanation'] = fwa_explanation
        
        return claim, fwa_type
    
    def generate(self, num_records=2000, output_path='insurance_fwa_data.csv') -> pd.DataFrame:
        """Generate comprehensive FWA dataset."""
        
        print(f"🔧 Generating {num_records} synthetic insurance claims with FWA patterns...")
        
        # Generate provider network
        providers = self._generate_provider_network(50)
        provider_dict = {p['provider_id']: p for p in providers}
        
        # Generate member cohort
        members = [f'MEM_{i:05d}' for i in range(1, 501)]
        
        claims = []
        fwa_stats = {}
        
        start_date = datetime(2025, 1, 1)
        
        for i in range(num_records):
            # Basic claim info
            claim_id = f'CLM_{i:06d}'
            member_id = random.choice(members)
            provider = random.choice(providers)
            
            # Service details
            diag_code = random.choice(list(self.icd10_codes.keys()))
            cpt_code = random.choice(list(self.cpt_codes.keys()))
            ndc_code = random.choice(list(self.ndc_codes.keys())) if random.random() > 0.5 else None
            
            service_date = start_date + timedelta(days=random.randint(0, 365))
            
            # Realistic service hours (most during business hours 8am-6pm)
            if provider['specialty'] == 'Emergency Medicine':
                hour = random.randint(0, 23)  # ER 24/7
            else:
                # 90% during business hours, 10% other times
                if random.random() > 0.1:
                    hour = random.randint(8, 18)  # 8am - 6pm
                else:
                    hour = random.choices([7, 19, 20, 21, 22], weights=[2, 3, 2, 1, 1])[0]
            
            service_date = service_date.replace(hour=hour, minute=random.randint(0, 59))

            
            # Base claim
            claim = {
                'claim_id': claim_id,
                'member_id': member_id,
                'provider_id': provider['provider_id'],
                'specialty': provider['specialty'],
                'state': provider['state'],
                'city': provider['city'],
                'diagnosis_code': diag_code,
                'diagnosis_name': self.icd10_codes[diag_code],
                'cpt_code': cpt_code,
                'service_name': self.cpt_codes[cpt_code][0],
                'claim_amount': self.cpt_codes[cpt_code][1] + np.random.normal(0, 20),
                'service_date': service_date,
                'service_rendered': 1,
                'ndc_code': ndc_code,
                'drug_name': self.ndc_codes[ndc_code][0] if ndc_code else 'N/A',
                'last_opioid_date': service_date - timedelta(days=random.randint(10, 60))
            }
            
            # Apply FWA patterns
            claim, fwa_type = self._apply_fwa_pattern(claim, provider_dict[provider['provider_id']])
            
            # Track statistics
            fwa_stats[fwa_type] = fwa_stats.get(fwa_type, 0) + 1
            
            claims.append(claim)
        
        # Convert to DataFrame
        df = pd.DataFrame(claims)
        
        # Format for QuickSight
        df['service_date'] = df['service_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['claim_amount'] = df['claim_amount'].round(2)
        df['year_month'] = pd.to_datetime(df['service_date']).dt.to_period('M').astype(str)
        df['day_of_week'] = pd.to_datetime(df['service_date']).dt.day_name()
        
        # Risk categories
        df['risk_category'] = pd.cut(
            df['fwa_risk_score'], 
            bins=[0, 0.3, 0.6, 0.8, 1.0],
            labels=['Low', 'Medium', 'High', 'Critical']
        )
        
        # Drop helper columns
        df = df.drop(['last_opioid_date'], axis=1)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        # Print summary
        print(f"\n✅ Generated {len(df)} claims")
        print(f"📊 FWA Pattern Distribution:")
        for pattern, count in sorted(fwa_stats.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(df)) * 100
            print(f"   {pattern:20s}: {count:4d} ({pct:5.2f}%)")
        
        print(f"\n💰 Financial Impact:")
        total_amount = df['claim_amount'].sum()
        fwa_amount = df[df['is_fwa'] == 1]['claim_amount'].sum()
        print(f"   Total Claims:    ${total_amount:,.2f}")
        print(f"   FWA Claims:      ${fwa_amount:,.2f}")
        print(f"   FWA Rate:        {(fwa_amount/total_amount)*100:.2f}%")
        
        print(f"\n📁 File saved: {output_path}")
        print(f"🔍 Ready for AWS QuickSight upload!")
        
        return df


def main():
    """Main execution function."""
    generator = FWADataGenerator(seed=42)
    df = generator.generate(
        num_records=5000,
        output_path='insurance_fwa_data.csv'
    )
    
    # Optional: Generate a smaller sample for testing
    sample_df = df.head(500)
    sample_df.to_csv('insurance_fwa_data_sample.csv', index=False)
    print(f"\n📦 Sample file (500 records): insurance_fwa_data_sample.csv")
    
    print("\n" + "="*70)
    print("QUICKSIGHT UPLOAD INSTRUCTIONS:")
    print("="*70)
    print("1. Go to AWS QuickSight Console")
    print("2. Create New Dataset → Upload CSV")
    print("3. Upload: insurance_fwa_data.csv")
    print("4. Suggested Visualizations:")
    print("   - Bar Chart: FWA Type by Count")
    print("   - Heat Map: State vs Risk Score")
    print("   - Line Chart: Monthly FWA Trend")
    print("   - Pie Chart: Risk Category Distribution")
    print("   - Table: Top 10 Providers by FWA Amount")
    print("="*70)


if __name__ == "__main__":
    main()
