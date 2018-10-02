from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.threader import Threader
from ec2mc.validate import validate_perms

from ec2mc.commands.aws_setup_sub import iam_policies
from ec2mc.commands.aws_setup_sub import iam_groups
from ec2mc.commands.aws_setup_sub import vpcs
from ec2mc.commands.aws_setup_sub import ssh_key_pairs

class AWSSetup(CommandBase):

    aws_components = [
        iam_policies.IAMPolicySetup,
        iam_groups.IAMGroupSetup,
        vpcs.VPCSetup,
        ssh_key_pairs.SSHKeyPairSetup
    ]

    def main(self, cmd_args):
        """manage AWS account setup with ~/.ec2mc/aws_setup/

        Args:
            cmd_args (dict): See add_documentation method.
        """
        if cmd_args['subcommand'] == "delete":
            path_prefix = f"/{consts.NAMESPACE}/"
            if not self.namespace_groups_empty(path_prefix):
                halt.err("IAM User(s) attached to namespace IAM group(s).")
            if not self.namespace_policies_empty(path_prefix):
                halt.err("IAM User(s) attached to namespace IAM policy(s).")
            if not self.namespace_vpcs_empty():
                halt.err("EC2 instance(s) found under namespace VPC(s).")

        # AWS setup JSON config dictionary
        config_aws_setup = os2.parse_json(consts.AWS_SETUP_JSON)

        for component in self.aws_components:
            component = component(config_aws_setup)
            component_info = component.check_component()
            print("")
            if cmd_args['subcommand'] == "check":
                component.notify_state(component_info)
            elif cmd_args['subcommand'] == "upload":
                component.upload_component(component_info)
            elif cmd_args['subcommand'] == "delete":
                component.delete_component()


    @staticmethod
    def namespace_groups_empty(path_prefix):
        """return False if any users attached to namespace groups"""
        iam_client = aws.iam_client()
        aws_groups = iam_client.list_groups(PathPrefix=path_prefix)['Groups']
        for aws_group in aws_groups:
            if iam_client.get_group(GroupName=aws_group['GroupName'])['Users']:
                return False
        return True


    @staticmethod
    def namespace_policies_empty(path_prefix):
        """return False if any users attached to namespace policies"""
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

    @classmethod
    def namespace_vpcs_empty(cls):
        """return False if any instances within namespace VPCs found"""
        threader = Threader()
        for region in consts.REGIONS:
            threader.add_thread(cls.region_vpc_empty, (region,))
        if not all(threader.get_results()):
            return False
        return True


    @staticmethod
    def region_vpc_empty(region):
        """return False if any instances found in region's namespace VPC"""
        ec2_client = aws.ec2_client(region)
        namespace_vpc = aws.get_region_vpc(region)
        if namespace_vpc is not None:
            vpc_reservations = ec2_client.describe_instances(Filters=[
                {'Name': "vpc-id", 'Values': [namespace_vpc['VpcId']]}
            ])['Reservations']
            if vpc_reservations:
                return False
        return True


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        subcommands = cmd_parser.add_subparsers(
            title="subcommands", metavar="<subcommand>", dest="subcommand")
        subcommands.required = True
        subcommands.add_parser(
            "check", help="check differences between local and AWS setup")
        subcommands.add_parser(
            "upload", help="configure AWS with ~/.ec2mc/aws_setup/")
        subcommands.add_parser(
            "delete", help="delete namespace configuration from AWS")


    def blocked_actions(self, cmd_args):
        denied_actions = []
        if cmd_args['subcommand'] == "delete":
            denied_actions.extend(validate_perms.blocked(actions=[
                "iam:ListGroups",
                "iam:GetGroup",
                "iam:ListPolicies",
                "iam:ListEntitiesForPolicy",
                "ec2:DescribeVpcs",
                "ec2:DescribeInstances"
            ]))
        for component in self.aws_components:
            denied_actions.extend(
                component.blocked_actions(cmd_args['subcommand']))
        return denied_actions
