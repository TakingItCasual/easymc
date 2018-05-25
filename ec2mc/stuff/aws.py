"""miscellaneous functions that directly interact with AWS"""

import re
from time import sleep
import json
import boto3
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.stuff import halt

def get_regions(region_filter=None):
    """return list of EC2 regions, or region_filter if not empty and valid

    Requires ec2:DescribeRegions permission.
    """

    region_list = []
    for region in ec2_client().describe_regions()["Regions"]:
        region_list.append(region["RegionName"])

    # The returned list cannot be empty, so the filter must be valid.
    if region_filter:
        if set(region_filter).issubset(set(region_list)):
            return list(set(region_filter))
        halt.err(["Following invalid region(s) specified:",
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

    Requires ec2:DescribeVpcs permission.
    """
    vpcs = ec2_client(region).describe_vpcs(Filters=[{
        "Name": "tag:Namespace",
        "Values": [config.NAMESPACE]
    }])["Vpcs"]

    if len(vpcs) > 1:
        halt.err(["Multiple VPCs with Namespace tag " + config.NAMESPACE +
            " found from AWS."])
    elif vpcs:
        return vpcs[0]
    return None


def get_region_security_groups(region, vpc_id=None):
    """get security groups from region with config's Namespace tag"""
    sg_filter = [{
        "Name": "tag:Namespace",
        "Values": [config.NAMESPACE]
    }]
    if vpc_id:
        sg_filter.append({
            "Name": "vpc-id",
            "Values": [vpc_id]
        })

    vpc_sgs = ec2_client(region).describe_security_groups(
        Filters=sg_filter)["SecurityGroups"]

    sg_group_names = [sg["GroupName"] for sg in vpc_sgs]
    if len(sg_group_names) > len(set(sg_group_names)):
        halt.err(["SGs with duplicate group names in " + region + " region."])
    return vpc_sgs


# TODO: Attach tag(s) on resource (e.g. VPC) creation when it becomes supported
def attach_tags(aws_ec2_client, resource_id, name_tag=None):
    """attach tag(s) to resource, including Namespace tag, and try for 60s
    
    Requires ec2:CreateTags permission.

    To account for newly created resources, InvalidID exceptions are checked 
    for and passed in a loop attempting to create tag(s). Why not use waiters? 
    Because waiters don't work reliably, that's why.

    Args:
        aws_ec2_client: Get existing EC2 client so a new one isn't needed.
        resource_id (str): The ID of the resource.
        name_tag (str): A tag value to assign to the tag key "Name".
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

    not_found_regex = re.compile("Invalid[a-zA-Z]*\\.NotFound")
    for _ in range(60):
        try:
            aws_ec2_client.create_tags(Resources=[resource_id], Tags=new_tags)
            return
        except ClientError as e:
            if not_found_regex.search(e.response["Error"]["Code"]) is None:
                halt.err(["Exception when tagging " + resource_id + ":",
                    str(e)])
            sleep(1)

    halt.err([resource_id + " doesn't exist after a minute of wating."])


def decode_error_msg(error_response):
    """decode AWS encoded error messages (why are they encoded though?)

    Requires sts:DecodeAuthorizationMessage permission.
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
