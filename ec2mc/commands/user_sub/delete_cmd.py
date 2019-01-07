from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class DeleteUser(CommandBase):

    def __init__(self, cmd_args):
        self._iam_client = aws.iam_client()


    def main(self, cmd_args):
        """delete an existing IAM user from AWS"""
        path_prefix = f"/{consts.NAMESPACE}/"
        user_name = cmd_args.name

        # IAM user names cannot differ only by case
        if user_name.lower() == consts.IAM_NAME.lower():
            halt.err("You cannot delete yourself.")

        user_name = aws.validate_user_exists(path_prefix, user_name)
        self._delete_user_access_keys(user_name)
        self._remove_user_from_groups(user_name)
        self._detach_user_from_policies(user_name)
        self._iam_client.delete_user(UserName=user_name)

        print("")
        print(f"IAM user \"{user_name}\" deleted from AWS.")

        user_config_zip = consts.CONFIG_DIR / f"{user_name}_config.zip"
        if user_config_zip.is_file():
            user_config_zip.unlink()
            print("  User's zipped configuration deleted from config.")


    def _delete_user_access_keys(self, user_name):
        """delete IAM user's access key(s)"""
        aws_access_keys = self._iam_client.list_access_keys(
            UserName=user_name)['AccessKeyMetadata']
        for access_key in aws_access_keys:
            self._iam_client.delete_access_key(
                UserName=user_name,
                AccessKeyId=access_key['AccessKeyId']
            )

            # Remove IAM user's backed up access key from config
            config_dict = os2.parse_json(consts.CONFIG_JSON)
            if 'backup_keys' in config_dict:
                config_dict['backup_keys'].pop(access_key['AccessKeyId'], None)
                if not config_dict['backup_keys']:
                    del config_dict['backup_keys']
                os2.save_json(config_dict, consts.CONFIG_JSON)


    def _remove_user_from_groups(self, user_name):
        """remove IAM user from IAM groups"""
        user_groups = self._iam_client.list_groups_for_user(
            UserName=user_name)['Groups']
        for user_group in user_groups:
            self._iam_client.remove_user_from_group(
                GroupName=user_group['GroupName'],
                UserName=user_name
            )


    def _detach_user_from_policies(self, user_name):
        """detach IAM user from IAM policies"""
        user_policies = self._iam_client.list_attached_user_policies(
            UserName=user_name)['AttachedPolicies']
        for user_policy in user_policies:
            self._iam_client.detach_user_policy(
                UserName=user_name,
                PolicyArn=user_policy['PolicyArn']
            )


    @classmethod
    def add_documentation(cls, argparse_obj):
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
