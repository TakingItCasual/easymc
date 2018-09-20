from ec2mc import consts
from ec2mc.utils import os2
from ec2mc.utils.base_classes import CommandBase

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

        whitelist_parser = actions.add_parser(
            "whitelist", help="set whitelist for AWS regions")
        whitelist_parser.add_argument(
            "regions", nargs="+", help="list of AWS regions")

        use_handler_parser = actions.add_parser(
            "use_handler", help="use IP handlers described by instance tags")
        use_handler_parser.add_argument(
            "-f", "--false", dest="boolean", action="store_false",
            help="do not use the handler")
