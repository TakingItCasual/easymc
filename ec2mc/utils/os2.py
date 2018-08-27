"""more specialized functions to interact with files and directories"""

import os
import json
import jsonschema
from jsonschema.exceptions import ValidationError
from ruamel import yaml

from ec2mc import consts
from ec2mc.utils import halt

def list_dir_files(target_dir, *, prefix="", ext=""):
    """return list of files in directory"""
    return [f"{prefix}{f}" for f in os.listdir(target_dir)
        if os.path.isfile(f"{target_dir}{f}") and f.endswith(ext)]


def list_dir_dirs(target_dir):
    """return list of directories in directory"""
    return [d for d in os.listdir(target_dir)
        if os.path.isdir(f"{target_dir}{d}")]


def get_json_schema(schema_name):
    """return schema from ec2mc.validate.jsonschemas as dictionary"""
    return parse_json(os.path.join(f"{consts.DIST_DIR}validate",
        "jsonschemas", f"{schema_name}_schema.json"))


def validate_dict(input_dict, schema_dict, input_dict_source):
    """validate dictionary using jsonschema schema dictionary"""
    try:
        jsonschema.validate(input_dict, schema_dict)
    except ValidationError as e:
        halt.err(f"{input_dict_source} incorrectly formatted:", e.message)


def parse_json(file_path):
    """validate JSON file exists and contains valid JSON"""
    if not os.path.isfile(file_path):
        halt.err(f"{file_path} not found.")
    with open(file_path, encoding="utf-8") as f:
        file_contents = f.read()
    try:
        return json.loads(file_contents)
    except ValueError:
        halt.err(f"{file_path} is not a valid JSON file.")


def save_json(input_dict, file_path):
    """modify/create JSON file from dictionary"""
    with open(file_path, "w", encoding="utf-8") as out_file:
        json.dump(input_dict, out_file, ensure_ascii=False, indent=4)


def parse_yaml(file_path):
    """validate YAML file exists and contains valid YAML"""
    if not os.path.isfile(file_path):
        halt.err(f"{file_path} not found.")
    with open(file_path, encoding="utf-8") as f:
        file_contents = f.read()
    try:
        return yaml.safe_load(file_contents)
    except Exception: # Multiple exceptions possible. Idk what they all are.
        halt.err(f"{file_path} is not a valid YAML file.")


def list_files_with_sub_dirs(top_dir):
    """recursively list files under top_dir (used with filecmp.cmpfiles)"""
    all_files = []
    for path, _, files in os.walk(top_dir):
        for f in files:
            all_files.append(os.path.join(path, f)[len(top_dir):])
    return all_files
