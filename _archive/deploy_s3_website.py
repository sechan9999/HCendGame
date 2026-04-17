"""
🌐 S3 Static Website로 FWA 대시보드 배포하기
QuickSight 대신 완전 무료로 대시보드 호스팅!
"""

import boto3
import json
from botocore.exceptions import ClientError

BUCKET_NAME = "fwa-detection-demo"  # 이미 생성된 버킷
REGION = "us-east-1"

def configure_static_website():
    """S3 버킷을 Static Website로 설정"""
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        # Static Website Hosting 활성화
        website_configuration = {
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'},
        }
        
        s3.put_bucket_website(
            Bucket=BUCKET_NAME,
            WebsiteConfiguration=website_configuration
        )
        
        print(f"✅ Static Website Hosting 활성화됨")
        
        # Public Access 설정
        public_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
                }
            ]
        }
        
        s3.put_bucket_policy(
            Bucket=BUCKET_NAME,
            Policy=json.dumps(public_policy)
        )
        
        print(f"✅ Public Access 정책 설정됨")
        
        # Public Access Block 해제
        s3.delete_public_access_block(Bucket=BUCKET_NAME)
        print(f"✅ Public Access Block 해제됨")
        
        return True
        
    except ClientError as e:
        print(f"❌ 오류: {e}")
        return False

def upload_dashboard():
    """대시보드 HTML 파일 업로드"""
    s3 = boto3.client('s3', region_name=REGION)
    
    files_to_upload = [
        ('fwa_dashboard.html', 'index.html', 'text/html'),
        ('insurance_fwa_data.csv', 'data/insurance_fwa_data.csv', 'text/csv'),
    ]
    
    for local_file, s3_key, content_type in files_to_upload:
        try:
            s3.upload_file(
                local_file,
                BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'max-age=3600'
                }
            )
            print(f"✅ 업로드: {local_file} → s3://{BUCKET_NAME}/{s3_key}")
        except Exception as e:
            print(f"⚠️  {local_file} 업로드 실패: {e}")

def get_website_url():
    """Website URL 반환"""
    if REGION == 'us-east-1':
        url = f"http://{BUCKET_NAME}.s3-website-{REGION}.amazonaws.com"
    else:
        url = f"http://{BUCKET_NAME}.s3-website.{REGION}.amazonaws.com"
    
    return url

def main():
    print("="*60)
    print("🌐 S3 STATIC WEBSITE 배포")
    print("="*60)
    
    # 1. Static Website 설정
    print("\n📝 Step 1: Static Website 설정 중...")
    if configure_static_website():
        print("✅ 설정 완료!")
    
    # 2. 파일 업로드
    print("\n📤 Step 2: 파일 업로드 중...")
    upload_dashboard()
    
    # 3. URL 출력
    website_url = get_website_url()
    
    print("\n" + "="*60)
    print("🎉 배포 완료!")
    print("="*60)
    print(f"\n🌐 대시보드 URL:")
    print(f"   {website_url}")
    print("\n📱 이 URL을 누구에게나 공유할 수 있습니다!")
    print("\n💡 팁:")
    print("   - 완전 무료 (S3 비용만)")
    print("   - 퍼블릭 접근 가능")
    print("   - 빠른 로딩 속도")
    print("   - QuickSight 불필요!")
    
    print("\n📋 다음 단계:")
    print("   1. 위 URL을 브라우저에서 열기")
    print("   2. GitHub README에 링크 추가")
    print("   3. 포트폴리오에 추가")
    print("   4. 이력서에 링크 포함")
    
    print("\n🔒 주의:")
    print("   - 이 대시보드는 PUBLIC입니다")
    print("   - 누구나 접근 가능합니다")
    print("   - 민감한 데이터는 제외하세요")

if __name__ == "__main__":
    main()
