from botocore.exceptions import WaiterError

from ec2mc import command_template
from ec2mc.utils import aws
from ec2mc.verify import verify_instances
from ec2mc.verify import verify_perms

class StopServer(command_template.BaseClass):

    def main(self, kwargs):
        """force instance(s) to stop, regardless of online players

        Args:
            kwargs (dict): See verify.verify_instances:argparse_args
        """

        instances = verify_instances.main(kwargs)

        for instance in instances:
            print("")
            print("Attempting to stop instance " + instance["id"] + "...")

            ec2_client = aws.ec2_client(instance["region"])

            instance_state = ec2_client.describe_instances(
                InstanceIds=[instance["id"]]
            )["Reservations"][0]["Instances"][0]["State"]["Name"]

            if instance_state == "stopped":
                print("  Instance is already stopped.")
                continue

            print("  Stopping instance...")
            ec2_client.stop_instances(InstanceIds=[instance["id"]])

            try:
                ec2_client.get_waiter("instance_stopped").wait(
                    InstanceIds=[instance["id"]],
                    WaiterConfig={"Delay": 5, "MaxAttempts": 12}
                )
            except WaiterError:
                print("  Instance not stopped after waiting 1 minute.")
                print("    Check instance's state in a minute.")
                continue

            print("  Instance stopped.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:StopInstances"
        ])
