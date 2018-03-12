import os
import configparser

from ec2mc import config
from ec2mc import command_template

class Configure(command_template.BaseClass):

    def main(self):
        """set IAM user's credentials and servers.dat file path"""

        if not os.path.isdir(config.CONFIG_DIR):
            os.mkdir(config.CONFIG_DIR)

        iam_id_str = "None"
        iam_secret_str = "None"
        servers_dat_str = "None"

        config_dict = configparser.ConfigParser()
        config_dict["default"] = {}

        config_file = config.CONFIG_DIR + "config"
        if os.path.isfile(config_file):
            config_dict.read(config_file)
            if config_dict.has_option("default", "iam_id"):
                iam_id_str = (
                    "*"*16 + config_dict["default"]["iam_id"][-4:])
            if config_dict.has_option("default", "iam_secret"):
                iam_secret_str = (
                    "*"*16 + config_dict["default"]["iam_secret"][-4:])
            if config_dict.has_option("default", "servers_dat"):
                servers_dat_str = config_dict["default"]["servers_dat"]

        iam_id = input(
            "AWS Access Key ID [" + iam_id_str + "]: ")
        iam_secret = input(
            "AWS Secret Access Key [" + iam_secret_str + "]: ")
        servers_dat = input(
            "MC client's servers.dat file path [" + servers_dat_str + "]: ")

        while (servers_dat and (
            not os.path.isfile(servers_dat) or 
            not servers_dat.endswith("servers.dat")
            )):
            servers_dat = input(
                servers_dat + " is not valid. Try again or leave empty: ")

        if iam_id:
            config_dict["default"]["iam_id"] = iam_id
        if iam_secret:
            config_dict["default"]["iam_secret"] = iam_secret
        if servers_dat:
            config_dict["default"]["servers_dat"] = servers_dat

        with open(config_file, "w") as output:
            config_dict.write(output)
        os.chmod(config_file, config.CONFIG_PERMS)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)


    def blocked_actions(self, _):
        return []


    def module_name(self):
        return super().module_name(__name__)
