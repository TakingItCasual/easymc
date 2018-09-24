from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class BeUser(CommandBase):

    def main(self, cmd_args):
        """set another IAM user's access key as default in config"""
        user_name = cmd_args['user_name']

        if user_name.lower() == consts.IAM_NAME.lower():
            halt.err(f"You are already {consts.IAM_NAME}.")

        user_name = self.switch_access_key(user_name)

        print("")
        print(f"{user_name}'s access key set as default in config.")


    @staticmethod
    def switch_access_key(user_name):
        """set access key stored in backup access keys list as default"""
        config_dict = os2.parse_json(consts.CONFIG_JSON)
        if 'backup_keys' not in config_dict:
            halt.err("No backup access keys stored in config.")

        for key_id, key_secret in config_dict['backup_keys'].items():
            # TODO: Validate access key is active
            key_owner = aws.access_key_owner(key_id)
            if key_owner is None:
                continue
            if key_owner.lower() == user_name.lower():
                # Swap default access key with requested IAM user's in config
                config_dict['backup_keys'].update(config_dict['access_key'])
                config_dict['access_key'] = {key_id: key_secret}
                del config_dict['backup_keys'][key_id]

                os2.save_json(config_dict, consts.CONFIG_JSON)
                return key_owner

        halt.err(f"Backup access key for IAM user \"{user_name}\" not found.")



    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "user_name", help="name of user to become")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=["iam:GetAccessKeyLastUsed"])
