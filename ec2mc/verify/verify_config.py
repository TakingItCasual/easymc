import os
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.verify import verify_perms

def main():
    """verifies existence of config file, as well as each key's value"""

    # If config directory doesn't already exist, create it.
    if not os.path.isdir(config.CONFIG_DIR):
        os.mkdir(config.CONFIG_DIR)

    # Retrieve the configuration. Halt if it doesn't exist.
    if not os.path.isfile(config.CONFIG_JSON):
        halt.err(
            "Configuration is not set. Set with \"ec2mc configure\".",
            "  IAM credentials needed to interact with AWS."
        )
    config_dict = os2.parse_json(config.CONFIG_JSON)

    # Verify config.json adheres to its schema.
    schema = os2.get_json_schema("config")
    os2.validate_dict(config_dict, schema, "config.json")

    # Assign config.SERVERS_DAT if config's servers.dat path is valid.
    if "servers_dat" in config_dict:
        servers_dat = config_dict["servers_dat"]
        if os.path.isfile(servers_dat) and servers_dat.endswith("servers.dat"):
            config.SERVERS_DAT = servers_dat

    # Verify config's IAM user credentials.
    verify_user(config_dict)

    # Verify config's region whitelist is valid.
    if "region_whitelist" in config_dict and config_dict["region_whitelist"]:
        config.REGION_WHITELIST = tuple(config_dict["region_whitelist"])
        if len(aws.get_regions()) != len(config.REGION_WHITELIST):
            halt.err("Following invalid region(s) in config whitelist:",
                *(set(config.REGION_WHITELIST) - set(aws.get_regions())))

    # Verify server_titles.json adheres to its schema.
    if os.path.isfile(config.SERVER_TITLES_JSON):
        server_titles_dict = os2.parse_json(config.SERVER_TITLES_JSON)
        schema = os2.get_json_schema("server_titles")
        os2.validate_dict(server_titles_dict, schema, "server_titles.json")

    if config.SERVERS_DAT is None:
        print("Config doesn't have a valid path for MC client's servers.dat.")
        print("  The Minecraft client's server list will not be updated.")
        print("")
    print("Credentials verified as IAM user \"" + config.IAM_NAME + "\".")


def verify_user(config_dict):
    """verify config's IAM user credentials and minimal permissions

    iam:GetUser, iam:SimulatePrincipalPolicy, and ec2:DescribeRegions 
    permissions required for successful verification.

    Args:
        config_dict (dict): Should contain config's IAM user credentials.
            "iam_id" (str): IAM user's access key ID
            "iam_secret" (str): IAM user's secret access key
    """

    if "iam_id" not in config_dict:
        halt.err("IAM user ID not set. Set with \"ec2mc configure\".")
    if "iam_secret" not in config_dict:
        halt.err("IAM user secret not set. Set with \"ec2mc configure\".")

    config.IAM_ID = config_dict["iam_id"]
    config.IAM_SECRET = config_dict["iam_secret"]

    # IAM User must be validated before permission verification can be done.
    try:
        iam_user = aws.iam_client().get_user()["User"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidClientTokenId":
            halt.err("IAM ID is invalid.")
        elif e.response["Error"]["Code"] == "SignatureDoesNotMatch":
            halt.err("IAM ID is valid, but its secret is invalid.")
        elif e.response["Error"]["Code"] == "AccessDenied":
            halt.assert_empty(["iam:GetUser"])
        halt.err(str(e))

    # This ARN is needed for iam:SimulatePrincipalPolicy action.
    config.IAM_ARN = iam_user["Arn"]
    config.IAM_NAME = iam_user["UserName"]

    # Verify IAM user can use iam:SimulatePrincipalPolicy action.
    try:
        verify_perms.blocked(actions=["iam:GetUser"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            halt.assert_empty(["iam:SimulatePrincipalPolicy"])
        halt.err(str(e))

    # Verify IAM user can use ec2:DescribeRegions action.
    halt.assert_empty(verify_perms.blocked(actions=["ec2:DescribeRegions"]))
