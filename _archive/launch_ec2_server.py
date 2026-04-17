import boto3
import os
import time
import sys

# Configuration
REGION = "us-east-2"
INSTANCE_TYPE = "t3.micro"
AMI_ID = "resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64" # Latest Amazon Linux 2023
KEY_NAME = "RxHCC-Key-Pair"
SECURITY_GROUP_NAME = "RxHCC-Security-Group"

ec2 = boto3.client("ec2", region_name=REGION)

def create_key_pair():
    """Creates a Key Pair and saves it to a .pem file."""
    try:
        key_pair = ec2.create_key_pair(KeyName=KEY_NAME)
        private_key = key_pair["KeyMaterial"]
        
        with open(f"{KEY_NAME}.pem", "w") as f:
            f.write(private_key)
        
        print(f"✅ Key Pair created: {KEY_NAME}.pem")
        os.chmod(f"{KEY_NAME}.pem", 0o400) # Secure permissions (Linux/Mac only, but good practice)
    except ec2.exceptions.ClientError as e:
        if "InvalidKeyPair.Duplicate" in str(e):
            print(f"ℹ️ Key Pair '{KEY_NAME}' already exists. Using existing one.")
        else:
            raise e

def create_security_group():
    """Creates a Security Group allowing SSH (22) and Streamlit (8501)."""
    try:
        # Check if exists
        response = ec2.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
        sg_id = response["SecurityGroups"][0]["GroupId"]
        print(f"ℹ️ Security Group '{SECURITY_GROUP_NAME}' already exists ({sg_id}).")
        return sg_id
    except ec2.exceptions.ClientError as e:
        if "InvalidGroup.NotFound" not in str(e):
            raise e

    # Create new
    vpc_response = ec2.describe_vpcs()
    vpc_id = vpc_response["Vpcs"][0]["VpcId"]
    
    sg = ec2.create_security_group(
        GroupName=SECURITY_GROUP_NAME,
        Description="Allow SSH and Streamlit",
        VpcId=vpc_id
    )
    sg_id = sg["GroupId"]
    
    # Add rules
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            # SSH
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            # Streamlit
            {
                'IpProtocol': 'tcp',
                'FromPort': 8501,
                'ToPort': 8501,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print(f"✅ Security Group created: {SECURITY_GROUP_NAME} ({sg_id})")
    return sg_id

def launch_instance(sg_id):
    """Launches the EC2 instance."""
    print(f"🚀 Launching EC2 Instance ({INSTANCE_TYPE})...")
    
    instances = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[sg_id],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'RxHCC-Server'}]
        }]
    )
    
    instance_id = instances["Instances"][0]["InstanceId"]
    print(f"⏳ Instance {instance_id} is starting... waiting for IP address...")
    
    # Wait for running state
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # Get Public IP
    desc = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = desc["Reservations"][0]["Instances"][0].get("PublicIpAddress")
    
    print(f"\n🎉 Server is UP and RUNNING!")
    print(f"ID: {instance_id}")
    print(f"Public IP: {public_ip}")
    
    return public_ip

if __name__ == "__main__":
    try:
        create_key_pair()
        sg_id = create_security_group()
        ip = launch_instance(sg_id)
        
        print("\n" + "="*50)
        print("CONNECT TO YOUR SERVER:")
        print("="*50)
        print(f"ssh -i \"{KEY_NAME}.pem\" ec2-user@{ip}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
