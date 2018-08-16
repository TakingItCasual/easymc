import zipfile
from shutil import copyfile
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.verify import verify_perms

class DeleteUser(CommandBase):

    def main(self, kwargs):
        """delete an existing Namespace IAM user from AWS"""
        iam_client = aws.iam_client()
        path_prefix = f"/{config.NAMESPACE}/"
        user_name = kwargs['name']

        if user_name == config.IAM_NAME:
            halt.err("You cannot delete yourself.")

        iam_users = iam_client.list_users(PathPrefix=path_prefix)['Users']
        for iam_user in iam_users:
            if iam_user['UserName'] == user_name:
                break
        else:
            halt.err(f"IAM user \"{user_name}\" not found from AWS.")

        aws_access_keys = iam_client.list_access_keys(
            UserName=user_name)['AccessKeyMetadata']
        for aws_access_key in aws_access_keys:
            iam_client.delete_access_key(
                UserName=user_name,
                AccessKeyId=aws_access_key['AccessKeyId']
            )

            # Remove IAM user's backed up access key from config
            config_dict = os2.parse_json(config.CONFIG_JSON)
            if 'iam_access_keys' in config_dict:
                config_dict['iam_access_keys'][:] = [
                    access_key for access_key in config_dict['iam_access_keys']
                    if access_key['iam_id'] != aws_access_key['AccessKeyId']]
                os2.save_json(config_dict, config.CONFIG_JSON)

        user_groups = iam_client.list_groups_for_user(
            UserName=user_name)['Groups']
        for user_group in user_groups:
            iam_client.remove_user_from_group(
                GroupName=user_group['GroupName'],
                UserName=user_name
            )

        user_policies = iam_client.list_attached_user_policies(
            UserName=user_name)['AttachedPolicies']
        for user_policy in user_policies:
            iam_client.detach_user_policy(
                UserName=user_name,
                PolicyArn=user_policy['PolicyArn']
            )

        iam_client.delete_user(UserName=user_name)

        print("")
        print(f"IAM user \"{user_name}\" deleted from AWS.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="name of IAM user to be deleted")


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "iam:ListUsers",
            "iam:ListAccessKeys",
            "iam:DeleteAccessKey",
            "iam:ListGroupsForUser",
            "iam:RemoveUserFromGroup",
            "iam:ListAttachedUserPolicies",
            "iam:DetachUserPolicy",
            "iam:DeleteUser"
        ])
