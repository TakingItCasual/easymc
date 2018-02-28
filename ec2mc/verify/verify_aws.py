import json
import boto3

from ec2mc import config
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

def main():
    """if AWS account isn't fully set up, set up what is needed

    Before EC2 instances can be created and used with this script, IAM groups, 
    IAM users, IAM group permissions, and EC2 security groups must be 
    intialized.
    """
    
    pass


def security_group(region):
    """verify that AWS has the security group aws_setup_files.security_group

    Args:
        region (str): EC2 region to check/create security group in

    Returns:
        str: ID for security group used for Minecraft instances
    """

    quit_out.assert_empty(simulate_policy.blocked(actions=[
        "ec2:DescribeSecurityGroups"
    ]))

    client = ec2_client(region)
    security_groups = client.describe_security_groups()["SecurityGroups"]
    security_group = [SG for SG in security_groups 
        if config.SECURITY_GROUP_FILTER.lower() in SG["GroupName"].lower()]

    if not security_group:
        pass
    elif len(security_group) > 1:
        quit_out.q(["Error: Multiple security groups matching filter found."])

    return security_group[0]["GroupId"]


def get_regions(region_filter=None):
    """returns list of EC2 regions, or region_filter if not empty and valid"""
    quit_out.assert_empty(simulate_policy.blocked(actions=[
        "ec2:DescribeRegions"
    ]))

    region_list = []
    for region in ec2_client().describe_regions()["Regions"]:
        region_list.append(region["RegionName"])

    # The returned list cannot be empty, so the filter must be valid.
    if region_filter:
        if set(region_filter).issubset(set(region_list)):
            return list(set(region_filter))
        quit_out.q(["Error: Invalid region(s) specified."])
    return region_list


def get_all_keys():
    """get instance tags from all instances in all regions"""
    pass


def ec2_client(region=config.DEFAULT_REGION):
    """create and return an EC2 client with IAM credentials and region"""
    return boto3.client("ec2", 
        aws_access_key_id=config.IAM_ID, 
        aws_secret_access_key=config.IAM_SECRET, 
        region_name=region
    )

def iam_client():
    """create and return an IAM client with IAM credentials"""
    return boto3.client("iam", 
        aws_access_key_id=config.IAM_ID, 
        aws_secret_access_key=config.IAM_SECRET
    )

def ssm_client():
    """create and return an SSM client with IAM credentials"""
    return boto3.client("ssm", 
        aws_access_key_id=config.IAM_ID, 
        aws_secret_access_key=config.IAM_SECRET
    )

def decode_error_msg(error_response):
    """decodes AWS encoded error messages (why are they encoded though?)"""
    encoded_message_indication = "Encoded authorization failure message: "

    if encoded_message_indication not in error_response["Error"]["Message"]:
        return {
            "Warning": "Error message wasn't encoded.", 
            "ErrorMessage": error_response["Error"]["Message"]
        }

    quit_out.assert_empty(simulate_policy.blocked(actions=[
        "sts:DecodeAuthorizationMessage"
    ]))

    encoded_error_str = error_response["Error"]["Message"].split(
        encoded_message_indication,1)[1]

    return json.loads(boto3.client("sts", 
        aws_access_key_id=config.IAM_ID, 
        aws_secret_access_key=config.IAM_SECRET
    ).decode_authorization_message(
        EncodedMessage=encoded_error_str
    )["DecodedMessage"])
