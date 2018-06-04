import os
import subprocess
import shutil

from ec2mc import config
from ec2mc import command_template
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.verify import verify_instances
from ec2mc.verify import verify_perms

class SSHServer(command_template.BaseClass):

    def main(self, kwargs):
        """SSH into an EC2 instance using its .pem private key

        The private key is expected to exist within config.CONFIG_DIR

        Currently SSH is only supported with a .pem private key, and using 
        multiple keys is not supported. Only posix systems are supported.

        Args:
            kwargs (dict): See verify.verify_instances:argparse_args
        """

        if os.name != "posix":
            halt.err("ssh command only supported on posix systems.",
                "  Google for a method of SSHing with your OS.")

        instance = verify_instances.main(kwargs)
        if len(instance) > 1:
            halt.err("Instance query returned multiple results.",
                "  Narrow filter(s) so that only one instance is returned.")
        instance = instance[0]

        # Verify RSA private key file path and permissions
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

        # Detects if the system has the "ssh" command.
        if not shutil.which("ssh"):
            halt.err("SSH executable not found. Please install it.")

        print("")
        print("Attempting to SSH into instance...")
        ssh_cmd_args = [
            "ssh", "-q",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-i", config.RSA_PRIV_KEY_PEM,
            default_user+"@"+instance_dns
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
