import os
import shutil
import filecmp
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ec2mc import config
from ec2mc.stuff import quit_out

def main():
    """create aws_setup if nonexistant, update if needed and is unmodified"""

    # Directory path for the distribution's packaged aws_setup
    src_aws_setup_dir = os.path.abspath(
        os.path.join(__file__, os.pardir, os.pardir, "aws_setup_src"))

    # If config.AWS_SETUP_DIR nonexistant, copy from ec2mc.aws_setup_src
    if not os.path.isdir(config.AWS_SETUP_DIR):
        cp_aws_setup_to_config(src_aws_setup_dir)
    config_aws_setup = get_config_dict()

    # The config's aws_setup.json must have the "Modified" and "Namespace" keys
    if not all(key in config_aws_setup for key in ("Modified", "Namespace")):
        cp_aws_setup_to_config(src_aws_setup_dir)
        config_aws_setup = get_config_dict()

    # If "Modified" key is True, prevent overwriting config's aws_setup
    if not config_aws_setup["Modified"]:
        diff = filecmp.cmpfiles(src_aws_setup_dir, config.AWS_SETUP_DIR, [
            "aws_setup.json",
            "iam_policies/admin_permissions.json",
            "iam_policies/basic_permissions.json",
            "vpc_security_groups/ec2mc_sg.json"
        ], shallow=False)
        # If source and config aws_setup differ, overwrite config aws_setup
        # If comparison fails (missing files?), overwrite config aws_setup
        if diff[1] or diff[2]:
            cp_aws_setup_to_config(src_aws_setup_dir)
            config_aws_setup = get_config_dict()

    verify_json_schema(config_aws_setup)

    config.NAMESPACE = config_aws_setup["Namespace"]

    verify_iam_policies(config_aws_setup)
    verify_vpc_security_groups(config_aws_setup)


def get_config_dict():
    """returns aws_setup.json from config in user's home dir as dict"""
    config_aws_setup_file = config.AWS_SETUP_JSON
    if not os.path.isfile(config_aws_setup_file):
        quit_out.err(["aws_setup.json not found from config."])
    return quit_out.parse_json(config_aws_setup_file)


def cp_aws_setup_to_config(src_aws_setup_dir):
    if os.path.isdir(config.AWS_SETUP_DIR):
        shutil.rmtree(config.AWS_SETUP_DIR)
    shutil.copytree(src_aws_setup_dir, config.AWS_SETUP_DIR)


def verify_json_schema(config_aws_setup):
    schema = quit_out.parse_json(os.path.abspath(
        os.path.join(__file__, os.pardir, "aws_setup_schema.json")))
    try:
        validate(config_aws_setup, schema)
    except ValidationError as e:
        quit_out.err(["aws_setup.json is incorrectly formatted:"] +
            [str(e).split("\n\n")[0]])

    # TODO: Handle this with jsonschema once it's able to
    if not unique_names(config_aws_setup["IAM"]["Policies"]):
        quit_out.err(["aws_setup.json is incorrectly formatted:",
            "IAM policy names must be unique."])
    if not unique_names(config_aws_setup["IAM"]["Groups"]):
        quit_out.err(["aws_setup.json is incorrectly formatted:",
            "IAM group names must be unique."])
    if not unique_names(config_aws_setup["EC2"]["SecurityGroups"]):
        quit_out.err(["aws_setup.json is incorrectly formatted:",
            "EC2 security group names must be unique."])


def verify_iam_policies(config_aws_setup):
    """verify aws_setup.json reflects contents of iam_policies dir"""
    policy_dir = os.path.join((config.AWS_SETUP_DIR + "iam_policies"), "")

    # Policies described in aws_setup/aws_setup.json
    setup_policy_list = [
        policy["Name"] for policy in config_aws_setup["IAM"]["Policies"]
    ]
    # Actual policy json files located in aws_setup/iam_policies/
    iam_policy_files = [
        json_file[:-5] for json_file in os.listdir(policy_dir)
            if json_file.endswith(".json")
    ]

    # Quit if aws_setup.json describes policies not found in iam_policies
    if not set(setup_policy_list).issubset(set(iam_policy_files)):
        quit_out.err([
            "Following policy(s) not found from iam_policies dir:",
            *[(policy + ".json") for policy in setup_policy_list
                if policy not in iam_policy_files]
        ])

    # Warn if iam_policies has policies not described by aws_setup.json
    if not set(iam_policy_files).issubset(set(setup_policy_list)):
        print("Warning: Unused policy(s) found from iam_policies dir.")


def verify_vpc_security_groups(config_aws_setup):
    """verify aws_setup.json reflects contents of vpc_security_groups dir"""
    sg_dir = os.path.join((config.AWS_SETUP_DIR + "vpc_security_groups"), "")

    # SGs described in aws_setup/aws_setup.json
    setup_sg_list = [
        sg["Name"] for sg in config_aws_setup["EC2"]["SecurityGroups"]
    ]
    # Actual SG json files located in aws_setup/vpc_security_groups/
    vpc_sg_files = [
        json_file[:-5] for json_file in os.listdir(sg_dir)
            if json_file.endswith(".json")
    ]

    # Quit if aws_setup.json describes SGs not found in vpc_security_groups
    if not set(setup_sg_list).issubset(set(vpc_sg_files)):
        quit_out.err([
            "Following SG(s) not found from vpc_security_groups dir:",
            *[(sg + ".json") for sg in setup_sg_list
                if sg not in vpc_sg_files]
        ])

    # Warn if vpc_security_groups has SGs not described by aws_setup.json
    if not set(vpc_sg_files).issubset(set(setup_sg_list)):
        print("Warning: Unused SG(s) found from vpc_security_groups dir.")


def unique_names(dict_list):
    names = [list_dict["Name"] for list_dict in dict_list]
    if len(names) != len(set(names)):
        return False
    return True
