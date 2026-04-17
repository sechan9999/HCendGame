import boto3
import time
import os

# Configuration
REGION = "us-east-2"
KEY_NAME = "RxHCC-Key-Pair"
SECURITY_GROUP_NAME = "RxHCC-Security-Group"
INSTANCE_TAG_KEY = "Name"
INSTANCE_TAG_VALUE = "RxHCC-Server"

ec2 = boto3.client("ec2", region_name=REGION)

def terminate_instance():
    """Finds and terminates the RxHCC-Server instance."""
    print("🔍 Searching for running instances...")
    
    # Find instance by tag
    response = ec2.describe_instances(
        Filters=[
            {'Name': f'tag:{INSTANCE_TAG_KEY}', 'Values': [INSTANCE_TAG_VALUE]},
            {'Name': 'instance-state-name', 'Values': ['running', 'pending', 'stopped']}
        ]
    )
    
    instance_ids = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_ids.append(instance["InstanceId"])
            
    if not instance_ids:
        print("ℹ️ No active instances found.")
        return

    print(f"🛑 Terminating instances: {instance_ids}...")
    ec2.terminate_instances(InstanceIds=instance_ids)
    
    # Wait for termination
    print("⏳ Waiting for instances to terminate...")
    waiter = ec2.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=instance_ids)
    print("✅ Instances terminated successfully.")

def delete_security_group():
    """Deletes the security group."""
    print(f"🗑️ Deleting Security Group: {SECURITY_GROUP_NAME}...")
    try:
        # Get Group ID first
        response = ec2.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
        if not response["SecurityGroups"]:
            print("ℹ️ Security Group not found.")
            return

        sg_id = response["SecurityGroups"][0]["GroupId"]
        
        # Security Group deletion might fail if instance is not fully terminated yet
        # Retry logic
        for i in range(5):
            try:
                ec2.delete_security_group(GroupId=sg_id)
                print("✅ Security Group deleted.")
                return
            except ec2.exceptions.ClientError as e:
                if "DependencyViolation" in str(e):
                    print("⏳ Waiting for dependencies to clear (retrying in 5s)...")
                    time.sleep(5)
                else:
                    raise e
                    
    except ec2.exceptions.ClientError as e:
        if "InvalidGroup.NotFound" in str(e):
            print("ℹ️ Security Group not found.")
        else:
            print(f"❌ Error deleting Security Group: {e}")

def delete_key_pair():
    """Deletes the key pair from AWS and local file."""
    print(f"🗑️ Deleting Key Pair: {KEY_NAME}...")
    try:
        ec2.delete_key_pair(KeyName=KEY_NAME)
        print("✅ AWS Key Pair deleted.")
    except Exception as e:
        print(f"❌ Error deleting AWS Key Pair: {e}")
        
    # Delete local .pem file
    pem_file = f"{KEY_NAME}.pem"
    if os.path.exists(pem_file):
        try:
            os.remove(pem_file)
            print(f"✅ Local key file '{pem_file}' deleted.")
        except Exception as e:
            print(f"❌ Error deleting local file: {e}")
    else:
        print(f"ℹ️ Local key file '{pem_file}' not found.")

if __name__ == "__main__":
    try:
        terminate_instance()
        delete_security_group()
        delete_key_pair()
        print("\n🎉 Cleanup Complete! No charges will occur.")
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
