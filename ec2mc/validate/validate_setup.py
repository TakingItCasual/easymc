import shutil
import filecmp
from pathlib import Path

from ec2mc import consts
from ec2mc.utils import os2
from ec2mc.utils import halt

def main():
    """validate contents of user's config's aws_setup directory"""
    # Directory path for distribution's packaged aws_setup
    src_aws_setup_dir = consts.DIST_DIR / "aws_setup_src"

    # If consts.AWS_SETUP_DIR nonexistant, copy from ec2mc.aws_setup_src
    if not consts.AWS_SETUP_DIR.is_dir():
        _cp_aws_setup_to_config(src_aws_setup_dir)
    config_aws_setup = _get_config_aws_setup_dict()

    # Config's aws_setup.json must contain the 'Modified' key
    if 'Modified' not in config_aws_setup:
        halt.err("'Modified' key missing from aws_setup.json.",
            "  Delete your config's aws_setup folder and it will regenerate.")

    # If 'Modified' key is True, prevent overwriting config's aws_setup
    if config_aws_setup['Modified'] is False:
        cmp_files = os2.recursive_dir_files(src_aws_setup_dir)
        diffs = filecmp.cmpfiles(
            src_aws_setup_dir, consts.AWS_SETUP_DIR, cmp_files, shallow=False)
        # If source and config aws_setup differ, overwrite config aws_setup
        # If config aws_setup missing files, overwrite config aws_setup
        if diffs[1] or diffs[2]:
            _cp_aws_setup_to_config(src_aws_setup_dir)
            print("Config's aws_setup directory updated.")
            config_aws_setup = _get_config_aws_setup_dict()

    consts.NAMESPACE = config_aws_setup['Namespace']
    consts.IAM_PREFIX = f"/{consts.NAMESPACE}/"
    consts.RSA_KEY_PEM = consts.CONFIG_DIR / f"{consts.NAMESPACE}.pem"
    consts.RSA_KEY_PPK = consts.CONFIG_DIR / f"{consts.NAMESPACE}.ppk"

    _validate_iam_policies(config_aws_setup)
    _validate_iam_groups(config_aws_setup)
    _validate_vpc_security_groups(config_aws_setup)
    _validate_instance_templates()


def _get_config_aws_setup_dict():
    """return aws_setup.json from config in user's home dir as dict"""
    if not consts.AWS_SETUP_JSON.is_file():
        halt.err("aws_setup.json not found from config.")

    config_aws_setup = os2.parse_json(consts.AWS_SETUP_JSON)
    schema = os2.get_json_schema("aws_setup")
    os2.validate_dict(config_aws_setup, schema, "aws_setup.json")
    return config_aws_setup


def _cp_aws_setup_to_config(src_aws_setup_dir):
    """delete config aws_setup, then copy source aws_setup to config"""
    if consts.AWS_SETUP_DIR.is_dir():
        shutil.rmtree(consts.AWS_SETUP_DIR, onerror=os2.del_readonly)
    shutil.copytree(src_aws_setup_dir, consts.AWS_SETUP_DIR)


def _validate_iam_policies(config_aws_setup):
    """validate aws_setup.json reflects contents of iam_policies dir"""
    policy_dir = consts.AWS_SETUP_DIR / "iam_policies"

    # Policies described in aws_setup/aws_setup.json
    setup_policy_list = [f"{policy}.json" for policy
        in config_aws_setup['IAM']['Policies']]
    # Actual policy JSON files located in aws_setup/iam_policies/
    iam_policy_files = os2.dir_files(policy_dir, ext=".json")

    # Halt if any IAM policy file contains invalid JSON
    for iam_policy_file in iam_policy_files:
        os2.parse_json(policy_dir / iam_policy_file)

    # Halt if aws_setup.json describes policies not found in iam_policies
    if not set(setup_policy_list).issubset(set(iam_policy_files)):
        halt.err(
            "Following policy(s) not found from aws_setup/iam_policies/:",
            *[policy for policy in setup_policy_list
                if policy not in iam_policy_files]
        )


def _validate_iam_groups(config_aws_setup):
    """validate IAM groups' policies are subsets of described IAM policies"""
    setup_policies = set(config_aws_setup['IAM']['Policies'].keys())
    for name, iam_group in config_aws_setup['IAM']['Groups'].items():
        if not set(iam_group['Policies']).issubset(setup_policies):
            halt.err("aws_setup.json incorrectly formatted:",
                f"IAM group {name} contains following invalid policy(s):",
                *[policy for policy in iam_group['Policies']
                    if policy not in setup_policies])


def _validate_vpc_security_groups(config_aws_setup):
    """validate aws_setup.json reflects contents of vpc_security_groups dir"""
    sg_dir = consts.AWS_SETUP_DIR / "vpc_security_groups"

    # SGs described in aws_setup/aws_setup.json
    setup_sg_list = [f"{sg_name}.json" for sg_name
        in config_aws_setup['VPC']['SecurityGroups']]
    # Actual SG json files located in aws_setup/vpc_security_groups/
    vpc_sg_json_files = os2.dir_files(sg_dir, ext=".json")

    # Halt if aws_setup.json describes SGs not found in sg_dir
    if not set(setup_sg_list).issubset(set(vpc_sg_json_files)):
        halt.err(
            "Following SG(s) not found from aws_setup/vpc_security_groups/:",
            *[sg for sg in setup_sg_list if sg not in vpc_sg_json_files]
        )

    # Halt if any security group missing Ingress key
    schema = os2.get_json_schema("vpc_security_groups")
    for sg_file in vpc_sg_json_files:
        sg_dict = os2.parse_json(sg_dir / sg_file)
        os2.validate_dict(sg_dict, schema, f"SG {sg_file}")


def _validate_instance_templates():
    """validate config aws_setup user_data YAML instance templates"""
    template_yaml_files = os2.dir_files(consts.USER_DATA_DIR, ext=".yaml")

    schema = os2.get_json_schema("instance_templates")
    for template_yaml_file in template_yaml_files:
        template_name = Path(template_yaml_file).stem
        user_data = os2.parse_yaml(consts.USER_DATA_DIR / template_yaml_file)
        os2.validate_dict(user_data, schema, template_yaml_file)

        template_info = user_data['ec2mc_template_info']
        if 'write_directories' not in template_info:
            continue

        for write_dir in template_info['write_directories']:
            dir_path = consts.USER_DATA_DIR.joinpath(*write_dir['local_dir'])
            if not dir_path.is_dir():
                halt.err(f"{dir_path} directory for the {template_name} "
                    "template not found.")
    # write_files path uniqueness validated in create:_process_user_data
