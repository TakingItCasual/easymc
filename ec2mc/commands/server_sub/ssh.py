import os
import platform
import subprocess
import shutil

from ec2mc import consts
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.validate import validate_instances
from ec2mc.validate import validate_perms

class SSHServer(CommandBase):

    def main(self, kwargs):
        """SSH into an EC2 instance using its .pem private key

        Attempts to open an interactive SSH session using either OpenSSH 
        or PuTTY (OpenSSH is prioritized). A .pem/.ppk private key file is 
        expected to exist within user's config. Instance's user@hostname 
        is printed, for if an alternative SSH method is desired.

        Args:
            kwargs (dict): See validate.validate_instances:argparse_args
        """
        instances = validate_instances.main(kwargs)
        if len(instances) > 1:
            halt.err("Instance query returned multiple results.",
                "  Narrow filter(s) so that only one instance is returned.")
        instance = instances[0]

        if 'DefaultUser' not in instance['tags']:
            halt.err("Instance missing DefaultUser tag key-value pair.")

        response = aws.ec2_client(instance['region']).describe_instances(
            InstanceIds=[instance['id']]
        )['Reservations'][0]['Instances'][0]
        instance_state = response['State']['Name']
        instance_dns = response['PublicDnsName']

        if instance_state != "running":
            halt.err("Cannot SSH into an instance that isn't running.")

        user_and_hostname = f"{instance['tags']['DefaultUser']}@{instance_dns}"

        print("")
        print("Instance's user and hostname (seperated by \"@\"):")
        print(user_and_hostname)

        pem_key_path = consts.RSA_PRIV_KEY_PEM
        if shutil.which("ssh") is not None:
            self.open_openssh_session(user_and_hostname, pem_key_path)
        elif shutil.which("putty") is not None:
            self.open_putty_session(user_and_hostname, pem_key_path)
        else:
            if platform.system() == "Windows":
                halt.err("Neither OpenSSH for Windows nor PuTTY were found.",
                    "  Please install one and ensure it is in PATH.",
                    "  OpenSSH: http://www.mls-software.com/opensshd.html",
                    "  PuTTY: https://www.putty.org/")
            halt.err("Neither the OpenSSH client nor PuTTY were found.",
                "  Please install one and ensure it is in PATH.")


    def open_openssh_session(self, user_and_hostname, pem_key_path):
        """open interactive SSH session using the OpenSSH client"""
        if not os.path.isfile(pem_key_path):
            key_file_base = os.path.basename(pem_key_path)
            halt.err(f"{key_file_base} not found from config.",
                f"  {key_file_base} file required to SSH with OpenSSH.")
        os.chmod(pem_key_path, consts.PK_PERMS)

        print("")
        print("Attempting to SSH into instance with OpenSSH...")
        subprocess.run([
            "ssh",
            "-o", "LogLevel=ERROR",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-i", pem_key_path,
            user_and_hostname
        ])


    def open_putty_session(self, user_and_hostname, pem_key_path):
        """open interactive SSH session using the PuTTY client"""
        ppk_key_path = f"{os.path.splitext(pem_key_path)[0]}.ppk"
        if not os.path.isfile(ppk_key_path):
            key_file_base = os.path.basename(ppk_key_path)
            halt.err(f"{key_file_base} not found from config.",
                f"  {key_file_base} file required to SSH with PuTTY.",
                "  You can convert a .pem file to .ppk using puttygen.")
        os.chmod(ppk_key_path, consts.PK_PERMS)

        print("")
        print("Attempting to SSH into instance with PuTTY...")
        subprocess.run([
            "putty", "-ssh",
            "-i", ppk_key_path,
            user_and_hostname
        ])
        print("Connection closed.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        validate_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances"
        ])
