import os
import configparser
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.verify import verify_aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

def main():
    """Verifies existence of config file, and the values therein.

    The config file should have an iam_id (AWS access key ID), iam_secret (AWS 
    Secret Access Key), and optionally servers_dat (file path for servers.dat).

    The config file is expected under .ec2mc/ under the user's home directory.

    server_titles.json is verified/managed separately by manage_titles.py.

    Returns:
        dict:
            "iam_id": IAM user's access key ID
            "iam_secret": IAM user's secret access key
            "iam_name": IAM user's username
            "iam_arn": IAM user's Amazon Resource Name
            "servers_dat" (optional): Minecraft client's servers.dat file path
    """

    user_info = {}

    config_file = config.CONFIG_DIR + "config"
    if not os.path.isfile(config_file):
        quit_out.q([
            "Configuration is not set. Set with \"ec2mc configure\".", 
            "IAM credentials must be set to access EC2 instances."
        ])
    config_dict = configparser.ConfigParser()
    config_dict.read(config_file)

    user_info.update(verify_user(config_dict))

    if config_dict.has_option("default", "servers_dat"):
        servers_dat = config_dict["default"]["servers_dat"]
        if os.path.isfile(servers_dat) and servers_dat.endswith("servers.dat"):
            user_info["servers_dat"] = servers_dat

    if "servers_dat" not in user_info:
        print("Config doesn't have a valid path for MC client's servers.dat.")
        print("  The Minecraft client's server list will not be updated.")
        print("")

    print("Credentials verified as IAM user \"" + user_info["iam_name"] + "\".")
    return user_info


def verify_user(config_dict):
    """Get IAM user credentials from config and verify them.

    Args:
        config_dict (configparser): IAM user credentials needed.

    Returns:
        dict: 
            "iam_id": IAM user's access key ID
            "iam_secret": IAM user's secret access key
            "iam_name": IAM user's username
            "iam_arn": IAM user's Amazon Resource Name
    """
    user_info = {}

    if not (config_dict.has_option("default", "iam_id") and 
            config_dict.has_option("default", "iam_secret")):
        quit_out.q([
            "Error: Configuration incomplete. Set with \"ec2mc configure\"."])

    user_info["iam_id"] = config_dict["default"]["iam_id"]
    user_info["iam_secret"] = config_dict["default"]["iam_secret"]

    # Test access to iam:GetUser, as SimulatePrincipalPolicy can't be used yet.
    try:
        iam_user = verify_aws.iam_client(user_info).get_user()["User"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidClientTokenId":
            quit_out.q(["Error: IAM ID is invalid."])
        elif e.response["Error"]["Code"] == "SignatureDoesNotMatch":
            quit_out.q(["Error: IAM ID is valid, but its secret is invalid."])
        elif e.response["Error"]["Code"] == "AccessDenied":
            quit_out.assert_empty(["iam:GetUser"])
        quit_out.q([e])

    user_info["iam_name"] = iam_user["UserName"]
    # This right here is what is needed for SimulatePrincipalPolicy.
    user_info["iam_arn"] = iam_user["Arn"] 

    # Meant for testing access to SimulatePrincipalPolicy, rather than GetUser.
    try:
        simulate_policy.blocked(user_info, actions=["iam:GetUser"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            quit_out.assert_empty(["iam:SimulatePrincipalPolicy"])
        quit_out.q([e])

    return user_info
