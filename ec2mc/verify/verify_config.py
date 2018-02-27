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
    IAM_ID, IAM_SECRET, IAM_ARN, IAM_NAME, and (optionally) SERVERS_DAT from 
    ec2mc.config will be modified by this function.

    The config file is expected under .ec2mc/ under the user's home directory.

    server_titles.json is verified/managed separately by manage_titles.py.
    """

    config_file = config.CONFIG_DIR + "config"
    if not os.path.isfile(config_file):
        quit_out.q([
            "Configuration is not set. Set with \"ec2mc configure\".", 
            "IAM credentials must be set to access EC2 instances."
        ])
    config_dict = configparser.ConfigParser()
    config_dict.read(config_file)

    verify_user(config_dict)

    if config_dict.has_option("default", "servers_dat"):
        servers_dat = config_dict["default"]["servers_dat"]
        if os.path.isfile(servers_dat) and servers_dat.endswith("servers.dat"):
            config.SERVERS_DAT = servers_dat

    if config.SERVERS_DAT is None:
        print("Config doesn't have a valid path for MC client's servers.dat.")
        print("  The Minecraft client's server list will not be updated.")
        print("")

    print("Credentials verified as IAM user \"" + config.IAM_NAME + "\".")


def verify_user(config_dict):
    """Get IAM user credentials from config and verify them.

    IAM_ID, IAM_SECRET, IAM_ARN, and IAM_NAME from ec2mc.config will be 
    modified by this function.

    Args:
        config_dict (configparser): IAM user credentials needed.
    """

    if not (config_dict.has_option("default", "iam_id") and 
            config_dict.has_option("default", "iam_secret")):
        quit_out.q([
            "Error: Configuration incomplete. Set with \"ec2mc configure\"."])

    config.IAM_ID = config_dict["default"]["iam_id"]
    config.IAM_SECRET = config_dict["default"]["iam_secret"]

    # Test access to iam:GetUser, as SimulatePrincipalPolicy can't be used yet.
    try:
        iam_user = verify_aws.iam_client().get_user()["User"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidClientTokenId":
            quit_out.q(["Error: IAM ID is invalid."])
        elif e.response["Error"]["Code"] == "SignatureDoesNotMatch":
            quit_out.q(["Error: IAM ID is valid, but its secret is invalid."])
        elif e.response["Error"]["Code"] == "AccessDenied":
            quit_out.assert_empty(["iam:GetUser"])
        quit_out.q([e])

    # This ARN is what is needed for SimulatePrincipalPolicy.
    config.IAM_ARN = iam_user["Arn"]
    config.IAM_NAME = iam_user["UserName"]

    # Meant for testing access to SimulatePrincipalPolicy, rather than GetUser.
    try:
        simulate_policy.blocked(actions=["iam:GetUser"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            quit_out.assert_empty(["iam:SimulatePrincipalPolicy"])
        quit_out.q([e])
