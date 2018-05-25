"""more specialized functions to interact with files and directories"""

import os
import json
from ruamel import yaml

from ec2mc.stuff import halt

def list_dir_files(target_dir, *, prefix="", ext=""):
    """return list of files in directory"""
    return [prefix + f for f in os.listdir(target_dir)
        if os.path.isfile(target_dir + f) and f.endswith(ext)]


def list_dir_dirs(target_dir, *, prefix=""):
    """return list of directories in directory"""
    return [prefix + d for d in os.listdir(target_dir)
        if os.path.isdir(target_dir + d)]


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
    """compile list of files under top_dir for use with filecmp.cmpfiles"""
    all_files = []
    for path, _, files in os.walk(top_dir):
        for f in files:
            all_files.append(os.path.join(path, f)[len(top_dir):])
    return all_files
