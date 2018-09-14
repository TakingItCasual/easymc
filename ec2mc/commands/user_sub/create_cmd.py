import shutil
from time import sleep
import boto3
from botocore.exceptions import ClientError

from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

class CreateUser(CommandBase):

    def main(self, kwargs):
        """create a new Namespace IAM user under an IAM group on AWS"""
        iam_client = aws.iam_client()
        path_prefix = f"/{consts.NAMESPACE}/"

        # Validate specified IAM group exists
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
        print(f"IAM user \"{kwargs['name']}\" created on AWS.")

        # IAM user access key generated and saved to dictionary
        new_access_key = iam_client.create_access_key(
            UserName=kwargs['name'])['AccessKey']
        new_access_key = {
            'id': new_access_key['AccessKeyId'],
            'secret': new_access_key['SecretAccessKey']
        }
        self.access_key_usable_waiter(new_access_key)

        config_dict = os2.parse_json(consts.CONFIG_JSON)
        if 'backup_access_keys' not in config_dict:
            config_dict['backup_access_keys'] = []

        if kwargs['default']:
            # Modify existing config instead of creating new one
            config_dict['backup_access_keys'].append(config_dict['access_key'])
            config_dict['access_key'] = new_access_key
            os2.save_json(config_dict, consts.CONFIG_JSON)
            print("  User's access key set as default in config.")
        else:
            # Back up new IAM user's access key in config file
            config_dict['backup_access_keys'].append(new_access_key)
            os2.save_json(config_dict, consts.CONFIG_JSON)

            self.create_configuration_zip(
                new_access_key, kwargs['ssh_key'], kwargs['name'])
            print("  User's zipped configuration created in config.")


    @staticmethod
    def create_configuration_zip(new_access_key, give_ssh_key, user_name):
        """create zipped config folder containing new IAM user access key"""
        new_config_dict = {'access_key': new_access_key}
        if consts.REGION_WHITELIST is not None:
            new_config_dict['region_whitelist'] = consts.REGION_WHITELIST

        temp_dir = consts.CONFIG_DIR/".ec2mc"
        if temp_dir.is_dir():
            shutil.rmtree(temp_dir, onerror=os2.del_readonly)
        temp_dir.mkdir()

        shutil.copytree(consts.AWS_SETUP_DIR, temp_dir/"aws_setup")
        os2.save_json(new_config_dict, temp_dir/"config.json")

        if give_ssh_key is True:
            if consts.RSA_KEY_PEM.is_file():
                pem_base = consts.RSA_KEY_PEM.name
                shutil.copy(consts.RSA_KEY_PEM, temp_dir/pem_base)
            if consts.RSA_KEY_PPK.is_file():
                ppk_base = consts.RSA_KEY_PPK.name
                shutil.copy(consts.RSA_KEY_PPK, temp_dir/ppk_base)

        out_zip = consts.CONFIG_DIR/f"{user_name}_config"
        shutil.make_archive(out_zip, "zip", consts.CONFIG_DIR, ".ec2mc")
        shutil.rmtree(temp_dir, onerror=os2.del_readonly)


    @staticmethod
    def access_key_usable_waiter(new_access_key):
        """waiter for IAM user access key usability (not perfect)"""
        iam_client = boto3.client("iam",
            aws_access_key_id=new_access_key['id'],
            aws_secret_access_key=new_access_key['secret']
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


    def add_documentation(self, argparse_obj):
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
