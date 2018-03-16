import os
import subprocess
import shutil

from ec2mc import config
from ec2mc import command_template
from ec2mc.verify import verify_instances
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

class SSHServer(command_template.BaseClass):

    def main(self, kwargs):
        """SSH into an EC2 instance using its .pem private key

        The private key is expected to exist within config.CONFIG_DIR

        Currently SSH is only supported with a .pem private key, and using 
        multiple keys is not supported. Only posix systems are supported.
        """

        if os.name != "posix":
            quit_out.err(["ssh_server only supported on posix systems.",
                "  Google around for methods of SSHing with your OS."])

        private_key_file = self.find_private_key()

        instance = verify_instances.main(kwargs)
        if len(instance) > 1:
            quit_out.err(["Instance query returned multiple results.",
                "  Narrow filter(s) so that only one instance is found."])
        instance = instance[0]

        ec2_client = aws.ec2_client(instance["region"])

        response = ec2_client.describe_instances(
            InstanceIds=[instance["id"]]
        )["Reservations"][0]["Instances"][0]
        instance_state = response["State"]["Name"]
        instance_dns = response["PublicDnsName"]

        if instance_state != "running":
            quit_out.err(["Cannot SSH into instance that isn't running."])

        # Detects if the system has the "ssh" command.
        if not shutil.which("ssh"):
            quit_out.err(["SSH executable not found. Please install it."])

        print("")
        print("Attempting to SSH into instance...")
        ssh_cmd_str = ([
            "ssh", "-q",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-i", private_key_file,
            "ec2-user@"+instance_dns
        ])
        subprocess.run(ssh_cmd_str)


    def find_private_key(self):
        """return config's private key file path, if only one exists"""
        private_keys = []
        for file in os.listdir(config.CONFIG_DIR):
            if file.endswith(".pem"):
                private_keys.append(config.CONFIG_DIR + file)

        if not private_keys:
            quit_out.err(["Private key file not found in config."])
        elif len(private_keys) > 1:
            quit_out.err(["Multiple private key files found in config."])

        os.chmod(private_keys[0], config.PK_PERMS)
        return private_keys[0]


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "ec2:DescribeInstances"
        ])


    def module_name(self):
        return super().module_name(__name__)
