import os.path
import shutil
import filecmp

from ec2mc import config
from ec2mc.utils import os2
from ec2mc.utils import halt

def main():
    """verify contents of user's config's aws_setup directory"""

    # Directory path for distribution's packaged aws_setup
    src_aws_setup_dir = os.path.join((config.DIST_DIR + "aws_setup_src"), "")

    # If config.AWS_SETUP_DIR nonexistant, copy from ec2mc.aws_setup_src
    if not os.path.isdir(config.AWS_SETUP_DIR):
        cp_aws_setup_to_config(src_aws_setup_dir)
    config_aws_setup = get_config_aws_setup_dict()

    # Config's aws_setup.json must have "Modified" and "Namespace" keys
    if not all(key in config_aws_setup for key in ("Modified", "Namespace")):
        cp_aws_setup_to_config(src_aws_setup_dir)
        config_aws_setup = get_config_aws_setup_dict()

    # If "Modified" key is True, prevent overwriting config's aws_setup
    if not config_aws_setup["Modified"]:
        files_to_compare = os2.list_files_with_sub_dirs(src_aws_setup_dir)
        diff = filecmp.cmpfiles(src_aws_setup_dir, config.AWS_SETUP_DIR,
            files_to_compare, shallow=False)
        # If source and config aws_setup differ, overwrite config aws_setup
        # If config aws_setup missing files, overwrite config aws_setup
        if diff[1] or diff[2]:
            cp_aws_setup_to_config(src_aws_setup_dir)
            config_aws_setup = get_config_aws_setup_dict()

    verify_aws_setup(config_aws_setup)
    verify_instance_templates(config_aws_setup)

    config.NAMESPACE = config_aws_setup["Namespace"]

    verify_iam_policies(config_aws_setup)
    verify_vpc_security_groups(config_aws_setup)


def get_config_aws_setup_dict():
    """return aws_setup.json from config in user's home dir as dict"""
    config_aws_setup_file = config.AWS_SETUP_JSON
    if not os.path.isfile(config_aws_setup_file):
        halt.err(["aws_setup.json not found from config."])
    return os2.parse_json(config_aws_setup_file)


def cp_aws_setup_to_config(src_aws_setup_dir):
    """delete config aws_setup, then copy source aws_setup to config"""
    if os.path.isdir(config.AWS_SETUP_DIR):
        shutil.rmtree(config.AWS_SETUP_DIR)
    shutil.copytree(src_aws_setup_dir, config.AWS_SETUP_DIR)


def verify_aws_setup(config_aws_setup):
    """verify config's aws_setup.json"""
    schema = os2.get_json_schema("aws_setup")
    os2.validate_dict(config_aws_setup, schema, "aws_setup.json")

    # TODO: Handle this with jsonschema once it's able to
    if not unique_names(config_aws_setup["IAM"]["Policies"]):
        halt.err(["aws_setup.json incorrectly formatted:",
            "IAM policy names must be unique."])
    if not unique_names(config_aws_setup["IAM"]["Groups"]):
        halt.err(["aws_setup.json incorrectly formatted:",
            "IAM group names must be unique."])
    if not unique_names(config_aws_setup["EC2"]["SecurityGroups"]):
        halt.err(["aws_setup.json incorrectly formatted:",
            "EC2 security group names must be unique."])


def verify_instance_templates(config_aws_setup):
    """verify config aws_setup user_data YAML instance templates"""
    template_yaml_files = os2.list_dir_files(config.USER_DATA_DIR, ext=".yaml")

    schema = os2.get_json_schema("instance_templates")
    sg_names = [sg["Name"] for sg in config_aws_setup["EC2"]["SecurityGroups"]]
    for template_yaml_file in template_yaml_files:
        user_data = os2.parse_yaml(config.USER_DATA_DIR + template_yaml_file)
        os2.validate_dict(user_data, schema, template_yaml_file)

        template_info = user_data["ec2mc_template_info"]
        # Verify template security group(s) also described in aws_setup.json
        for security_group in template_info["security_groups"]:
            if security_group not in sg_names:
                halt.err([template_yaml_file + " incorrectly formatted:",
                    "SG " + security_group + " not found in aws_setup.json."])

        template_name = os.path.splitext(template_yaml_file)[0]
        template_dir = os.path.join((config.USER_DATA_DIR + template_name), "")
        # If write_directories not empty, verify template directory exists
        if not os.path.isdir(template_dir):
            if ("write_directories" in template_info
                    and template_info["write_directories"]):
                halt.err([template_name + " template directory not found."])
        # Verify existance of write_directories subdir(s) in template directory
        else:
            template_subdirs = os2.list_dir_dirs(template_dir)
            if "write_directories" in template_info:
                for write_dir in template_info["write_directories"]:
                    if write_dir["local_dir"] not in template_subdirs:
                        halt.err([write_dir["local_dir"] + " subdirectory not "
                            "found from user_data."])
    # write_files path uniqueness verified in create_server:process_user_data


def verify_iam_policies(config_aws_setup):
    """verify aws_setup.json reflects contents of iam_policies dir"""
    policy_dir = os.path.join((config.AWS_SETUP_DIR + "iam_policies"), "")

    # Policies described in aws_setup/aws_setup.json
    setup_policy_list = [policy["Name"] + ".json" for policy
        in config_aws_setup["IAM"]["Policies"]]
    # Actual policy JSON files located in aws_setup/iam_policies/
    iam_policy_files = os2.list_dir_files(policy_dir, ext=".json")

    # Halt if aws_setup.json describes policies not found in iam_policies
    if not set(setup_policy_list).issubset(set(iam_policy_files)):
        halt.err([
            "Following policy(s) not found from aws_setup/iam_policies/:",
            *[policy for policy in setup_policy_list
                if policy not in iam_policy_files]
        ])

    # Warn if iam_policies has policies not described by aws_setup.json
    if not set(iam_policy_files).issubset(set(setup_policy_list)):
        print("Warning: Unused policy(s) found from iam_policies dir.")


def verify_vpc_security_groups(config_aws_setup):
    """verify aws_setup.json reflects contents of vpc_security_groups dir"""
    sg_dir = os.path.join((config.AWS_SETUP_DIR + "vpc_security_groups"), "")

    # SGs described in aws_setup/aws_setup.json
    setup_sg_list = [sg["Name"] + ".json" for sg
        in config_aws_setup["EC2"]["SecurityGroups"]]
    # Actual SG json files located in aws_setup/vpc_security_groups/
    vpc_sg_json_files = os2.list_dir_files(sg_dir, ext=".json")

    # Halt if aws_setup.json describes SGs not found in vpc_security_groups
    if not set(setup_sg_list).issubset(set(vpc_sg_json_files)):
        halt.err([
            "Following SG(s) not found from aws_setup/vpc_security_groups/:",
            *[sg for sg in setup_sg_list
                if sg not in vpc_sg_json_files]
        ])

    # Halt if any security group missing Ingress and/or Egress tags
    schema = os2.get_json_schema("vpc_security_groups")
    for sg_file in vpc_sg_json_files:
        sg_dict = os2.parse_json(sg_dir + sg_file)
        os2.validate_dict(sg_dict, schema, "SG " + sg_file)

    # Warn if vpc_security_groups has SGs not described by aws_setup.json
    if not set(vpc_sg_json_files).issubset(set(setup_sg_list)):
        print("Warning: Unused SG(s) found from vpc_security_groups dir.")


def unique_names(dict_list):
    """verify each Name key value is unique within list of dicts"""
    names = [list_dict["Name"] for list_dict in dict_list]
    if len(names) != len(set(names)):
        return False
    return True
