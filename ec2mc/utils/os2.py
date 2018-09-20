"""more specialized functions to interact with files and directories"""

import os
from pathlib import Path
import filecmp
import json
import jsonschema
from jsonschema.exceptions import ValidationError
from ruamel import yaml

from ec2mc import consts
from ec2mc.utils import halt

def dir_files(target_dir, *, ext=""):
    """return list[str] of names of files in directory"""
    return [f.name for f in target_dir.iterdir()
        if (target_dir / f).is_file() and str(f).endswith(ext)]


def dir_dirs(target_dir):
    """return list[str] of names of directories in directory"""
    return [d.name for d in target_dir.iterdir() if (target_dir / d).is_dir()]


def get_json_schema(schema_name):
    """return schema from ec2mc.validate.jsonschemas as dictionary"""
    return parse_json(consts.DIST_DIR / "validate" / "jsonschemas" /
        f"{schema_name}_schema.json")


def validate_dict(input_dict, schema_dict, input_dict_source):
    """validate dictionary using jsonschema schema dictionary"""
    try:
        jsonschema.validate(input_dict, schema_dict)
    except ValidationError as e:
        halt.err(f"{input_dict_source} incorrectly formatted:", e.message)


def parse_json(file_path):
    """validate JSON file exists and contains valid JSON"""
    if not file_path.is_file():
        halt.err(f"{file_path} not found.")
    file_contents = file_path.read_text(encoding="utf-8")
    try:
        return json.loads(file_contents)
    except ValueError:
        halt.err(f"{file_path} is not a valid JSON file.")


def save_json(input_dict, file_path):
    """modify/create JSON file from dictionary"""
    with file_path.open("w", encoding="utf-8") as out_file:
        json.dump(input_dict, out_file, ensure_ascii=False, indent=4)


def parse_yaml(file_path):
    """validate YAML file exists and contains valid YAML"""
    if not file_path.is_file():
        halt.err(f"{file_path} not found.")
    file_contents = file_path.read_text(encoding="utf-8")
    try:
        return yaml.safe_load(file_contents)
    except Exception: # Multiple exceptions possible. Idk what they all are.
        halt.err(f"{file_path} is not a valid YAML file.")


def del_readonly(action, name, exc):
    """handle deletion of readonly files for shutil.rmtree"""
    name = Path(name)
    name.chmod(0o777)
    name.unlink()


def recursive_cmpfiles(src_dir, dest_dir):
    """wrapper for filecmp.cmpfiles, which recursively finds src_dir's files"""
    prefix_len = len(src_dir.parts)
    cmp_files = []
    for path, _, files in os.walk(src_dir):
        for f in files:
            cmp_files.append(Path(*(Path(path) / f).parts[prefix_len:]))
    return filecmp.cmpfiles(src_dir, dest_dir, cmp_files, shallow=False)
