import os.path
import shutil
import filecmp

from ec2mc import consts
from ec2mc.utils import os2
from ec2mc.utils import halt

# TODO: Validate local AWS setup against AWS (e.g. template SG(s))
def main():
    """validate contents of user's config's aws_setup directory"""
    # Directory path for distribution's packaged aws_setup
    src_aws_setup_dir = os.path.join(f"{consts.DIST_DIR}aws_setup_src", "")

    # If consts.AWS_SETUP_DIR nonexistant, copy from ec2mc.aws_setup_src
    if not os.path.isdir(consts.AWS_SETUP_DIR):
        cp_aws_setup_to_config(src_aws_setup_dir)
    config_aws_setup = get_config_aws_setup_dict()

    # Config's aws_setup.json must contain the 'Modified' key
    if 'Modified' not in config_aws_setup:
        halt.err("'Modified' key missing from aws_setup.json.",
            "  Delete your config's aws_setup folder and it will regenerate.")

    # If 'Modified' key is True, prevent overwriting config's aws_setup
    if config_aws_setup['Modified'] is False:
        files_to_compare = os2.list_files_with_sub_dirs(src_aws_setup_dir)
        diff = filecmp.cmpfiles(src_aws_setup_dir, consts.AWS_SETUP_DIR,
            files_to_compare, shallow=False)
        # If source and config aws_setup differ, overwrite config aws_setup
        # If config aws_setup missing files, overwrite config aws_setup
        if diff[1] or diff[2]:
            cp_aws_setup_to_config(src_aws_setup_dir)
            config_aws_setup = get_config_aws_setup_dict()

    validate_aws_setup(config_aws_setup)

    consts.NAMESPACE = config_aws_setup['Namespace']
    consts.RSA_PRIV_KEY_PEM = f"{consts.CONFIG_DIR}{consts.NAMESPACE}.pem"

    validate_iam_policies(config_aws_setup)
    validate_iam_groups(config_aws_setup)
    validate_instance_templates(config_aws_setup)
    validate_vpc_security_groups(config_aws_setup)


def get_config_aws_setup_dict():
    """return aws_setup.json from config in user's home dir as dict"""
    if not os.path.isfile(consts.AWS_SETUP_JSON):
        halt.err("aws_setup.json not found from config.")
    return os2.parse_json(consts.AWS_SETUP_JSON)


def cp_aws_setup_to_config(src_aws_setup_dir):
    """delete config aws_setup, then copy source aws_setup to config"""
    if os.path.isdir(consts.AWS_SETUP_DIR):
        shutil.rmtree(consts.AWS_SETUP_DIR)
    shutil.copytree(src_aws_setup_dir, consts.AWS_SETUP_DIR)


def validate_aws_setup(config_aws_setup):
    """validate config's aws_setup.json"""
    schema = os2.get_json_schema("aws_setup")
    os2.validate_dict(config_aws_setup, schema, "aws_setup.json")


def validate_iam_policies(config_aws_setup):
    """validate aws_setup.json reflects contents of iam_policies dir"""
    policy_dir = os.path.join(f"{consts.AWS_SETUP_DIR}iam_policies", "")

    # Policies described in aws_setup/aws_setup.json
    setup_policy_list = [f"{policy}.json" for policy
        in config_aws_setup['IAM']['Policies']]
    # Actual policy JSON files located in aws_setup/iam_policies/
    iam_policy_files = os2.list_dir_files(policy_dir, ext=".json")

    # Halt if any IAM policy file contains invalid JSON
    for iam_policy_file in iam_policy_files:
        os2.parse_json(f"{policy_dir}{iam_policy_file}")

    # Halt if aws_setup.json describes policies not found in iam_policies
    if not set(setup_policy_list).issubset(set(iam_policy_files)):
        halt.err(
            "Following policy(s) not found from aws_setup/iam_policies/:",
            *[policy for policy in setup_policy_list
                if policy not in iam_policy_files]
        )


def validate_iam_groups(config_aws_setup):
    """validate IAM groups' policies are subsets of described IAM policies"""
    setup_policies = set(config_aws_setup['IAM']['Policies'].keys())
    for name, iam_group in config_aws_setup['IAM']['Groups'].items():
        if not set(iam_group['Policies']).issubset(setup_policies):
            halt.err("aws_setup.json incorrectly formatted:",
                f"IAM group {name} contains following invalid policy(s):",
                *[policy for policy in iam_group['Policies']
                    if policy not in setup_policies])


def validate_instance_templates(config_aws_setup):
    """validate config aws_setup user_data YAML instance templates"""
    template_yaml_files = os2.list_dir_files(consts.USER_DATA_DIR, ext=".yaml")

    schema = os2.get_json_schema("instance_templates")
    sg_names = [sg for sg in config_aws_setup['VPC']['SecurityGroups']]
    for template_yaml_file in template_yaml_files:
        user_data = os2.parse_yaml(
            f"{consts.USER_DATA_DIR}{template_yaml_file}")
        os2.validate_dict(user_data, schema, template_yaml_file)

        template_info = user_data['ec2mc_template_info']
        # Validate template security group(s) also described in aws_setup.json
        for security_group in template_info['security_groups']:
            if security_group not in sg_names:
                halt.err(f"{template_yaml_file} incorrectly formatted:",
                    f"SG {security_group} not found in aws_setup.json.")

        template_name = os.path.splitext(template_yaml_file)[0]
        template_dir = os.path.join(
            f"{consts.USER_DATA_DIR}{template_name}", "")
        # If write_directories in template, validate template directory exists
        if not os.path.isdir(template_dir):
            if 'write_directories' in template_info:
                halt.err(f"{template_name} template's directory not found.")
        # Validate template's subdirectories exist
        else:
            template_subdirs = os2.list_dir_dirs(template_dir)
            if 'write_directories' in template_info:
                for write_dir in template_info['write_directories']:
                    if write_dir['local_dir'] not in template_subdirs:
                        halt.err(f"{template_name} template's "
                            f"{write_dir['local_dir']} subdir not found.")
    # write_files path uniqueness validated in create:process_user_data


def validate_vpc_security_groups(config_aws_setup):
    """validate aws_setup.json reflects contents of vpc_security_groups dir"""
    sg_dir = os.path.join(f"{consts.AWS_SETUP_DIR}vpc_security_groups", "")

    # SGs described in aws_setup/aws_setup.json
    setup_sg_list = [f"{sg_name}.json" for sg_name
        in config_aws_setup['VPC']['SecurityGroups']]
    # Actual SG json files located in aws_setup/vpc_security_groups/
    vpc_sg_json_files = os2.list_dir_files(sg_dir, ext=".json")

    # Halt if aws_setup.json describes SGs not found in vpc_security_groups
    if not set(setup_sg_list).issubset(set(vpc_sg_json_files)):
        halt.err(
            "Following SG(s) not found from aws_setup/vpc_security_groups/:",
            *[sg for sg in setup_sg_list if sg not in vpc_sg_json_files]
        )

    # Halt if any security group missing Ingress key
    schema = os2.get_json_schema("vpc_security_groups")
    for sg_file in vpc_sg_json_files:
        sg_dict = os2.parse_json(f"{sg_dir}{sg_file}")
        os2.validate_dict(sg_dict, schema, f"SG {sg_file}")
