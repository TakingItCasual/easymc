from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class RotateUserKey(CommandBase):

    def __init__(self, cmd_args):
        self._iam_client = aws.iam_client()


    def main(self, cmd_args):
        """delete IAM user's access key(s) and create a new one"""
        path_prefix = f"/{consts.NAMESPACE}/"
        user_name = aws.validate_user_exists(path_prefix, cmd_args.name)

        old_access_keys = self._iam_client.list_access_keys(
            UserName=user_name)['AccessKeyMetadata']
        old_key_ids = [key['AccessKeyId'] for key in old_access_keys]

        new_key = self._rotate_user_key(old_key_ids, user_name)
        self._update_config_dict(new_key, old_key_ids)

        print("")
        print(f"{user_name}'s access key rotated.")

        os2.create_configuration_zip(user_name, new_key, cmd_args.ssh_key)
        print("  User's updated zipped configuration created in config.")


    def _rotate_user_key(self, old_key_ids, user_name):
        """rotate IAM user's access key"""
        for key_id in old_key_ids:
            if key_id != consts.KEY_ID:
                self._iam_client.delete_access_key(
                    UserName=user_name,
                    AccessKeyId=key_id
                )

        new_key = self._iam_client.create_access_key(
            UserName=user_name)['AccessKey']
        new_key = {new_key['AccessKeyId']: new_key['SecretAccessKey']}

        if consts.KEY_ID in old_key_ids:
            self._iam_client.delete_access_key(
                UserName=user_name,
                AccessKeyId=consts.KEY_ID
            )

        return new_key


    @staticmethod
    def _update_config_dict(new_key, old_key_ids):
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
        cmd_parser.add_argument(
            "-k", "--ssh_key", action="store_true",
            help="copy RSA private key to user's zipped configuration")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "iam:ListUsers",
            "iam:ListAccessKeys",
            "iam:CreateAccessKey",
            "iam:DeleteAccessKey"
        ])
