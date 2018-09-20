import boto3
from botocore.exceptions import ClientError

from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

def main():
    """validates existence of config file, as well as each key's value"""
    # If config directory doesn't already exist, create it.
    consts.CONFIG_DIR.mkdir(exist_ok=True)

    # Retrieve config/credentials file. Halt if neither exist.
    if not consts.CONFIG_JSON.is_file():
        credentials_csv = consts.CONFIG_DIR / "accessKeys.csv"
        if not credentials_csv.is_file():
            config_base = consts.CONFIG_JSON.name
            halt.err(f"{config_base} not found from config directory.",
                "  An IAM user access key is needed to interact with AWS.",
                "  Set access key with \"ec2mc configure access_key\"."
            )
        create_config_from_credentials_csv(credentials_csv)
    config_dict = os2.parse_json(consts.CONFIG_JSON)

    if 'use_handler' not in config_dict:
        config_dict['use_handler'] = True
    consts.USE_HANDLER = config_dict['use_handler']

    # Validate config.json adheres to its schema.
    schema = os2.get_json_schema("config")
    os2.validate_dict(config_dict, schema, "config.json")

    # Validate config's IAM user access key and save to consts.
    validate_user(config_dict)
    # Validate config's region whitelist and save to consts.
    validate_region_whitelist(config_dict)

    print(f"Access key validated as IAM user \"{consts.IAM_NAME}\".")


def validate_user(config_dict):
    """validate config's IAM user access key and minimal permissions

    iam:GetUser, iam:SimulatePrincipalPolicy, iam:GetAccessKeyLastUsed, and
    ec2:DescribeRegions permissions required for successful validation.

    Args:
        config_dict (dict): Should contain config's IAM user access key.
            'access_key' (dict): IAM user's access key.
                Access key ID (str): Secret access key.
    """
    if 'access_key' not in config_dict:
        halt.err("IAM user access key not set.",
            "  Set with \"ec2mc configure access_key\".")

    consts.KEY_ID = next(iter(config_dict['access_key']))
    consts.KEY_SECRET = config_dict['access_key'][consts.KEY_ID]

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


def validate_region_whitelist(config_dict):
    """validate config's region whitelist and save to consts.REGIONS tuple

    Requires ec2:DescribeRegions permission.
    """
    response = boto3.client("ec2",
        aws_access_key_id=consts.KEY_ID,
        aws_secret_access_key=consts.KEY_SECRET,
        region_name="us-east-1"
    ).describe_regions()
    region_names = [region['RegionName'] for region in response['Regions']]

    if 'region_whitelist' not in config_dict:
        halt.err("AWS region whitelist not set.",
            "  Set with \"ec2mc configure whitelist\".")

    whitelist = tuple(config_dict['region_whitelist'])
    if not set(whitelist).issubset(set(region_names)):
        halt.err("Following invalid region(s) in config whitelist:",
            *(set(whitelist) - set(region_names)))
    consts.REGIONS = whitelist


def create_config_from_credentials_csv(file_path):
    """create JSON config file from IAM user's accessKeys.csv file"""
    with file_path.open(encoding="utf-8") as csv_file:
        key_id_and_secret = csv_file.readlines()[1].strip().split(",")
    config_dict = {'access_key': {key_id_and_secret[0]: key_id_and_secret[1]}}

    os2.save_json(config_dict, consts.CONFIG_JSON)
    consts.CONFIG_JSON.chmod(consts.CONFIG_PERMS)
