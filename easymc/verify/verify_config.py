import os
import configparser
import boto3
from botocore.exceptions import ClientError

import constants
from stuff import simulate_policy
from stuff import quit_out

def main():
    """Verifies existence of client's servers.dat and IAM credentials csv.

    Not being able to find servers.dat results in a warning, not being able to
    find the IAM credentials results in an error.

    server_titles.json is verified/managed by manage_titles.py

    Returns:
        dict:
            "iam_id": IAM user's access key ID
            "iam_secret": IAM user's secret access key
            "iam_name": IAM user's username
            "iam_arn": IAM user's Amazon Resource Name
            "servers_dat" (optional): Minecraft client's servers.dat file path
    """

    user_info = {}

    config_file = constants.config_folder + "config"
    if not os.path.isfile(config_file):
        quit_out.q([
            "Configuration is not set. Set with \"easymc configure\".", 
            "IAM credentials must be set to access EC2 instances."
        ])
    config_dict = configparser.ConfigParser()
    config_dict.read(config_file)

    user_info.update(verify_user(config_dict))

    if config_dict.has_option("default", "servers_dat"):
        if os.path.isfile(config_dict["default"]["servers_dat"]):
            user_info["servers_dat"] = config_dict["default"]["servers_dat"]

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
            "Error: Configuration incomplete. Set with \"easymc configure\"."])

    user_info["iam_id"] = config_dict["default"]["iam_id"]
    user_info["iam_secret"] = config_dict["default"]["iam_secret"]

    # Can't verify access to GetUser, as user's ARN is needed for verification
    try:
        iam_user = boto3.client("iam", 
            aws_access_key_id=user_info["iam_id"], 
            aws_secret_access_key=user_info["iam_secret"]
        ).get_user()["User"]
    except ClientError as e:
        print(e.response)
        if e.response["Error"]["Code"] == "InvalidClientTokenId":
            quit_out.q(["Error: IAM ID is invalid."])
        elif e.response["Error"]["Code"] == "SignatureDoesNotMatch":
            quit_out.q(["Error: IAM ID is valid, but its secret is invalid."])
        elif e.response["Error"]["Code"] == "AccessDenied":
            quit_out.assert_empty(["iam:GetUser"])

    user_info["iam_name"] = iam_user["UserName"]
    user_info["iam_arn"] = iam_user["Arn"]

    # Meant for testing access to SimulatePrincipalPolicy, rather than GetUser
    try:
        simulate_policy.blocked(user_info, actions=["iam:GetUser"])
    except ClientError:
        quit_out.assert_empty(["iam:SimulatePrincipalPolicy"])

    return user_info


def create_configuration():
    """User can set their IAM credentials and servers.dat file path here."""
    if not os.path.isdir(constants.config_folder):
        os.mkdir(constants.config_folder)

    iam_id_str = "None"
    iam_secret_str = "None"
    servers_dat_str = "None"

    config_dict = configparser.ConfigParser()
    config_dict["default"] = {}

    config_file = os.path.join(constants.config_folder, "config")
    if os.path.isfile(config_file):
        config_dict.read(config_file)
        if config_dict.has_option("default", "iam_id"):
            iam_id_str = "*"*16 + config_dict["default"]["iam_id"][-4:]
        if config_dict.has_option("default", "iam_secret"):
            iam_secret_str = "*"*16 + config_dict["default"]["iam_secret"][-4:]
        if config_dict.has_option("default", "servers_dat"):
            servers_dat_str = config_dict["default"]["servers_dat"]

    iam_id = input("AWS Access Key ID [" + iam_id_str + "]: ")
    iam_secret = input("AWS Secret Access Key [" + iam_secret_str + "]: ")
    servers_dat = input(
        "File path for Minecraft's servers.dat [" + servers_dat_str + "]: ")

    while servers_dat and not os.path.isfile(servers_dat):
        servers_dat = input(
            servers_dat + " does not exist, try again or leave empty: ")

    if iam_id:
        config_dict["default"]["iam_id"] = iam_id
    if iam_secret:
        config_dict["default"]["iam_secret"] = iam_secret
    if servers_dat:
        config_dict["default"]["servers_dat"] = servers_dat

    with open(config_file, "w") as output:
        config_dict.write(output)
