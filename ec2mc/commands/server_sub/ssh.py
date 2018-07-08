import os
import subprocess
import shutil

from ec2mc import config
from ec2mc.commands import template
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.verify import verify_instances
from ec2mc.verify import verify_perms

class SSHServer(template.BaseClass):

    def main(self, kwargs):
        """SSH into an EC2 instance using its .pem private key

        The private key is expected at config.RSA_PRIV_KEY_PEM (file path). 
        File's name is linked to the Namespace. If not a POSIX system, just 
        print out instance's username@hostname.

        Args:
            kwargs (dict): See verify.verify_instances:argparse_args
        """

        if os.name != "posix":
            print("")
            print("Notice: This command is not fully implemented for your OS.")
            print("  Interactive SSH session will not be opened.")

        instances = verify_instances.main(kwargs)
        if len(instances) > 1:
            halt.err("Instance query returned multiple results.",
                "  Narrow filter(s) so that only one instance is returned.")
        instance = instances[0]

        # Verify RSA private key file exists and set permissions
        if not os.path.isfile(config.RSA_PRIV_KEY_PEM):
            halt.err(config.RSA_PRIV_KEY_PEM + " not found.",
                "  Namespace RSA private key PEM file required to SSH.")
        os.chmod(config.RSA_PRIV_KEY_PEM, config.PK_PERMS)

        ec2_client = aws.ec2_client(instance["region"])

        response = ec2_client.describe_instances(
            InstanceIds=[instance["id"]]
        )["Reservations"][0]["Instances"][0]
        instance_state = response["State"]["Name"]
        instance_dns = response["PublicDnsName"]
        try:
            default_user = next(pair["Value"] for pair in response["Tags"]
                if pair["Key"] == "DefaultUser")
        except StopIteration:
            halt.err("Instance missing DefaultUser tag key-value pair.")

        if instance_state != "running":
            halt.err("Cannot SSH into an instance that isn't running.")

        username_and_hostname = default_user + "@" + instance_dns

        print("")
        print("Instance's user and hostname are the following:")
        print(username_and_hostname)

        if os.name == "posix":
            # Detect if system has the "ssh" command.
            if shutil.which("ssh") is None:
                halt.err("OpenSSH SSH client executable not found.",
                    "  Please install it.")

            print("")
            print("Attempting to SSH into instance...")
            ssh_cmd_args = [
                "ssh",
                "-o", "LogLevel=ERROR",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-i", config.RSA_PRIV_KEY_PEM,
                username_and_hostname
            ]
            subprocess.run(ssh_cmd_args)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances"
        ])
