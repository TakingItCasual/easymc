"""various functions that directly interact with AWS"""

import json
import boto3

from ec2mc import config
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

def get_regions(region_filter=None):
    """return list of EC2 regions, or region_filter if not empty and valid"""
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
        quit_out.err(["Invalid region(s) specified."])
    return region_list


def ec2_client(region=config.DEFAULT_REGION):
    """create and return an EC2 client using IAM credentials and a region"""
    return boto3.client("ec2",
        aws_access_key_id=config.IAM_ID,
        aws_secret_access_key=config.IAM_SECRET,
        region_name=region
    )

def iam_client():
    """create and return an IAM client using IAM credentials"""
    return boto3.client("iam",
        aws_access_key_id=config.IAM_ID,
        aws_secret_access_key=config.IAM_SECRET
    )

def ssm_client():
    """create and return an SSM client using IAM credentials"""
    return boto3.client("ssm",
        aws_access_key_id=config.IAM_ID,
        aws_secret_access_key=config.IAM_SECRET
    )


def decode_error_msg(error_response):
    """decode AWS encoded error messages (why are they encoded though?)"""
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
