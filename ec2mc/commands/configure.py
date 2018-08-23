import os

from ec2mc import config
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

# TODO: Think through how to manage config's servers_dat entry
class Configure(CommandBase):

    def main(self, kwargs):
        """set IAM access key, servers.dat path, and region whitelist"""
        # validate_config:main normally does this, but it wasn't called.
        if not os.path.isdir(config.CONFIG_DIR):
            os.mkdir(config.CONFIG_DIR)

        config_dict = {}
        if os.path.isfile(config.CONFIG_JSON):
            schema = os2.get_json_schema("config")
            config_dict = os2.parse_json(config.CONFIG_JSON)
            os2.validate_dict(config_dict, schema, "config.json")

        if kwargs['swap_user'] is not None:
            config_dict = self.switch_access_key(
                config_dict, kwargs['swap_user'])
        else:
            config_dict = self.default_set_config(config_dict)

        if config_dict:
            os2.save_json(config_dict, config.CONFIG_JSON)
            os.chmod(config.CONFIG_JSON, config.CONFIG_PERMS)


    def default_set_config(self, config_dict):
        """default behavior when no argparse arguments are specified"""
        iam_id_str = "None"
        iam_secret_str = "None"
        servers_dat_str = "None"
        whitelist_str = "All"

        if 'iam_id' in config_dict:
            iam_id_str = "*"*16 + config_dict['iam_id'][-4:]
        if 'iam_secret' in config_dict:
            iam_secret_str = "*"*16 + config_dict['iam_secret'][-4:]
        if 'servers_dat' in config_dict:
            servers_dat_str = config_dict['servers_dat']
        if ('region_whitelist' in config_dict
                and config_dict['region_whitelist']):
            whitelist_str = ",".join(config_dict['region_whitelist'])

        iam_id = input(f"AWS Access Key ID [{iam_id_str}]: ")
        iam_secret = input(f"AWS Secret Access Key [{iam_secret_str}]: ")

        servers_dat = input(
            f"MC client's servers.dat path [{servers_dat_str}]: ")
        # If given servers.dat path isn't valid, loop until valid or empty.
        while servers_dat and not (
                os.path.isfile(servers_dat) and
                servers_dat.endswith("servers.dat")):
            servers_dat = input(
                f"{servers_dat} is not valid. Try again or leave empty: ")

        region_whitelist = [input(
            f"AWS region whitelist [{whitelist_str}] (first item): ")]
        while region_whitelist[-1] != "":
            region_whitelist.append(input(
                "Additional whitelist item (or leave empty): "))
        del region_whitelist[-1]

        # Only modify key value(s) if non-empty string(s) given.
        if iam_id:
            config_dict['iam_id'] = iam_id
        if iam_secret:
            config_dict['iam_secret'] = iam_secret
        if servers_dat:
            config_dict['servers_dat'] = servers_dat
        if region_whitelist:
            config_dict['region_whitelist'] = region_whitelist

        return config_dict


    def switch_access_key(self, config_dict, user_name):
        """set access key stored under iam_access_keys list as primary"""
        if not ('iam_access_keys' in config_dict and
                config_dict['iam_access_keys']):
            halt.err("No backup access keys stored in config.")

        for index, access_key in enumerate(config_dict['iam_access_keys']):
            # TODO: Validate access key is active
            key_owner = aws.access_key_owner(access_key['iam_id'])
            if key_owner.lower() == user_name.lower():
                # Swap default access key with requested IAM user's in config
                config_dict['iam_access_keys'].append({
                    'iam_id': config_dict['iam_id'],
                    'iam_secret': config_dict['iam_secret']
                })
                config_dict.update({
                    'iam_id': access_key['iam_id'],
                    'iam_secret': access_key['iam_secret']
                })
                del config_dict['iam_access_keys'][index]

                print(f"{key_owner}'s access key set as default in config.")
                break
        else:
            halt.err(f"IAM User \"{user_name}\" backup access key not found.")

        return config_dict


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "--swap_user", metavar="",
            help="swap default access key in config")


    def blocked_actions(self, kwargs):
        if kwargs['swap_user'] is not None:
            return validate_perms.blocked(actions=["iam:GetAccessKeyLastUsed"])
        return []
