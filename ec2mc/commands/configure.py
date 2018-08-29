import os

from ec2mc import consts
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

class Configure(CommandBase):

    def main(self, kwargs):
        """set IAM access key, servers.dat path, and region whitelist"""
        # validate_config:main normally does this, but it wasn't called.
        if not os.path.isdir(consts.CONFIG_DIR):
            os.mkdir(consts.CONFIG_DIR)

        config_dict = {}
        if os.path.isfile(consts.CONFIG_JSON):
            schema = os2.get_json_schema("config")
            config_dict = os2.parse_json(consts.CONFIG_JSON)
            os2.validate_dict(config_dict, schema, "config.json")

        # TODO: Implement use_handler configuring
        if kwargs['action'] == "access_key":
            config_dict = self.set_access_key(
                config_dict, kwargs['key_id'], kwargs['key_secret'])
        elif kwargs['action'] == "swap_user":
            config_dict = self.switch_access_key(
                config_dict, kwargs['user_name'])
        elif kwargs['action'] == "whitelist":
            config_dict = self.set_whitelist(config_dict, kwargs['regions'])
        elif kwargs['action'] == "use_handler":
            config_dict['use_handler'] = kwargs['boolean']
            print(f"IP handler usage set to {str(kwargs['boolean']).lower()}.")

        if config_dict:
            os2.save_json(config_dict, consts.CONFIG_JSON)
            os.chmod(consts.CONFIG_JSON, consts.CONFIG_PERMS)


    def set_access_key(self, config_dict, key_id, key_secret):
        """set id and secret of config's default access key"""
        if 'access_key' in config_dict:
            print("Existing access key overwritten.")
        else:
            print("Access key set.")
        config_dict['access_key'] = {'id': key_id, 'secret': key_secret}
        return config_dict


    def switch_access_key(self, config_dict, user_name):
        """set access key stored under backup_access_keys list as default"""
        if 'backup_access_keys' not in config_dict:
            halt.err("No backup access keys stored in config.")

        for index, access_key in enumerate(config_dict['backup_access_keys']):
            # TODO: Validate access key is active
            key_owner = aws.access_key_owner(access_key['id'])
            if key_owner is None:
                continue
            if key_owner.lower() == user_name.lower():
                # Swap default access key with requested IAM user's in config
                config_dict['backup_access_keys'].append({
                    'id': config_dict['access_key']['id'],
                    'secret': config_dict['access_key']['secret']
                })
                config_dict['access_key'] = {
                    'id': access_key['id'],
                    'secret': access_key['secret']
                }
                del config_dict['backup_access_keys'][index]

                print(f"{key_owner}'s access key set as default in config.")
                break
        else:
            halt.err(f"IAM User \"{user_name}\" backup access key not found.")

        return config_dict


    def set_whitelist(self, config_dict, regions):
        """set whitelist for AWS regions the script interacts with"""
        if regions:
            config_dict['region_whitelist'] = list(set(regions))
            print("Region whitelist set.")
        elif 'region_whitelist' in config_dict:
            del config_dict['region_whitelist']
            print("Region whitelist disabled.")
        else:
            print("Region whitelist is already disabled.")
        return config_dict


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        actions = cmd_parser.add_subparsers(
            metavar="{action}"+" "*5, dest="action")
        actions.required = True

        access_key_parser = actions.add_parser(
            "access_key", help="set default IAM user access key")
        access_key_parser.add_argument(
            "key_id", help="ID of access key")
        access_key_parser.add_argument(
            "key_secret", help="secret access key")

        swap_user_parser = actions.add_parser(
            "swap_user", help="switch default IAM user access key for another")
        swap_user_parser.add_argument(
            "user_name", help="name of desired access key owner")

        whitelist_parser = actions.add_parser(
            "whitelist", help="set whitelist for AWS regions")
        whitelist_parser.add_argument(
            "regions", nargs="*",
            help="list of regions (leave empty to disable whitelist)")

        use_handler_parser = actions.add_parser(
            "use_handler", help="use IP handlers described by instance tags")
        use_handler_parser.add_argument(
            "-f", "--false", dest="boolean", action="store_false",
            help="do not use the handler")
        use_handler_parser.set_defaults(boolean=True)


    def blocked_actions(self, kwargs):
        if kwargs['action'] == "swap_user":
            return validate_perms.blocked(actions=["iam:GetAccessKeyLastUsed"])
        return []
