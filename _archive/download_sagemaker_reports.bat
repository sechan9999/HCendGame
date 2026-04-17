@echo off
echo ============================================
echo AWS Credentials Setup for SageMaker Reports
echo ============================================
echo.
echo Please provide your AWS credentials:
echo.

aws configure set aws_access_key_id YOUR_ACCESS_KEY_HERE
aws configure set aws_secret_access_key YOUR_SECRET_KEY_HERE
aws configure set default.region us-east-2
aws configure set default.output json

echo.
echo ============================================
echo Testing AWS Connection...
echo ============================================
aws sts get-caller-identity

echo.
echo ============================================
echo Downloading SageMaker Reports...
echo ============================================
mkdir sagemaker_reports 2>nul
aws s3 cp s3://amazon-sagemaker-411471605920-us-east-2-6ifag4k7vfg8bt/shared/fwa_analysis_reports_20260210_021221/ ./sagemaker_reports/ --recursive

echo.
echo ============================================
echo Download Complete!
echo ============================================
echo Check sagemaker_reports/ folder for files
pause
