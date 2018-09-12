from botocore.exceptions import WaiterError

from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import handle_ip
from ec2mc.validate import validate_instances
from ec2mc.validate import validate_perms

class StartServers(CommandBase):

    def main(self, kwargs):
        """start stopped instance(s)

        Args:
            kwargs (dict): See validate.validate_instances:argparse_args
        """
        instances = validate_instances.main(kwargs)

        for instance in instances:
            print("")
            print(f"Attempting to start {instance['name']} "
                f"({instance['id']})...")

            ec2_client = aws.ec2_client(instance['region'])

            instance_state, _ = validate_instances.get_state_and_ip(
                instance['region'], instance['id'])

            if instance_state not in ("running", "stopped"):
                print(f"  Instance is currently {instance_state}.")
                print("  Cannot start an instance from a transitional state.")
                continue

            if instance_state == "stopped":
                print("  Starting instance...")
                ec2_client.start_instances(InstanceIds=[instance['id']])

                try:
                    ec2_client.get_waiter("instance_running").wait(
                        InstanceIds=[instance['id']],
                        WaiterConfig={'Delay': 5, 'MaxAttempts': 12}
                    )
                except WaiterError:
                    print("  Instance not running after waiting 1 minute.")
                    print("    Check instance's state in a minute.")
                    continue

                print("  Instance started.")
            elif instance_state == "running":
                print("  Instance is already running.")

            _, instance_ip = validate_instances.get_state_and_ip(
                instance['region'], instance['id'])

            print(f"  Instance IP: {instance_ip}")
            handle_ip.main(instance, instance_ip)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        validate_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:StartInstances"
        ])
