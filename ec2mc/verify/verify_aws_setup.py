import os
import json
import shutil

from ec2mc import config

import pprint
pp = pprint.PrettyPrinter(indent=2)

def main():
    """create aws_setup if nonexistant, update if needed and is unprotected"""
    
    aws_setup_src_dir = os.path.abspath(
        os.path.join(__file__, os.pardir, os.pardir, "aws_setup_src"))

    # If config.AWS_SETUP_DIR nonexistant, copy from ec2mc.aws_setup_src
    if not os.path.isdir(config.AWS_SETUP_DIR):
        overwrite_aws_setup(aws_setup_src_dir)
        return

    # Otherwise, check if it should be updated
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
        overwrite_aws_setup(aws_setup_src_dir)
    # If the "Protect" key has been set to True, prevent overwriting aws_setup
    elif config_aws_setup["Protect"]:
        pass
    # Version can be set to 0 during development for constant refreshing
    elif source_aws_setup["Version"] == 0:
        overwrite_aws_setup(aws_setup_src_dir)
    # Update if version in source is more recent
    elif source_aws_setup["Version"] > config_aws_setup["Version"]:
        overwrite_aws_setup(aws_setup_src_dir)


def overwrite_aws_setup(aws_setup_src_dir):
    if os.path.isdir(config.AWS_SETUP_DIR):
        shutil.rmtree(config.AWS_SETUP_DIR)
    shutil.copytree(aws_setup_src_dir, config.AWS_SETUP_DIR)
