import os
import shutil
import zipfile
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.verify import verify_perms

class CreateUser(CommandBase):

    def main(self, kwargs):
        """create a new Namespace IAM user under an IAM group on AWS"""
        iam_client = aws.iam_client()
        path_prefix = f"/{config.NAMESPACE}/"

        # Specified IAM group verified to exist
        iam_groups = iam_client.list_groups(PathPrefix=path_prefix)['Groups']
        for iam_group in iam_groups:
            if (iam_group['Path'] == path_prefix and
                    iam_group['GroupName'] == kwargs['group']):
                break
        else:
            halt.err(f"IAM group {kwargs['group']} not found from AWS.")

        # IAM user created and added to group (given the name is unique)
        try:
            iam_client.create_user(
                Path=path_prefix, UserName=kwargs['name'])
        except ClientError as e:
            if e.response['Error']['Code'] == "EntityAlreadyExists":
                halt.err(f"IAM user \"{kwargs['name']}\" already exists.")
            halt.err(str(e))
        iam_client.add_user_to_group(
            GroupName=kwargs['group'],
            UserName=kwargs['name']
        )

        print("")
        print(f"IAM user \"{kwargs['name']}\" created on AWS")

        # IAM user credentials generated and saved to dictionary
        new_credentials = iam_client.create_access_key(
            UserName=kwargs['name'])['AccessKey']
        config_dict = os2.parse_json(config.CONFIG_JSON)
        if 'iam_access_keys' not in config_dict:
            config_dict['iam_access_keys'] = []

        if kwargs['default']:
            # Modify existing config instead of creating new one
            config_dict['iam_access_keys'].append({
                'iam_id': config_dict['iam_id'],
                'iam_secret': config_dict['iam_secret']
            })
            config_dict.update({
                'iam_id': new_credentials['AccessKeyId'],
                'iam_secret': new_credentials['SecretAccessKey']
            })
            os2.save_json(config_dict, config.CONFIG_JSON)
            print("  User's credentials set as default in config.")
        else:
            # Back up new credentials in config file
            config_dict['iam_access_keys'].append({
                'iam_id': new_credentials['AccessKeyId'],
                'iam_secret': new_credentials['SecretAccessKey']
            })
            os2.save_json(config_dict, config.CONFIG_JSON)

            #self.create_configuration_zip(new_credentials)
            #print("  User's zipped config folder created in config.")


    def create_configuration_zip(self, new_credentials):
        """create zipped config folder containing new credentials"""
        new_config = {
            'iam_id': new_credentials['AccessKeyId'],
            'iam_secret': new_credentials['SecretAccessKey']
        }
        if config.REGION_WHITELIST is not None:
            new_config['region_whitelist'] = config.REGION_WHITELIST

        temp_dir = os.path.join(f"{config.CONFIG_DIR}.ec2mc", "")
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)

        if kwargs['ssh_key']:
            pass


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="name to assign to the IAM user")
        cmd_parser.add_argument(
            "group", help="name of IAM group to assign IAM user to")
        cmd_parser.add_argument(
            "-d", "--default", action="store_true",
            help="set new IAM user's credentials as primary credentials")
        cmd_parser.add_argument(
            "-k", "--ssh_key", action="store_true",
            help="copy RSA private key to new user's zipped configuration")


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "iam:ListGroups",
            "iam:CreateUser",
            "iam:AddUserToGroup",
            "iam:CreateAccessKey"
        ])
