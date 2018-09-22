from time import sleep
import boto3
from botocore.exceptions import ClientError

from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class CreateUser(CommandBase):

    def main(self, cmd_args):
        """create a new IAM user under an IAM group"""
        iam_client = aws.iam_client()
        path_prefix = f"/{consts.NAMESPACE}/"

        # Validate specified IAM group exists
        iam_groups = iam_client.list_groups(PathPrefix=path_prefix)['Groups']
        for iam_group in iam_groups:
            if (iam_group['Path'] == path_prefix and
                    iam_group['GroupName'] == cmd_args['group']):
                break
        else:
            halt.err(f"IAM group {cmd_args['group']} not found from AWS.")

        # IAM user created and added to group (given the name is unique)
        try:
            iam_client.create_user(
                Path=path_prefix, UserName=cmd_args['name'])
        except ClientError as e:
            if e.response['Error']['Code'] == "EntityAlreadyExists":
                halt.err(f"IAM user \"{cmd_args['name']}\" already exists.")
            halt.err(str(e))
        iam_client.add_user_to_group(
            GroupName=cmd_args['group'],
            UserName=cmd_args['name']
        )

        print("")
        print(f"IAM user \"{cmd_args['name']}\" created on AWS.")

        # IAM user access key generated and saved to dictionary
        new_key = iam_client.create_access_key(
            UserName=cmd_args['name'])['AccessKey']
        new_key = {new_key['AccessKeyId']: new_key['SecretAccessKey']}
        self.access_key_usable_waiter(new_key)

        config_dict = os2.parse_json(consts.CONFIG_JSON)
        if 'backup_keys' not in config_dict:
            config_dict['backup_keys'] = {}

        if cmd_args['default']:
            # Modify existing config instead of creating new one
            config_dict['backup_keys'].update(config_dict['access_key'])
            config_dict['access_key'] = new_key
            os2.save_json(config_dict, consts.CONFIG_JSON)
            print("  User's access key set as default in config.")
        else:
            # Back up new IAM user's access key in config file
            config_dict['backup_keys'].update(new_key)
            os2.save_json(config_dict, consts.CONFIG_JSON)

            os2.create_configuration_zip(
                new_key, cmd_args['ssh_key'], cmd_args['name'])
            print("  User's zipped configuration created in config.")


    @staticmethod
    def access_key_usable_waiter(new_key):
        """waiter for IAM user access key usability (not perfect)"""
        iam_client = boto3.client("iam",
            aws_access_key_id=next(iter(new_key)),
            aws_secret_access_key=next(iter(new_key.values()))
        )
        for _ in range(60):
            try:
                # New IAM user is assumed to have the iam:GetUser permission.
                iam_client.get_user()
                break
            except ClientError:
                sleep(1)
        else:
            halt.err("Access key not usable even after waiting 1 minute.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="name to assign to the IAM user")
        cmd_parser.add_argument(
            "group", help="name of IAM group to assign IAM user to")
        cmd_group = cmd_parser.add_mutually_exclusive_group()
        cmd_group.add_argument(
            "-d", "--default", action="store_true",
            help="set new IAM user's access key as default in config")
        cmd_group.add_argument(
            "-k", "--ssh_key", action="store_true",
            help="copy RSA private key to new user's zipped configuration")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "iam:ListGroups",
            "iam:CreateUser",
            "iam:AddUserToGroup",
            "iam:CreateAccessKey"
        ])
