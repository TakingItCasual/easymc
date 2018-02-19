import os
import subprocess
import shutil
import boto3

import const
from verify import verify_instances
from stuff import simulate_policy
from stuff import quit_out
from commands.check_server import add_documentation_args

def main(user_info, args):
    """SSH into an EC2 instance using a .pem private key

    The private key is searched for from the script's config folder. Currently 
    SSH is only supported with a .pem private key, and using multiple keys is 
    not supported: all instances under an AWS account must share a private key.
    """
    
    if os.name != "posix":
        quit_out.q(["Error: This command is only supported on posix systems."])

    instance = verify_instances.main(user_info, args)

    if len(instance) > 1:
        quit_out.q(["Error: Instance query returned multiple results.", 
            "  Narrow filter(s) so that only one instance is returned."])
    instance = instance[0]

    ec2_client = boto3.client("ec2", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"], 
        region_name=instance["region"]
    )

    response = ec2_client.describe_instances(
        InstanceIds=[instance["id"]]
    )["Reservations"][0]["Instances"][0]
    instance_state = response["State"]["Name"]
    instance_dns = response["PublicDnsName"]

    if instance_state != "running":
        quit_out.q(["Error: Cannot SSH into instance unless it is running."])

    # Detects if the system has the "ssh" command.
    if not shutil.which("ssh"):
        quit_out.q(["Error: SSH executable not found. Please install it."])

    print("")
    print("Attempting to SSH into instance...")
    ssh_cmd_str = ([
        "ssh", "-q", 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "UserKnownHostsFile=/dev/null", 
        "-i", find_private_key(), 
        "ec2-user@"+instance_dns
    ])
    subprocess.run(ssh_cmd_str)


def find_private_key():
    """Returns file path of .pem private key from config, if only one exists."""
    private_keys = []
    for file in os.listdir(const.CONFIG_FOLDER):
        if file.endswith(".pem"):
            private_keys.append(const.CONFIG_FOLDER + file)

    if not private_keys:
        quit_out.q(["Error: .pem private key file not found in config."])
    elif len(private_keys) > 1:
        quit_out.q(["Error: Multiple .pem private key files found in config."])
    return private_keys[0]


def add_documentation(argparse_obj, module_name):
    cmd_parser = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])
    add_documentation_args(cmd_parser)


def blocked_actions(user_info):
    """Returns list of denied AWS actions used in the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances"
    ])
