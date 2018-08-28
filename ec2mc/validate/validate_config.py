import os
from botocore.exceptions import ClientError

from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

def main():
    """validates existence of config file, as well as each key's value"""
    # If config directory doesn't already exist, create it.
    if not os.path.isdir(consts.CONFIG_DIR):
        os.mkdir(consts.CONFIG_DIR)

    # Retrieve the configuration. Halt if it doesn't exist.
    if not os.path.isfile(consts.CONFIG_JSON):
        credentials_csv = f"{consts.CONFIG_DIR}accessKeys.csv"
        if not os.path.isfile(credentials_csv):
            config_base = os.path.basename(consts.CONFIG_JSON)
            halt.err(f"{config_base} not found from config directory.",
                "  An IAM user access key is needed to interact with AWS.",
                "  Set access key with \"ec2mc configure access_key\"."
            )
        create_config_from_credentials_csv(credentials_csv)
    config_dict = os2.parse_json(consts.CONFIG_JSON)

    # Validate config.json adheres to its schema.
    schema = os2.get_json_schema("config")
    os2.validate_dict(config_dict, schema, "config.json")

    # Validate config's IAM user access key.
    validate_user(config_dict)

    # Validate config's region whitelist is valid.
    if 'region_whitelist' in config_dict:
        consts.REGION_WHITELIST = tuple(config_dict['region_whitelist'])
        if len(aws.get_regions()) != len(consts.REGION_WHITELIST):
            halt.err("Following invalid region(s) in config whitelist:",
                *(set(consts.REGION_WHITELIST) - set(aws.get_regions())))

    # Validate server_titles.json adheres to its schema.
    if os.path.isfile(consts.SERVER_TITLES_JSON):
        server_titles_dict = os2.parse_json(consts.SERVER_TITLES_JSON)
        schema = os2.get_json_schema("server_titles")
        os2.validate_dict(server_titles_dict, schema, "server_titles.json")

    print(f"Access key validated as IAM user \"{consts.IAM_NAME}\".")


def validate_user(config_dict):
    """validate config's IAM user access key and minimal permissions

    iam:GetUser, iam:SimulatePrincipalPolicy, iam:GetAccessKeyLastUsed, and 
    ec2:DescribeRegions permissions required for successful validation.

    Args:
        config_dict (dict): Should contain config's IAM user access key.
            'access_key' (dict): IAM user's access key.
                'id' (str): ID of access key ID.
                'secret' (str): Secret access key.
    """
    if 'access_key' not in config_dict:
        halt.err("IAM user access key not set.",
            "  Set with \"ec2mc configure access_key\".")

    consts.IAM_ID = config_dict['access_key']['id']
    consts.IAM_SECRET = config_dict['access_key']['secret']

    # IAM User access key must be validated before validate_perms can be used.
    try:
        iam_user = aws.iam_client().get_user()['User']
    except ClientError as e:
        # TODO: Use client exceptions instead once they're documented
        if e.response['Error']['Code'] == "InvalidClientTokenId":
            halt.err("Access key ID is invalid.")
        elif e.response['Error']['Code'] == "SignatureDoesNotMatch":
            halt.err("Access key ID is valid, but its secret is invalid.")
        elif e.response['Error']['Code'] == "AccessDenied":
            halt.assert_empty(["iam:GetUser"])
        halt.err(str(e))

    # This ARN is needed for iam:SimulatePrincipalPolicy action.
    consts.IAM_ARN = iam_user['Arn']
    consts.IAM_NAME = iam_user['UserName']

    # Validate IAM user can use iam:SimulatePrincipalPolicy action.
    try:
        validate_perms.blocked(actions=["iam:GetUser"])
    except ClientError as e:
        if e.response['Error']['Code'] == "AccessDenied":
            halt.assert_empty(["iam:SimulatePrincipalPolicy"])
        halt.err(str(e))

    # Validate IAM user can use other basic permissions needed for the script
    halt.assert_empty(validate_perms.blocked(actions=[
        "iam:GetAccessKeyLastUsed",
        "ec2:DescribeRegions"
    ]))


def create_config_from_credentials_csv(file_path):
    """create JSON config file from IAM user's credentials.csv file"""
    with open(file_path, encoding="utf-8") as csv_file:
        iam_user_access_key = csv_file.readlines()[1].strip().split(",")
    config_dict = {
        'access_key': {
            'id': iam_user_access_key[0],
            'secret': iam_user_access_key[1]
        }
    }
    os2.save_json(config_dict, consts.CONFIG_JSON)
    os.chmod(consts.CONFIG_JSON, consts.CONFIG_PERMS)
