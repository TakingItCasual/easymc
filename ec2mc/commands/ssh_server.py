import os
import subprocess
import shutil
import boto3

from ec2mc import const
from ec2mc import abstract_command
from ec2mc.verify import verify_instances
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

class SSHServer(abstract_command.CommandBase):

    def main(self, user_info, kwargs):
        """SSH into an EC2 instance using a .pem private key

        The private key is searched for from the script's config folder. 
        Currently SSH is only supported with a .pem private key, and using 
        multiple keys is not supported.
        """
        
        if os.name != "posix":
            quit_out.q(["Error: ssh_server only supported on posix systems."])

        instance = verify_instances.main(user_info, kwargs)

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
            quit_out.q(["Error: Cannot SSH into instance that isn't running."])

        # Detects if the system has the "ssh" command.
        if not shutil.which("ssh"):
            quit_out.q(["Error: SSH executable not found. Please install it."])

        print("")
        print("Attempting to SSH into instance...")
        ssh_cmd_str = ([
            "ssh", "-q", 
            "-o", "StrictHostKeyChecking=no", 
            "-o", "UserKnownHostsFile=/dev/null", 
            "-i", self.find_private_key(), 
            "ec2-user@"+instance_dns
        ])
        subprocess.run(ssh_cmd_str)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        abstract_command.args_to_filter_instances(cmd_parser)


    def blocked_actions(self, user_info):
        return simulate_policy.blocked(user_info, actions=[
            "ec2:DescribeInstances"
        ])


    def module_name(self):
        return super().module_name(__name__)


    def find_private_key(self):
        """Returns config's private key file path, if only one exists."""
        private_keys = []
        for file in os.listdir(const.CONFIG_FOLDER):
            if file.endswith(".pem"):
                private_keys.append(const.CONFIG_FOLDER + file)

        if not private_keys:
            quit_out.q(["Error: Private key file not found in config."])
        elif len(private_keys) > 1:
            quit_out.q(["Error: Multiple private key files found in config."])
        return private_keys[0]
