from botocore.exceptions import WaiterError

from ec2mc import command_template
from ec2mc.verify import verify_instances
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy

class StopServer(command_template.BaseClass):

    def main(self, kwargs):
        """force instance(s) to stop, regardless of online players"""
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
                ec2_client.get_waiter('instance_stopped').wait(
                    InstanceIds=[instance["id"]], WaiterConfig={
                        "Delay": 5, "MaxAttempts": 12
                    })
            except WaiterError:
                quit_out.err([
                    "Instance should be stopped after 1 minute.",
                    "  Check server's state after a few minutes."])

            print("  Instance stopped.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:StopInstances"
        ])


    def module_name(self):
        return super().module_name(__name__)
