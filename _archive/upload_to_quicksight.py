"""
🚀 AWS QuickSight Upload Automation
Uploads FWA dataset to S3 and prepares it for QuickSight analysis.

Features:
- Uploads CSV to S3 bucket
- Creates QuickSight-ready manifest file
- Validates AWS credentials
- Provides step-by-step instructions
"""

import boto3
import json
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError

# Configuration
BUCKET_NAME = "rxhcc-quicksight-data-sechan9999"
REGION = "us-east-2"
CSV_FILE = "insurance_fwa_data.csv"
SAMPLE_FILE = "insurance_fwa_data_sample.csv"

def check_aws_credentials():
    """Verify AWS credentials are configured."""
    try:
        sts = boto3.client('sts', region_name=REGION)
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials Valid")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("\nPlease configure AWS credentials:")
        print("   1. Run: aws configure")
        print("   2. Enter your Access Key ID")
        print("   3. Enter your Secret Access Key")
        print("   4. Region: us-east-2")
        print("   5. Format: json")
        return False
    except ClientError as e:
        print(f"❌ Invalid AWS credentials: {e}")
        print("\nYour credentials may be expired or incorrect.")
        print("Please run: aws configure")
        return False

def create_s3_bucket():
    """Create S3 bucket for QuickSight data if it doesn't exist."""
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        # Check if bucket exists
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' already exists")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # Bucket doesn't exist, create it
            try:
                if REGION == 'us-east-1':
                    s3.create_bucket(Bucket=BUCKET_NAME)
                else:
                    s3.create_bucket(
                        Bucket=BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': REGION}
                    )
                print(f"✅ Created bucket: {BUCKET_NAME}")
                
                # Enable QuickSight access
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "quicksight.amazonaws.com"
                            },
                            "Action": [
                                "s3:GetObject",
                                "s3:GetObjectVersion"
                            ],
                            "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
                        }
                    ]
                }
                
                s3.put_bucket_policy(
                    Bucket=BUCKET_NAME,
                    Policy=json.dumps(bucket_policy)
                )
                print(f"✅ QuickSight access policy applied")
                return True
                
            except ClientError as create_error:
                print(f"❌ Failed to create bucket: {create_error}")
                return False
        else:
            print(f"❌ Error checking bucket: {e}")
            return False

def upload_to_s3(local_file, s3_key):
    """Upload file to S3."""
    s3 = boto3.client('s3', region_name=REGION)
    
    if not os.path.exists(local_file):
        print(f"❌ File not found: {local_file}")
        return False
    
    try:
        file_size = os.path.getsize(local_file) / 1024  # KB
        print(f"⏳ Uploading {local_file} ({file_size:.1f} KB)...")
        
        s3.upload_file(
            local_file,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'text/csv'}
        )
        
        s3_url = f"s3://{BUCKET_NAME}/{s3_key}"
        print(f"✅ Uploaded to: {s3_url}")
        return s3_url
        
    except ClientError as e:
        print(f"❌ Upload failed: {e}")
        return False

def create_manifest_file(s3_csv_url):
    """Create QuickSight manifest file for easier import."""
    manifest = {
        "fileLocations": [
            {
                "URIPrefixes": [
                    s3_csv_url.rsplit('/', 1)[0] + "/"
                ]
            }
        ],
        "globalUploadSettings": {
            "format": "CSV",
            "delimiter": ",",
            "textqualifier": "\"",
            "containsHeader": "true"
        }
    }
    
    manifest_file = "quicksight_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📄 Created manifest file: {manifest_file}")
    
    # Upload manifest to S3
    s3 = boto3.client('s3', region_name=REGION)
    try:
        s3.upload_file(
            manifest_file,
            BUCKET_NAME,
            "manifest/quicksight_manifest.json",
            ExtraArgs={'ContentType': 'application/json'}
        )
        manifest_url = f"s3://{BUCKET_NAME}/manifest/quicksight_manifest.json"
        print(f"✅ Manifest uploaded to: {manifest_url}")
        return manifest_url
    except ClientError as e:
        print(f"⚠️  Could not upload manifest: {e}")
        return None

