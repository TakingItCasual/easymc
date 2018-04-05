import os
import json
import shutil

from ec2mc import config
from ec2mc.stuff import quit_out

def main():
    """create aws_setup if nonexistant, update if needed and is unprotected"""
    
    aws_setup_src_dir = os.path.abspath(
        os.path.join(__file__, os.pardir, os.pardir, "aws_setup_src"))

    # If config.AWS_SETUP_DIR nonexistant, copy from ec2mc.aws_setup_src
    if not os.path.isdir(config.AWS_SETUP_DIR):
        cp_aws_setup_to_config(aws_setup_src_dir)

    config_aws_setup_file = config.AWS_SETUP_DIR + "aws_setup.json"
    if not os.path.isfile(config_aws_setup_file):
        quit_out.err(["aws_setup.json not found from config."])
    with open(config_aws_setup_file) as f:
        config_aws_setup = json.loads(f.read())

    source_aws_setup_file = os.path.join(aws_setup_src_dir, "aws_setup.json")
    if not os.path.isfile(source_aws_setup_file):
        quit_out.err(["aws_setup.json not found from distribution."])
    with open(source_aws_setup_file) as f:
        source_aws_setup = json.loads(f.read())

    # The aws_setup in the config must have the "Protect" and "Version" keys
    if not all(key in config_aws_setup for key in ("Protect", "Version")):
        cp_aws_setup_to_config(aws_setup_src_dir)
    # If the "Protect" key has been set to True, prevent overwriting aws_setup
    elif config_aws_setup["Protect"]:
        pass
    # Version can be set to 0 during development for constant refreshing
    elif source_aws_setup["Version"] == 0:
        cp_aws_setup_to_config(aws_setup_src_dir)
    # Update if aws_setup_src has larger version number
    elif source_aws_setup["Version"] > config_aws_setup["Version"]:
        cp_aws_setup_to_config(aws_setup_src_dir)

    if "Namespace" not in config_aws_setup:
        quit_out.err(["Namespace key missing from aws_setup.json in config."])
    config.NAMESPACE = config_aws_setup["Namespace"]

    verify_iam_policies(config_aws_setup)
    verify_vpc_security_groups(config_aws_setup)


def cp_aws_setup_to_config(aws_setup_src_dir):
    if os.path.isdir(config.AWS_SETUP_DIR):
        shutil.rmtree(config.AWS_SETUP_DIR)
    shutil.copytree(aws_setup_src_dir, config.AWS_SETUP_DIR)


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
        sg["Name"] for sg in config_aws_setup["VPC"]["SecurityGroups"]
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
