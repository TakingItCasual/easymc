from ec2mc import config
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

def main():
    """verify that AWS account setup matches config.AWS_SETUP_DIR"""
    pass


def security_group(region):
    """verify that AWS has the security group defined in config.AWS_SETUP_DIR

    Args:
        region (str): EC2 region to check security group in

    Returns:
        str: ID for security group used for Minecraft instances
    """

    quit_out.assert_empty(simulate_policy.blocked(actions=[
        "ec2:DescribeSecurityGroups"
    ]))

    # TODO: Filter based on SG in config.AWS_SETUP_DIR

    ec2_client = aws.ec2_client(region)
    security_groups = ec2_client.describe_security_groups()["SecurityGroups"]
    security_group = [SG for SG in security_groups 
        if config.SECURITY_GROUP_FILTER.lower() in SG["GroupName"].lower()]

    if not security_group:
        quit_out.err(["No security groups matching aws_setup found."])
    elif len(security_group) > 1:
        quit_out.err(["Multiple security groups matching filter found."])

    return security_group[0]["GroupId"]


def get_all_keys():
    """get instance tags from all instances in all regions"""
    pass
