"""more specialized functions to interact with files and directories"""

import os
import json
import jsonschema
from jsonschema.exceptions import ValidationError
from ruamel import yaml

from ec2mc import config
from ec2mc.utils import halt

def list_dir_files(target_dir, *, prefix="", ext=""):
    """return list of files in directory"""
    return [prefix + f for f in os.listdir(target_dir)
        if os.path.isfile(target_dir + f) and f.endswith(ext)]


def list_dir_dirs(target_dir):
    """return list of directories in directory"""
    return [d for d in os.listdir(target_dir) if os.path.isdir(target_dir + d)]


def get_json_schema(schema_name):
    """return schema from ec2mc.verify.jsonschemas as dictionary"""
    return parse_json(os.path.join((config.DIST_DIR + "verify"),
        "jsonschemas", schema_name + "_schema.json"))


def validate_dict(input_dict, schema_dict, input_dict_source):
    """validate dictionary using jsonschema schema dictionary"""
    try:
        jsonschema.validate(input_dict, schema_dict)
    except ValidationError as e:
        halt.err([input_dict_source + " incorrectly formatted:"] + [e.message])


def parse_json(file_path):
    """verify that JSON file exists and contains valid JSON"""
    if not os.path.isfile(file_path):
        halt.err([file_path + " not found."])
    with open(file_path, encoding="utf-8") as f:
        file_contents = f.read()
    try:
        return json.loads(file_contents)
    except ValueError:
        halt.err([file_path + " is not a valid JSON file."])


def save_json(input_dict, file_path):
    """modify/create JSON file from dictionary"""
    with open(file_path, "w", encoding="utf-8") as out_file:
        json.dump(input_dict, out_file, ensure_ascii=False, indent=4)


def parse_yaml(file_path):
    """verify that YAML file exists and contains valid YAML"""
    if not os.path.isfile(file_path):
        halt.err([file_path + " not found."])
    with open(file_path, encoding="utf-8") as f:
        file_contents = f.read()
    try:
        return yaml.load(file_contents, Loader=yaml.RoundTripLoader)
    except: # Multiple exceptions are possible. Idk what they all are.
        halt.err([file_path + " is not a valid YAML file."])


def list_files_with_sub_dirs(top_dir):
    """recursively list files under top_dir (used with filecmp.cmpfiles)"""
    all_files = []
    for path, _, files in os.walk(top_dir):
        for f in files:
            all_files.append(os.path.join(path, f)[len(top_dir):])
    return all_files
