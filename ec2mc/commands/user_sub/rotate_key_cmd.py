from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class RotateUserKey(CommandBase):

    def main(self, cmd_args):
        """delete IAM user's access key(s) and create new one"""
        self.iam_client = aws.iam_client()
        path_prefix = f"/{consts.NAMESPACE}/"
        user_name = cmd_args['name']

        iam_users = self.iam_client.list_users(PathPrefix=path_prefix)['Users']
        for iam_user in iam_users:
            if iam_user['UserName'].lower() == user_name.lower():
                user_name = iam_user['UserName']
                break
        else:
            halt.err(f"IAM user \"{user_name}\" not found from AWS.")

        if user_name == consts.IAM_NAME:
            new_key, old_key_ids = self.rotate_own_access_key(user_name)
        else:
            new_key, old_key_ids = self.rotate_user_access_key(user_name)
        self.update_config_dict(new_key, old_key_ids)

        print("")
        print(f"{user_name}'s access key rotated.")


    def rotate_user_access_key(self, user_name):
        """rotate access key for IAM user other than default IAM user"""
        old_access_keys = self.iam_client.list_access_keys(
            UserName=user_name)['AccessKeyMetadata']
        old_key_ids = [key['AccessKeyId'] for key in old_access_keys]
        for key_id in old_key_ids:
            self.iam_client.delete_access_key(
                UserName=user_name,
                AccessKeyId=key_id
            )

        new_key = self.iam_client.create_access_key(
            UserName=user_name)['AccessKey']
        new_key = {new_key['AccessKeyId']: new_key['SecretAccessKey']}

        return new_key, old_key_ids


    def rotate_own_access_key(self, user_name):
        """rotate access key for default IAM user"""
        old_access_keys = self.iam_client.list_access_keys(
            UserName=user_name)['AccessKeyMetadata']
        old_key_ids = [key['AccessKeyId'] for key in old_access_keys]
        for key_id in old_key_ids:
            if key_id != consts.KEY_ID:
                self.iam_client.delete_access_key(
                    UserName=user_name,
                    AccessKeyId=key_id
                )

        new_key = self.iam_client.create_access_key(
            UserName=user_name)['AccessKey']
        new_key = {new_key['AccessKeyId']: new_key['SecretAccessKey']}
        self.iam_client.delete_access_key(
            UserName=user_name,
            AccessKeyId=consts.KEY_ID
        )

        return new_key, old_key_ids


    @staticmethod
    def update_config_dict(new_key, old_key_ids):
        """remove old access keys and place new one in config"""
        config_dict = os2.parse_json(consts.CONFIG_JSON)

        if 'backup_keys' in config_dict:
            for old_key_id in old_key_ids:
                config_dict['backup_keys'].pop(old_key_id, None)
            if not config_dict['backup_keys']:
                del config_dict['backup_keys']

        if next(iter(config_dict['access_key'])) in old_key_ids:
            config_dict['access_key'] = new_key
        else:
            config_dict.setdefault('backup_keys', {}).update(new_key)

        os2.save_json(config_dict, consts.CONFIG_JSON)


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="name of IAM user to rotate keys for")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "iam:ListUsers",
            "iam:ListAccessKeys",
            "iam:CreateAccessKey",
            "iam:DeleteAccessKey"
        ])
