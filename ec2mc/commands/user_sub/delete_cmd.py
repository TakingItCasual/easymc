from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

class DeleteUser(CommandBase):

    def main(self, kwargs):
        """delete an existing Namespace IAM user from AWS"""
        self.iam_client = aws.iam_client()
        path_prefix = f"/{consts.NAMESPACE}/"
        user_name = kwargs['name']

        # IAM user names cannot differ only by case
        if user_name.lower() == consts.IAM_NAME.lower():
            halt.err("You cannot delete yourself.")

        iam_users = self.iam_client.list_users(PathPrefix=path_prefix)['Users']
        for iam_user in iam_users:
            if iam_user['UserName'].lower() == user_name.lower():
                user_name = iam_user['UserName']
                break
        else:
            halt.err(f"IAM user \"{user_name}\" not found from AWS.")

        self.delete_user_access_keys(user_name)
        self.remove_user_from_groups(user_name)
        self.detach_user_from_policies(user_name)
        self.iam_client.delete_user(UserName=user_name)

        print("")
        print(f"IAM user \"{user_name}\" deleted from AWS.")


    def delete_user_access_keys(self, user_name):
        """delete IAM user's access key(s)"""
        aws_access_keys = self.iam_client.list_access_keys(
            UserName=user_name)['AccessKeyMetadata']
        for aws_access_key in aws_access_keys:
            self.iam_client.delete_access_key(
                UserName=user_name,
                AccessKeyId=aws_access_key['AccessKeyId']
            )

            # Remove IAM user's backed up access key from config
            config_dict = os2.parse_json(consts.CONFIG_JSON)
            if 'backup_access_keys' in config_dict:
                config_dict['backup_access_keys'][:] = [
                    access_key for access_key
                    in config_dict['backup_access_keys']
                    if access_key['id'] != aws_access_key['AccessKeyId']]
                if not config_dict['backup_access_keys']:
                    del config_dict['backup_access_keys']
                os2.save_json(config_dict, consts.CONFIG_JSON)


    def remove_user_from_groups(self, user_name):
        """remove IAM user from IAM groups"""
        user_groups = self.iam_client.list_groups_for_user(
            UserName=user_name)['Groups']
        for user_group in user_groups:
            self.iam_client.remove_user_from_group(
                GroupName=user_group['GroupName'],
                UserName=user_name
            )


    def detach_user_from_policies(self, user_name):
        """detach IAM user from IAM policies"""
        user_policies = self.iam_client.list_attached_user_policies(
            UserName=user_name)['AttachedPolicies']
        for user_policy in user_policies:
            self.iam_client.detach_user_policy(
                UserName=user_name,
                PolicyArn=user_policy['PolicyArn']
            )


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="name of IAM user to be deleted")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "iam:ListUsers",
            "iam:ListAccessKeys",
            "iam:DeleteAccessKey",
            "iam:ListGroupsForUser",
            "iam:RemoveUserFromGroup",
            "iam:ListAttachedUserPolicies",
            "iam:DetachUserPolicy",
            "iam:DeleteUser"
        ])
