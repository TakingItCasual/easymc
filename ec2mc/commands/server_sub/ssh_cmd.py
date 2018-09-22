import platform
import subprocess
import shutil

from ec2mc import consts
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

# TODO: Look into using the ssm:StartSession action
class SSHServer(CommandBase):

    def main(self, cmd_args):
        """SSH into an EC2 instance using its .pem/.ppk private key

        Attempts to open an interactive SSH session using either OpenSSH
        or PuTTY (OpenSSH is prioritized). A .pem/.ppk private key file is
        expected to exist within user's config. Instance's user@hostname
        is printed, for if an alternative SSH method is desired.

        Args:
            cmd_args (dict): See utils.find.find_instances:argparse_args
        """
        instance = find_instances.main(cmd_args, single_instance=True)
        instance_state, instance_ip = find_instances.get_state_and_ip(
            instance['region'], instance['id'])

        if 'DefaultUser' not in instance['tags']:
            halt.err("Instance missing DefaultUser tag key-value pair.")

        if instance_state != "running":
            halt.err("Cannot SSH into an instance that isn't running.")

        user_and_hostname = f"{instance['tags']['DefaultUser']}@{instance_ip}"

        print("")
        print("Instance's user and hostname (seperated by \"@\"):")
        print(user_and_hostname)

        if shutil.which("ssh") is not None:
            self.open_openssh_session(user_and_hostname, consts.RSA_KEY_PEM)
        elif shutil.which("putty") is not None:
            self.open_putty_session(user_and_hostname, consts.RSA_KEY_PPK)
        else:
            if platform.system() == "Windows":
                halt.err("Neither OpenSSH for Windows nor PuTTY were found.",
                    "  Please install one and ensure it is in PATH.",
                    "  OpenSSH: http://www.mls-software.com/opensshd.html",
                    "  PuTTY: https://www.putty.org/")
            halt.err("Neither the OpenSSH client nor PuTTY were found.",
                "  Please install one and ensure it is in PATH.")


    @staticmethod
    def open_openssh_session(user_and_hostname, pem_key_path):
        """open interactive SSH session using the OpenSSH client"""
        if not pem_key_path.is_file():
            halt.err(f"{pem_key_path.name} not found from config.",
                f"  {pem_key_path.name} file required to SSH with OpenSSH.")
        pem_key_path.chmod(consts.PK_PERMS)

        print("")
        print("Attempting to SSH into instance with OpenSSH...")
        subprocess.run([
            "ssh",
            "-o", "LogLevel=ERROR",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-i", str(pem_key_path),
            user_and_hostname
        ])


    @staticmethod
    def open_putty_session(user_and_hostname, ppk_key_path):
        """open interactive SSH session using the PuTTY client"""
        if not ppk_key_path.is_file():
            halt.err(f"{ppk_key_path.name} not found from config.",
                f"  {ppk_key_path.name} file required to SSH with PuTTY.",
                "  You can convert a .pem file to .ppk using puttygen.")
        ppk_key_path.chmod(consts.PK_PERMS)

        print("")
        print("Attempting to SSH into instance with PuTTY...")
        subprocess.run([
            "putty", "-ssh",
            "-i", str(ppk_key_path),
            user_and_hostname
        ])
        print("Connection closed.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        find_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=["ec2:DescribeInstances"])
