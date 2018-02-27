import boto3

from ec2mc import config
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

def main():
    """If AWS account isn't fully set up, set up what is needed.

    Before EC2 instances can be created and used with this script, IAM groups, 
    IAM users, IAM group permissions, and EC2 security groups must be 
    intialized.
    """
    
    pass


def security_group(user_info, region):
    """Verify that AWS has the security group aws_setup_files.security_group.

    Args:
        user_info (dict): iam_id and iam_secret are needed.

    Returns:
        str: ID for security group used for Minecraft instances
    """

    client = ec2_client(user_info, region)
    security_groups = client.describe_security_groups()["SecurityGroups"]
    security_group = [SG for SG in security_groups 
        if config.SECURITY_GROUP_FILTER.lower() in SG["GroupName"].lower()]

    if not security_group:
        pass
    elif len(security_group) > 1:
        quit_out.q(["Error: Multiple security groups matching filter found."])

    pp.pprint(security_group)
    quit_out.q(["blah"])

    return ""


def get_regions(user_info, region_filter=None):
    """Returns list of EC2 regions, or region_filter if not empty and valid."""
    quit_out.assert_empty(simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeRegions"
    ]))

    region_list = []
    for region in ec2_client(user_info).describe_regions()["Regions"]:
        region_list.append(region["RegionName"])

    # The returned list cannot be empty, so the filter must be valid.
    if region_filter:
        if set(region_filter).issubset(set(region_list)):
            return list(set(region_filter))
        quit_out.q(["Error: Invalid region(s) specified."])
    return region_list


def ec2_client(user_info, region=config.DEFAULT_REGION):
    """Create and return an EC2 client with IAM credentials and region"""
    return boto3.client("ec2", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"], 
        region_name=region
    )

def iam_client(user_info):
    """Create and return an IAM client with IAM credentials"""
    return boto3.client("iam", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"]
    )

def ssm_client(user_info):
    """Create and return an SSM client with IAM credentials"""
    return boto3.client("ssm", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"]
    )
