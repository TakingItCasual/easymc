from botocore.exceptions import WaiterError

from ec2mc.utils import aws
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

class StopServers(CommandBase):

    def main(self, kwargs):
        """stop instance(s)

        Args:
            kwargs (dict): See utils.find.find_instances:argparse_args
        """
        instances = find_instances.main(kwargs)

        for instance in instances:
            print("")
            print(f"Attempting to stop {instance['name']} "
                f"({instance['id']})...")

            instance_state, _ = find_instances.get_state_and_ip(
                instance['region'], instance['id'])

            if instance_state == "stopped":
                print("  Instance is already stopped.")
                continue

            ec2_client = aws.ec2_client(instance['region'])

            print("  Stopping instance...")
            ec2_client.stop_instances(InstanceIds=[instance['id']])

            try:
                ec2_client.get_waiter("instance_stopped").wait(
                    InstanceIds=[instance['id']],
                    WaiterConfig={'Delay': 5, 'MaxAttempts': 12}
                )
            except WaiterError:
                print("  Instance not stopped after waiting 1 minute.")
                print("    Check instance's state in a minute.")
                continue

            print("  Instance stopped.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        find_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:StopInstances"
        ])
