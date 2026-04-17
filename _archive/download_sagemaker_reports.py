"""
📥 Download SageMaker FWA Analysis Reports
Downloads all reports from S3 to local sagemaker_reports/ folder
"""

import boto3
import os
from botocore.exceptions import ClientError

BUCKET = 'amazon-sagemaker-411471605920-us-east-2-6ifag4k7vfg8bt'
PREFIX = 'shared/fwa_analysis_reports_20260210_021221/'
LOCAL_DIR = 'sagemaker_reports'

def download_sagemaker_reports():
    """Download all SageMaker reports from S3"""
    
    print("=" * 60)
    print("📥 DOWNLOADING SAGEMAKER REPORTS")
    print("=" * 60)
    
    try:
        # Initialize S3 client
        s3 = boto3.client('s3', region_name='us-east-2')
        
        # Test credentials
        print("\n🔐 Testing AWS credentials...")
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Connected as: {identity['Arn']}")
        
        # Create local directory
        os.makedirs(LOCAL_DIR, exist_ok=True)
        print(f"\n📂 Created directory: {LOCAL_DIR}/")
        
        # List objects
        print(f"\n📋 Listing files in S3...")
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET, Prefix=PREFIX)
        
        file_count = 0
        total_size = 0
        
        for page in pages:
            for obj in page.get('Contents', []):
                # Skip folders
                if obj['Key'].endswith('/'):
                    continue
                
                file_name = obj['Key']
                file_size = obj['Size']
                
                # Create local path
                local_name = file_name.replace(PREFIX, '')
                local_path = os.path.join(LOCAL_DIR, local_name)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download file
                print(f"\n📥 Downloading: {local_name} ({file_size:,} bytes)")
                s3.download_file(BUCKET, file_name, local_path)
                print(f"   ✅ Saved to: {local_path}")
                
                file_count += 1
                total_size += file_size
        
        print("\n" + "=" * 60)
        print("✅ DOWNLOAD COMPLETE!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   Files downloaded: {file_count}")
        print(f"   Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        print(f"   Location: ./{LOCAL_DIR}/")
        
        print("\n📋 Next steps:")
        print("   1. Review downloaded files")
        print("   2. Run: python analyze_sagemaker_results.py")
        print("   3. Add to Git: git add sagemaker_reports/")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'InvalidAccessKeyId':
            print("\n❌ ERROR: Invalid AWS credentials")
            print("\n🔧 Fix:")
            print("   1. Run: aws configure")
            print("   2. Enter valid Access Key and Secret Key")
            print("   3. Try again")
        
        elif error_code == 'NoSuchBucket':
            print(f"\n❌ ERROR: Bucket not found: {BUCKET}")
        
        elif error_code == 'AccessDenied':
            print("\n❌ ERROR: Access denied")
            print("   Your credentials don't have permission to access this bucket")
        
        else:
            print(f"\n❌ ERROR: {e}")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = download_sagemaker_reports()
    
    if not success:
        print("\n💡 Alternative: Download via AWS Console")
        print(f"   URL: https://s3.console.aws.amazon.com/s3/buckets/{BUCKET}")
        exit(1)
