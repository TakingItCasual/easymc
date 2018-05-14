"""miscellaneous functions that directly interact with AWS"""

import re
from time import sleep
import json
import boto3
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.stuff import quit_out

def get_regions(region_filter=None):
    """return list of EC2 regions, or region_filter if not empty and valid

    Requires the ec2:DescribeRegions permission.
    """

    region_list = []
    for region in ec2_client().describe_regions()["Regions"]:
        region_list.append(region["RegionName"])

    # The returned list cannot be empty, so the filter must be valid.
    if region_filter:
        if set(region_filter).issubset(set(region_list)):
            return list(set(region_filter))
        quit_out.err(["Following invalid region(s) specified:",
            *set(region_filter).difference(set(region_list))])
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


def get_region_vpc(region):
    """get VPC from region with config's Namespace tag

    Args:
        region (str): AWS region to search from.

    Returns:
        list of dict(s): VPC matching filter
    """

    vpcs = ec2_client(region).describe_vpcs(Filters=[{
        "Name": "tag:Namespace",
        "Values": [config.NAMESPACE]
    }])["Vpcs"]

    if len(vpcs) > 1:
        quit_out.err("Multiple VPCs with Namespace tag " + config.NAMESPACE +
            "found from AWS.")
    return vpcs


def security_group_id(region, sg_name=config.SECURITY_GROUP_FILTER):
    """get ID of security group with correct GroupName from AWS

    Requires the ec2:DescribeSecurityGroups permission.

    Args:
        region (str): EC2 region to search security group from
        sg_name (str): Name of security group

    Returns:
        str: ID for security group used for Minecraft instances
    """

    # TODO: Shift over to the new SG system defined in aws_setup.json

    security_groups = ec2_client(
        region).describe_security_groups()["SecurityGroups"]
    security_group = [SG for SG in security_groups
        if sg_name.lower() in SG["GroupName"].lower()]

    if not security_group:
        quit_out.err(["No security groups matching aws_setup found."])
    elif len(security_group) > 1:
        quit_out.err(["Multiple security groups matching filter found."])

    return security_group[0]["GroupId"]


def attach_tags(aws_ec2_client, resource_id, name_tag=None):
    """attach tag(s) to a resource, including Namespace tag
    
    Requires the ec2:CreateTags permission.

    To account for newly created resources, InvalidID exceptions are checked 
    for and skipped in a loop attempting to create tag(s). Why not use 
    waiters? Because waiters don't work reliably, that's why.

    Args:
        aws_ec2_client: Get existing ec2_client so a new one isn't needed.
        resource_id: The ID of the resource.
        name_tag: A tag value to assign to the tag key "Name".
    """

    new_tags = [{
        "Key": "Namespace",
        "Value": config.NAMESPACE
    }]
    if name_tag is not None:
        new_tags.append({
            "Key": "Name",
            "Value": name_tag
        })

    invalid_id_regex = re.compile("Invalid[a-zA-Z]*ID")
    for _ in range(60):
        try:
            aws_ec2_client.create_tags(Resources=[resource_id], Tags=new_tags)
            return
        except ClientError as e:
            if invalid_id_regex.search(e.response["Error"]["Code"]) is None:
                quit_out.err(["Exception when tagging " + resource_id + ":",
                    e.response])
            sleep(1)

    quit_out.err([resource_id + " doesn't exist after a minute of wating."])


def decode_error_msg(error_response):
    """decode AWS encoded error messages (why are they encoded though?)

    Requires the sts:DecodeAuthorizationMessage permission.
    """
    encoded_message_indication = "Encoded authorization failure message: "

    if encoded_message_indication not in error_response["Error"]["Message"]:
        return {
            "Warning": "Error message wasn't encoded.",
            "ErrorMessage": error_response["Error"]["Message"]
        }

    encoded_error_str = error_response["Error"]["Message"].split(
        encoded_message_indication, 1)[1]

    return json.loads(boto3.client("sts",
        aws_access_key_id=config.IAM_ID,
        aws_secret_access_key=config.IAM_SECRET
    ).decode_authorization_message(
        EncodedMessage=encoded_error_str
    )["DecodedMessage"])
