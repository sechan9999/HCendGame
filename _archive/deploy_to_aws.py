import boto3
import os
import sys
import logging
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path to import engine
sys.path.append(os.getcwd())

try:
    from engine.sagemaker_replication import SyntheticClaimGenerator
except ImportError:
    logger.error("Could not import engine.sagemaker_replication. Ensure you are running from the project root.")
    sys.exit(1)

BUCKET_NAME = "rxhcc-integrity-check-sechan9999"  # Unique bucket name
REGION = "us-east-2"

def create_bucket():
    """Create S3 bucket if not exists."""
    s3 = boto3.client('s3', region_name=REGION)
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        logger.info(f"Bucket {BUCKET_NAME} created successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            logger.info(f"Bucket {BUCKET_NAME} already exists and is owned by you.")
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            logger.error(f"Bucket {BUCKET_NAME} already exists and is owned by someone else. Change BUCKET_NAME.")
            sys.exit(1)
        else:
            logger.error(f"Error creating bucket: {e}")
            sys.exit(1)

def upload_file(file_name, object_name=None):
    """Upload a file to S3 bucket."""
    if object_name is None:
        object_name = file_name

    s3 = boto3.client('s3', region_name=REGION)
    try:
        s3.upload_file(file_name, BUCKET_NAME, object_name)
        logger.info(f"Uploaded {file_name} to s3://{BUCKET_NAME}/{object_name}")
    except ClientError as e:
        logger.error(f"Failed to upload {file_name}: {e}")

def generate_and_upload_data():
    """Generate sample data and upload to S3."""
    logger.info("Generating synthetic claims data...")
    generator = SyntheticClaimGenerator(seed=42)
    df = generator.generate(n_records=1000, anomaly_rate=0.2)
    
    os.makedirs("data", exist_ok=True)
    local_path = "data/sample_claims.csv"
    df.to_csv(local_path, index=False)
    logger.info(f"Generated {len(df)} records at {local_path}")
    
    upload_file(local_path, "data/input/sample_claims.csv")

def upload_project_code():
    """Upload project code to S3 for SageMaker/EC2 usage."""
    logger.info("Uploading project code...")
    
    # Files to upload
    files = [
        "requirements.txt",
        "README.md"
    ]
    
    # Upload root files
    for f in files:
        if os.path.exists(f):
            upload_file(f, f"code/{f}")
            
    # Upload directories
    for directory in ["app", "engine"]:
        if not os.path.isdir(directory):
            continue
            
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".pyc") or "__pycache__" in root:
                    continue
                local_path = os.path.join(root, filename)
                s3_path = f"code/{local_path.replace(os.path.sep, '/')}"
                upload_file(local_path, s3_path)

def main():
    logger.info("Starting deployment to AWS S3...")
    
    # 1. Create Bucket
    create_bucket()
    
    # 2. Generate and Upload Data
    generate_and_upload_data()
    
    # 3. Upload Code
    upload_project_code()
    
    logger.info("Deployment Complete!")
    print("\n" + "="*50)
    print(f"✅ Project Deployed to s3://{BUCKET_NAME}")
    print("="*50)
    print("Code location: s3://{}/code/".format(BUCKET_NAME))
    print("Data location: s3://{}/data/input/sample_claims.csv".format(BUCKET_NAME))
    print("\nNext Steps:")
    print("1. You can now use SageMaker Processing Job with this S3 input.")
    print("2. Or launch an EC2 instance and download the code from S3 using:")
    print(f"   aws s3 cp s3://{BUCKET_NAME}/code/ . --recursive")

if __name__ == "__main__":
    main()
