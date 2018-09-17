"""miscellaneous functions that directly/indirectly interact with AWS"""

import re
from time import sleep
import boto3
from botocore.exceptions import ClientError

from ec2mc import consts
from ec2mc.utils import halt

def ec2_client(region):
    """create and return EC2 client using IAM user access key and a region"""
    if region is None: # True for when command has unused region argument
        if len(consts.REGIONS) > 1:
            halt.err("AWS region whitelist has more than one entry.",
                "  A region must be specified using the -r argument.")
        region = consts.REGIONS[0]
    elif region not in consts.REGIONS:
        halt.err(f"\"{region}\" not in region whitelist.")

    return boto3.client("ec2",
        aws_access_key_id=consts.KEY_ID,
        aws_secret_access_key=consts.KEY_SECRET,
        region_name=region
    )


def iam_client():
    """create and return IAM client using IAM user access key"""
    return boto3.client("iam",
        aws_access_key_id=consts.KEY_ID,
        aws_secret_access_key=consts.KEY_SECRET
    )


def get_region_vpc(region):
    """get VPC from region with name of aws_setup's Namespace

    Requires ec2:DescribeVpcs permission.
    """
    vpcs = ec2_client(region).describe_vpcs(Filters=[{
        'Name': "tag:Name",
        'Values': [consts.NAMESPACE]
    }])['Vpcs']

    if len(vpcs) > 1:
        halt.err(f"Multiple VPCs named {consts.NAMESPACE} in {region} region.")
    elif vpcs:
        return vpcs[0]
    return None


def get_vpc_security_groups(region, vpc_id):
    """get non-default security groups in specified VPC

    Requires ec2:DescribeSecurityGroups permission.
    """
    aws_sgs = ec2_client(region).describe_security_groups(Filters=[{
        'Name': "vpc-id",
        'Values': [vpc_id]
    }])['SecurityGroups']
    return [sg for sg in aws_sgs if sg['GroupName'] != "default"]


# TODO: Attach tag(s) on resource (e.g. VPC) creation when it becomes supported
def attach_tags(region, resource_id, name_tag=None):
    """attempt to attach tag(s) to resource (including Namespace tag) for 60s

    Requires ec2:CreateTags permission.

    The functionality of blocking until the resource exists is relied upon.

    To account for newly created resources, NotFound exceptions are checked
    for and passed in a loop attempting to create tag(s). Why not use waiters?
    Because waiters don't work reliably (in my experience), that's why.

    Args:
        region (str): AWS region the resource resides in.
        resource_id (str): The ID of the resource.
        name_tag (str): A tag value to assign to the tag key "Name".
    """
    new_tags = [{
        'Key': "Namespace",
        'Value': consts.NAMESPACE
    }]
    if name_tag is not None:
        new_tags.append({
            'Key': "Name",
            'Value': name_tag
        })

    not_found_regex = re.compile("Invalid[a-zA-Z]*\\.NotFound")
    for _ in range(60):
        try:
            ec2_client(region).create_tags(
                Resources=[resource_id], Tags=new_tags)
            break
        except ClientError as e:
            if not_found_regex.search(e.response['Error']['Code']) is None:
                halt.err(f"Exception when tagging {resource_id}:", str(e))
            sleep(1)
    else:
        halt.err(f"{resource_id} doesn't exist after a minute of waiting.")


def access_key_owner(access_key_id):
    """get name of IAM user who owns access key (or None if key invalid)

    Requires iam:GetAccessKeyLastUsed permission.
    """
    try:
        return iam_client().get_access_key_last_used(
            AccessKeyId=access_key_id)['UserName']
    except ClientError as e:
        if e.response['Error']['Code'] == "AccessDenied":
            return None
        halt.err(str(e))
