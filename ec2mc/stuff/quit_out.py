import os.path
import json
from ruamel import yaml

def assert_empty(blocked_actions):
    """used with simulate_policy, which returns a list of denied AWS actions"""
    if blocked_actions:
        err(["Missing following IAM permission(s):"] + blocked_actions)


def parse_json(file_path):
    """verify that JSON file exists and contains valid JSON"""
    if not os.path.isfile(file_path):
        err([file_path + " not found."])
    with open(file_path, encoding="utf-8") as f:
        file_contents = f.read()
    try:
        return json.loads(file_contents)
    except ValueError:
        err([file_path + " is not a valid JSON file."])


def parse_yaml(file_path):
    """verify that YAML file exists and contains valid YAML"""
    if not os.path.isfile(file_path):
        err([file_path + " not found."])
    with open(file_path, encoding="utf-8") as f:
        file_contents = f.read()
    try:
        return yaml.load(file_contents, Loader=yaml.RoundTripLoader)
    except: # Multiple exceptions are possible. Idk what they all are.
        err([file_path + " is not a valid YAML file."])


def err(quit_message_list):
    """first prepend Error to the first quit message, then quit"""
    quit_message_list[0] = "Error: " + quit_message_list[0]
    q(quit_message_list)


def q(quit_message_list=None):
    """quits ec2mc when called by raising SystemExit"""
    if quit_message_list:
        print("")
        for quit_message in quit_message_list:
            print(quit_message)
    raise SystemExit(0) # Equivalent to sys.exit(0)
