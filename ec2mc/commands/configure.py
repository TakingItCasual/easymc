import os

from ec2mc import config
from ec2mc.commands import template
from ec2mc.utils import os2

class Configure(template.BaseClass):

    def main(self):
        """set IAM credentials, servers.dat path, and region whitelist"""

        # verify_config:main normally does this, but it wasn't called.
        if not os.path.isdir(config.CONFIG_DIR):
            os.mkdir(config.CONFIG_DIR)

        config_dict = {}
        iam_id_str = "None"
        iam_secret_str = "None"
        servers_dat_str = "None"
        whitelist_str = "All"

        if os.path.isfile(config.CONFIG_JSON):
            schema = os2.get_json_schema("config")
            config_dict = os2.parse_json(config.CONFIG_JSON)
            os2.validate_dict(config_dict, schema, "config.json")
            if "iam_id" in config_dict:
                iam_id_str = "*"*16 + config_dict["iam_id"][-4:]
            if "iam_secret" in config_dict:
                iam_secret_str = "*"*16 + config_dict["iam_secret"][-4:]
            if "servers_dat" in config_dict:
                servers_dat_str = config_dict["servers_dat"]
            if ("region_whitelist" in config_dict
                    and config_dict["region_whitelist"]):
                whitelist_str = ",".join(config_dict["region_whitelist"])

        iam_id = input(
            "AWS Access Key ID [" + iam_id_str + "]: ")
        iam_secret = input(
            "AWS Secret Access Key [" + iam_secret_str + "]: ")

        servers_dat = input(
            "MC client's servers.dat path [" + servers_dat_str + "]: ")
        # If given servers.dat path isn't valid, loop until valid or empty.
        while servers_dat and not (
                os.path.isfile(servers_dat) and
                servers_dat.endswith("servers.dat")):
            servers_dat = input(
                servers_dat + " is not valid. Try again or leave empty: ")

        region_whitelist = [input(
            "AWS region whitelist [" + whitelist_str + "] (first item): ")]
        while region_whitelist[-1] != "":
            region_whitelist.append(input(
                "Additional whitelist item (or leave empty): "))
        del region_whitelist[-1]

        # Only change key value(s) if non-empty string(s) given.
        if iam_id:
            config_dict["iam_id"] = iam_id
        if iam_secret:
            config_dict["iam_secret"] = iam_secret
        if servers_dat:
            config_dict["servers_dat"] = servers_dat
        if region_whitelist:
            config_dict["region_whitelist"] = region_whitelist

        os2.save_json(config_dict, config.CONFIG_JSON)
        os.chmod(config.CONFIG_JSON, config.CONFIG_PERMS)