def generate_quicksight_instructions(csv_url, manifest_url=None):
    """Generate step-by-step QuickSight setup instructions."""
    
    print("\n" + "="*80)
    print("🎯 AWS QUICKSIGHT SETUP INSTRUCTIONS")
    print("="*80)
    
    print("\n📝 STEP 1: Sign up for QuickSight (if not already)")
    print("   1. Go to: https://quicksight.aws.amazon.com/")
    print("   2. Click 'Sign up for QuickSight'")
    print("   3. Choose 'Standard' edition (free trial available)")
    print(f"   4. Select region: {REGION}")
    print("   5. Enable S3 access and select your bucket")
    
    print("\n📂 STEP 2: Create Dataset from S3")
    print("   Option A - Using S3 URL (Recommended):")
    print("   1. In QuickSight, click 'Datasets' → 'New dataset'")
    print("   2. Choose 'S3'")
    print("   3. Data source name: 'FWA_Insurance_Claims'")
    if manifest_url:
        print(f"   4. Upload manifest file OR paste this URL:")
        print(f"      {manifest_url}")
    print(f"   5. Or use CSV URL directly:")
    print(f"      {csv_url}")
    
    print("\n   Option B - Download and Upload:")
    print("   1. Download the CSV from S3")
    print("   2. In QuickSight: 'Datasets' → 'New dataset' → 'Upload a file'")
    print(f"   3. Upload: {CSV_FILE}")
    
    print("\n🔧 STEP 3: Configure Dataset")
    print("   1. Click 'Edit/Preview data'")
    print("   2. Verify column types:")
    print("      - claim_amount: Decimal")
    print("      - fwa_risk_score: Decimal")
    print("      - service_date: DateTime")
    print("      - is_fwa: Integer")
    print("      - state, city, fwa_type: String")
    print("   3. Click 'Save & visualize'")
    
    print("\n📊 STEP 4: Create Analysis")
    print("   1. Name: 'FWA Detection Dashboard'")
    print("   2. Start adding visuals (see suggestions below)")
    
    print("\n💡 SUGGESTED VISUALIZATIONS:")
    print("   📈 Visual 1: KPI Cards")
    print("      - Total Claims Amount (SUM of claim_amount)")
    print("      - FWA Claims Count (SUM of is_fwa)")
    print("      - FWA Rate % (calculated field)")
    print("      - High Risk Count (COUNT where risk_category = 'Critical')")
    
    print("\n   🥧 Visual 2: Pie Chart - FWA Type Distribution")
    print("      - Group by: fwa_type")
    print("      - Value: COUNT(claim_id)")
    
    print("\n   📊 Visual 3: Bar Chart - State Analysis")
    print("      - X-axis: state")
    print("      - Y-axis: SUM(claim_amount)")
    print("      - Color: risk_category")
    
    print("\n   📈 Visual 4: Line Chart - Monthly Trend")
    print("      - X-axis: year_month")
    print("      - Y-axis: COUNT(is_fwa)")
    print("      - Line style: Smooth")
    
    print("\n   🗺️  Visual 5: Heat Map - Provider Risk")
    print("      - Rows: provider_id")
    print("      - Columns: specialty")
    print("      - Values: AVG(fwa_risk_score)")
    
    print("\n   📋 Visual 6: Table - High Risk Claims")
    print("      - Columns: claim_id, provider_id, fwa_type, claim_amount")
    print("      - Filter: fwa_risk_score > 0.8")
    print("      - Sort: fwa_risk_score DESC")
    
    print("\n🧮 CALCULATED FIELDS:")
    print("   Create these in QuickSight for advanced analysis:")
    print("\n   1. FWA Amount:")
    print("      ifelse({is_fwa} = 1, {claim_amount}, 0)")
    print("\n   2. FWA Rate %:")
    print("      sum({is_fwa}) / count({claim_id}) * 100")
    print("\n   3. Risk Tier:")
    print("      ifelse({fwa_risk_score} > 0.8, 'Critical',")
    print("             {fwa_risk_score} > 0.6, 'High',")
    print("             {fwa_risk_score} > 0.3, 'Medium', 'Low')")
    
    print("\n" + "="*80)
    print("📚 ADDITIONAL RESOURCES")
    print("="*80)
    print("   • QuickSight Guide: FWA_DATASET_README.md")
    print("   • Project Summary: FWA_GENERATOR_SUMMARY.md")
    print("   • Data Preview: Run 'python preview_fwa_data.py'")
    
    print("\n" + "="*80)
    print("✨ READY TO ANALYZE!")
    print("="*80)

def main():
    """Main execution flow."""
    print("="*80)
    print("🚀 AWS QUICKSIGHT DATA UPLOAD")
    print("="*80)
    
    # Step 1: Check credentials
    print("\n📋 Step 1: Validating AWS Credentials...")
    if not check_aws_credentials():
        sys.exit(1)
    
    # Step 2: Create S3 bucket
    print(f"\n📦 Step 2: Setting up S3 bucket...")
    if not create_s3_bucket():
        print("\n⚠️  Warning: Could not create/access S3 bucket")
        print("You can still upload manually to QuickSight")
    
    # Step 3: Upload CSV files
    print(f"\n⬆️  Step 3: Uploading data files...")
    
    csv_uploaded = upload_to_s3(CSV_FILE, f"data/{CSV_FILE}")
    if csv_uploaded:
        sample_uploaded = upload_to_s3(SAMPLE_FILE, f"data/{SAMPLE_FILE}")
        
        # Step 4: Create manifest
        print(f"\n📝 Step 4: Creating QuickSight manifest...")
        manifest_url = create_manifest_file(csv_uploaded)
        
        # Step 5: Generate instructions
        print(f"\n✅ Upload Complete!")
        generate_quicksight_instructions(csv_uploaded, manifest_url)
    else:
        print("\n❌ Upload failed. Please check:")
        print("   1. AWS credentials are valid")
        print("   2. You have S3 permissions")
        print("   3. The CSV file exists in current directory")
        print("\n💡 Alternative: Upload directly to QuickSight")
        print("   1. Go to QuickSight console")
        print("   2. Create dataset → Upload file")
        print(f"   3. Select: {CSV_FILE}")

if __name__ == "__main__":
    main()
