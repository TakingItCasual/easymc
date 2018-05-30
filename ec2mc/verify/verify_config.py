import os
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.stuff import aws
from ec2mc.stuff import os2
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import halt

def main():
    """verifies existence of config file, and the values therein

    The config file is expected within config.CONFIG_DIR

    The config file should have an iam_id (AWS access key ID), iam_secret 
    (AWS Secret Access Key), and optionally servers_dat (file path for 
    servers.dat). IAM_ID, IAM_SECRET, IAM_ARN, IAM_NAME, and (optionally) 
    SERVERS_DAT from ec2mc.config will be modified by this function.
    """

    # If config directory doesn't already exist, create it.
    if not os.path.isdir(config.CONFIG_DIR):
        os.mkdir(config.CONFIG_DIR)

    # Retrieve the configuration. Halt if it doesn't exist.
    if not os.path.isfile(config.CONFIG_JSON):
        halt.err([
            "Configuration is not set. Set with \"ec2mc configure\".",
            "  IAM credentials needed to interact with AWS."
        ])
    config_dict = os2.parse_json(config.CONFIG_JSON)

    # Verify config.json adheres to its schema.
    schema = os2.get_json_schema("config")
    os2.validate_dict(config_dict, schema, "config.json")

    # Verify config's region whitelist is valid.
    if "region_whitelist" in config_dict:
        config.REGION_WHITELIST = config_dict["region_whitelist"]
        if len(aws.get_regions()) != len(config.REGION_WHITELIST):
            halt.err(["Following invalid region(s) in config whitelist:",
                *(set(config.REGION_WHITELIST) - set(aws.get_regions()))])

    # Assign config.SERVERS_DAT if config's servers.dat path is valid.
    if "servers_dat" in config_dict:
        servers_dat = config_dict["servers_dat"]
        if os.path.isfile(servers_dat) and servers_dat.endswith("servers.dat"):
            config.SERVERS_DAT = servers_dat

    # Verify server_titles.json adheres to its schema.
    if os.path.isfile(config.SERVER_TITLES_JSON):
        server_titles_dict = os2.parse_json(config.SERVER_TITLES_JSON)
        schema = os2.get_json_schema("server_titles")
        os2.validate_dict(server_titles_dict, schema, "server_titles.json")

    # Verify configuration's IAM user credentials.
    verify_user(config_dict)

    if config.SERVERS_DAT is None:
        print("Config doesn't have a valid path for MC client's servers.dat.")
        print("  The Minecraft client's server list will not be updated.")
        print("")

    print("Credentials verified as IAM user \"" + config.IAM_NAME + "\".")


def verify_user(config_dict):
    """get IAM user credentials from config and verify them

    IAM_ID, IAM_SECRET, IAM_ARN, and IAM_NAME from ec2mc.config will be 
    modified by this function.

    Args:
        config_dict (configparser): IAM user credentials needed.
    """

    if "iam_id" not in config_dict or "iam_secret" not in config_dict:
        halt.err(["Configuration incomplete. Set with \"ec2mc configure\"."])

    config.IAM_ID = config_dict["iam_id"]
    config.IAM_SECRET = config_dict["iam_secret"]

    # Test access to iam:GetUser, as SimulatePrincipalPolicy can't be used yet.
    try:
        iam_user = aws.iam_client().get_user()["User"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidClientTokenId":
            halt.err(["IAM ID is invalid."])
        elif e.response["Error"]["Code"] == "SignatureDoesNotMatch":
            halt.err(["IAM ID is valid, but its secret is invalid."])
        elif e.response["Error"]["Code"] == "AccessDenied":
            halt.assert_empty(["iam:GetUser"])
        halt.err([str(e)])

    # This ARN is what is needed for SimulatePrincipalPolicy.
    config.IAM_ARN = iam_user["Arn"]
    config.IAM_NAME = iam_user["UserName"]

    # Meant for testing access to SimulatePrincipalPolicy, rather than GetUser.
    try:
        simulate_policy.blocked(actions=["iam:GetUser"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            halt.assert_empty(["iam:SimulatePrincipalPolicy"])
        halt.err([str(e)])
