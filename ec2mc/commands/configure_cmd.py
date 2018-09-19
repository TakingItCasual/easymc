from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class Configure(CommandBase):

    def main(self, cmd_args):
        """configure, for example, the default IAM user access key"""
        # validate_config:main normally does this, but it wasn't called.
        consts.CONFIG_DIR.mkdir(exist_ok=True)

        config_dict = {}
        if consts.CONFIG_JSON.is_file():
            schema = os2.get_json_schema("config")
            config_dict = os2.parse_json(consts.CONFIG_JSON)
            os2.validate_dict(config_dict, schema, "config.json")

        if cmd_args['action'] == "access_key":
            config_dict = self.set_access_key(
                config_dict, cmd_args['key_id'], cmd_args['key_secret'])
        elif cmd_args['action'] == "swap_key":
            config_dict = self.switch_access_key(
                config_dict, cmd_args['user_name'])
        elif cmd_args['action'] == "whitelist":
            config_dict['region_whitelist'] = list(set(cmd_args['regions']))
            print("Region whitelist set.")
        elif cmd_args['action'] == "use_handler":
            config_dict['use_handler'] = cmd_args['boolean']
            print(f"IP handler usage set to {str(cmd_args['boolean'])}.")

        if config_dict:
            os2.save_json(config_dict, consts.CONFIG_JSON)
            consts.CONFIG_JSON.chmod(consts.CONFIG_PERMS)


    @staticmethod
    def set_access_key(config_dict, key_id, key_secret):
        """set id and secret of config's default access key"""
        if 'access_key' in config_dict:
            print("Existing access key overwritten.")
        else:
            print("Access key set.")
        config_dict['access_key'] = {key_id: key_secret}
        return config_dict


    @staticmethod
    def switch_access_key(config_dict, user_name):
        """set access key stored in backup access keys list as default"""
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

                print(f"{key_owner}'s access key set as default in config.")
                break
        else:
            halt.err(f"IAM User \"{user_name}\" backup access key not found.")

        return config_dict


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        actions = cmd_parser.add_subparsers(
            title="commands", metavar="<action>", dest="action")
        actions.required = True

        access_key_parser = actions.add_parser(
            "access_key", help="set default IAM user access key")
        access_key_parser.add_argument(
            "key_id", help="ID of access key")
        access_key_parser.add_argument(
            "key_secret", help="secret access key")

        swap_key_parser = actions.add_parser(
            "swap_key", help="switch default IAM user access key for another")
        swap_key_parser.add_argument(
            "user_name", help="name of desired access key owner")

        whitelist_parser = actions.add_parser(
            "whitelist", help="set whitelist for AWS regions")
        whitelist_parser.add_argument(
            "regions", nargs="+", help="list of AWS regions")

        use_handler_parser = actions.add_parser(
            "use_handler", help="use IP handlers described by instance tags")
        use_handler_parser.add_argument(
            "-f", "--false", dest="boolean", action="store_false",
            help="do not use the handler")


    def blocked_actions(self, cmd_args):
        if cmd_args['action'] == "swap_key":
            return validate_perms.blocked(actions=["iam:GetAccessKeyLastUsed"])
        return []
