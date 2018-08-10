from ec2mc import config
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.threader import Threader
from ec2mc.verify import verify_perms

from ec2mc.commands.aws_setup_sub import iam_policies
from ec2mc.commands.aws_setup_sub import iam_groups
from ec2mc.commands.aws_setup_sub import vpcs
from ec2mc.commands.aws_setup_sub import ssh_key_pairs

class AWSSetup(CommandBase):

    def __init__(self):
        super().__init__()
        self.aws_components = [
            iam_policies.IAMPolicySetup(),
            iam_groups.IAMGroupSetup(),
            vpcs.VPCSetup(),
            ssh_key_pairs.SSHKeyPairSetup()
        ]


    def main(self, kwargs):
        """manage AWS account setup with ~/.ec2mc/aws_setup/

        Args:
            kwargs (dict):
                'action': Whether to check, upload, or delete setup on AWS
        """
        if kwargs['action'] == "delete":
            path_prefix = f"/{config.NAMESPACE}/"
            if not self.verify_namespace_groups_empty(path_prefix):
                halt.err("IAM User(s) attached to Namespace IAM group(s).")
            if not self.verify_namespace_policies_empty(path_prefix):
                halt.err("IAM User(s) attached to Namespace IAM policy(s).")
            if not self.verify_namespace_vpcs_empty():
                halt.err("EC2 instance(s) found under Namespace VPC(s).")

        # AWS setup JSON config dictionary
        config_aws_setup = os2.parse_json(config.AWS_SETUP_JSON)

        for component in self.aws_components:
            component_info = component.verify_component(config_aws_setup)
            print("")
            if kwargs['action'] == "check":
                component.notify_state(component_info)
            elif kwargs['action'] == "upload":
                component.upload_component(component_info)
            elif kwargs['action'] == "delete":
                component.delete_component()


    def verify_namespace_groups_empty(self, path_prefix):
        """return False if any users attached to Namespace groups"""
        iam_client = aws.iam_client()
        aws_groups = iam_client.list_groups(PathPrefix=path_prefix)['Groups']
        for aws_group in aws_groups:
            if iam_client.get_group(GroupName=aws_group['GroupName'])['Users']:
                return False
        return True


    def verify_namespace_policies_empty(self, path_prefix):
        """return False if any users attached to Namespace policies"""
        iam_client = aws.iam_client()
        aws_policies = iam_client.list_policies(
            Scope="Local",
            OnlyAttached=True,
            PathPrefix=path_prefix
        )['Policies']
        for aws_policy in aws_policies:
            attached_users = iam_client.list_entities_for_policy(
                PolicyArn=aws_policy['Arn'],
                EntityFilter="User"
            )['PolicyUsers']
            if attached_users:
                return False
        return True


    def verify_namespace_vpcs_empty(self):
        """return False if any instances within Namespace VPCs found"""
        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(self.region_vpc_is_empty, (region,))
        if not all(threader.get_results()):
            return False
        return True


    def region_vpc_is_empty(self, region):
        """return False if any instances found in region's Namespace VPC"""
        ec2_client = aws.ec2_client(region)
        namespace_vpc = aws.get_region_vpc(region)
        if namespace_vpc is not None:
            vpc_reservations = ec2_client.describe_instances(Filters=[{
                'Name': "vpc-id",
                'Values': [namespace_vpc['VpcId']]
            }])['Reservations']
            if vpc_reservations:
                return False
        return True


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        actions = cmd_parser.add_subparsers(metavar="{action}", dest="action")
        actions.required = True
        actions.add_parser(
            "check", help="check differences between local and AWS setup")
        actions.add_parser(
            "upload", help="configure AWS with ~/.ec2mc/aws_setup/")
        actions.add_parser(
            "delete", help="delete Namespace configuration from AWS")


    def blocked_actions(self, kwargs):
        denied_actions = []
        if kwargs['action'] == "delete":
            denied_actions.extend(verify_perms.blocked(actions=[
                "iam:ListGroups",
                "iam:GetGroup",
                "iam:ListPolicies",
                "iam:ListEntitiesForPolicy",
                "ec2:DescribeRegions",
                "ec2:DescribeVpcs",
                "ec2:DescribeInstances"
            ]))
        for component in self.aws_components:
            denied_actions.extend(component.blocked_actions(kwargs['action']))
        return denied_actions
