import os
import shutil
import filecmp
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ec2mc import config
from ec2mc.stuff import quit_out

def main():
    """verify contents of user's config's aws_setup directory"""

    # Directory path for distribution's packaged aws_setup
    src_aws_setup_dir = os.path.abspath(
        os.path.join(__file__, os.pardir, os.pardir, "aws_setup_src"))
    # Why do I need to do this?
    src_aws_setup_dir = os.path.join(src_aws_setup_dir, "")

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
        files_to_compare = list_files_with_sub_dirs(src_aws_setup_dir)
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
    verify_user_data_files()


def get_config_aws_setup_dict():
    """return aws_setup.json from config in user's home dir as dict"""
    config_aws_setup_file = config.AWS_SETUP_JSON
    if not os.path.isfile(config_aws_setup_file):
        quit_out.err(["aws_setup.json not found from config."])
    return quit_out.parse_json(config_aws_setup_file)


def get_config_instance_templates_dict():
    """return instance_templates.json from config in user's home dir as dict"""
    config_instance_templates_file = config.INSTANCE_TEMPLATES_JSON
    if not os.path.isfile(config_instance_templates_file):
        quit_out.err(["instance_templates.json not found from config."])
    return quit_out.parse_json(config_instance_templates_file)


def cp_aws_setup_to_config(src_aws_setup_dir):
    """delete config aws_setup, then copy source aws_setup to config"""
    if os.path.isdir(config.AWS_SETUP_DIR):
        shutil.rmtree(config.AWS_SETUP_DIR)
    shutil.copytree(src_aws_setup_dir, config.AWS_SETUP_DIR)


def verify_aws_setup(config_aws_setup):
    """verify config's aws_setup.json"""
    schema = quit_out.parse_json(os.path.abspath(os.path.join(
        __file__, os.pardir, "jsonschemas", "aws_setup_schema.json")))
    try:
        validate(config_aws_setup, schema)
    except ValidationError as e:
        quit_out.err(["aws_setup.json incorrectly formatted:"] +
            [str(e).split("\n\n")[0]])

    # TODO: Handle this with jsonschema once it's able to
    if not unique_names(config_aws_setup["IAM"]["Policies"]):
        quit_out.err(["aws_setup.json incorrectly formatted:",
            "IAM policy names must be unique."])
    if not unique_names(config_aws_setup["IAM"]["Groups"]):
        quit_out.err(["aws_setup.json incorrectly formatted:",
            "IAM group names must be unique."])
    if not unique_names(config_aws_setup["EC2"]["SecurityGroups"]):
        quit_out.err(["aws_setup.json incorrectly formatted:",
            "EC2 security group names must be unique."])


def verify_instance_templates(config_aws_setup):
    """verify config's instance_templates.json"""
    config_instance_templates = get_config_instance_templates_dict()
    schema = quit_out.parse_json(os.path.abspath(os.path.join(
        __file__, os.pardir, "jsonschemas", "instance_templates_schema.json")))
    try:
        validate(config_instance_templates, schema)
    except ValidationError as e:
        quit_out.err(["instance_templates.json incorrectly formatted:"] +
            [str(e).split("\n\n")[0]])

    # Verify template security group(s) described in aws_setup.json
    sg_names = [sg["Name"] for sg in config_aws_setup["EC2"]["SecurityGroups"]]
    for instance_template in config_instance_templates:
        for security_group in instance_template["SecurityGroups"]:
            if security_group not in sg_names:
                quit_out.err(["instance_templates.json incorrectly formatted:",
                    "SG " + security_group + " not found in aws_setup.json."])


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
    vpc_sg_json_files = [f[:-5] for f in os.listdir(sg_dir)
        if f.endswith(".json")]

    # Quit if aws_setup.json describes SGs not found in vpc_security_groups
    if not set(setup_sg_list).issubset(set(vpc_sg_json_files)):
        quit_out.err([
            "Following SG(s) not found from vpc_security_groups dir:",
            *[(sg + ".json") for sg in setup_sg_list
                if sg not in vpc_sg_json_files]
        ])

    # Quit if any security group missing Ingress and/or Egress tags
    schema = quit_out.parse_json(os.path.abspath(os.path.join(
        __file__, os.pardir, "jsonschemas", "vpc_security_group_schema.json")))
    for sg_file in vpc_sg_json_files:
        sg_dict = quit_out.parse_json(sg_dir + sg_file + ".json")
        try:
            validate(sg_dict, schema)
        except ValidationError as e:
            quit_out.err(["SG " + sg_file + " incorrectly formatted:"] +
                [str(e).split("\n\n")[0]])

    # Warn if vpc_security_groups has SGs not described by aws_setup.json
    if not set(vpc_sg_json_files).issubset(set(setup_sg_list)):
        print("Warning: Unused SG(s) found from vpc_security_groups dir.")


def verify_user_data_files():
    """verify write_file path entries in user_data YAML files"""
    user_data_dir = os.path.join((config.AWS_SETUP_DIR + "user_data"), "")
    user_data_files = [f for f in os.listdir(user_data_dir)
        if f.endswith(".yaml")]

    config_instance_templates = get_config_instance_templates_dict()
    for template in config_instance_templates:
        # Verify template YAML file in user_data directory
        template_yaml_file = template["TemplateName"] + ".yaml"
        if template_yaml_file not in user_data_files:
            quit_out.err([template_yaml_file + " not found from user_data."])

        # Verify template YAML's write_files is disjoin to user_data files
        user_data_file_dir = os.path.join(
            (user_data_dir + template["TemplateName"]), "")
        if os.path.isdir(user_data_file_dir):
            template_files = [template["WriteFilesPath"] + f for f
                in os.listdir(user_data_file_dir)
                if os.path.isfile(user_data_file_dir + f)]
            template_yaml_dict = quit_out.parse_yaml(
                user_data_dir + template_yaml_file)

            if "WriteFilesPath" not in template and template_files:
                quit_out.err(["WriteFilesPath key missing from template.",
                    "  Required when template directory not empty."])

            if "write_files" in template_yaml_dict:
                for write_file in template_yaml_dict["write_files"]:
                    if write_file["path"] in template_files:
                        quit_out.err(["write_files file path collision."])


def list_files_with_sub_dirs(top_dir):
    """compile list of files under top_dir for use with filecmp.cmpfiles"""
    all_files = []
    for path, _, files in os.walk(top_dir):
        for f in files:
            all_files.append(os.path.join(path, f)[len(top_dir):])
    return all_files


def unique_names(dict_list):
    """verify each Name key value is unique within list of dicts"""
    names = [list_dict["Name"] for list_dict in dict_list]
    if len(names) != len(set(names)):
        return False
    return True
