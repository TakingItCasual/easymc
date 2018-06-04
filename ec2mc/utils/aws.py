"""miscellaneous functions that directly/indirectly interact with AWS"""

import re
from time import sleep
import boto3
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.utils import halt

def get_regions():
    """return list of AWS regions, or config's region whitelist if defined

    Requires ec2:DescribeRegions permission.
    """

    region_whitelist = []
    if config.REGION_WHITELIST is not None:
        region_whitelist = [{
            "Name": "region-name",
            "Values": config.REGION_WHITELIST
        }]

    response = ec2_client(config.DEFAULT_REGION).describe_regions(
        Filters=region_whitelist)
    return [region["RegionName"] for region in response["Regions"]]


def ec2_client(region):
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
        halt.err("Multiple VPCs with Namespace tag " + config.NAMESPACE +
            " found from AWS.")
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
        halt.err("SGs with duplicate group names in " + region + " region.")
    return vpc_sgs


# TODO: Attach tag(s) on resource (e.g. VPC) creation when it becomes supported
def attach_tags(aws_ec2_client, resource_id, name_tag=None):
    """attempt to attach tag(s) to resource (including Namespace tag) for 60s
    
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
            break
        except ClientError as e:
            if not_found_regex.search(e.response["Error"]["Code"]) is None:
                halt.err("Exception when tagging " + resource_id + ":",
                    str(e))
            sleep(1)
    else:
        halt.err(resource_id + " doesn't exist after a minute of waiting.")
