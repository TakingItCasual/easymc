from botocore.exceptions import WaiterError

from ec2mc import config
from ec2mc import command_template
from ec2mc.verify import verify_instances
from ec2mc.stuff import aws
from ec2mc.stuff import manage_titles
from ec2mc.stuff import simulate_policy

class StartServer(command_template.BaseClass):

    def main(self, kwargs):
        """start stopped instance(s) & update client's server list

        Args:
            kwargs (dict): See verify.verify_instances:argparse_args
        """

        instances = verify_instances.main(kwargs)

        for instance in instances:
            print("")
            print("Attempting to start instance " + instance["id"] + "...")

            ec2_client = aws.ec2_client(instance["region"])

            instance_state = ec2_client.describe_instances(
                InstanceIds=[instance["id"]]
            )["Reservations"][0]["Instances"][0]["State"]["Name"]

            if instance_state != "running" and instance_state != "stopped":
                print("  Instance is currently " + instance_state + ".")
                print("  Cannot start an instance from a transitional state.")
                continue

            if instance_state == "stopped":
                print("  Starting instance...")
                ec2_client.start_instances(InstanceIds=[instance["id"]])

                try:
                    ec2_client.get_waiter("instance_running").wait(
                        InstanceIds=[instance["id"]], WaiterConfig={
                            "Delay": 5, "MaxAttempts": 12
                        })
                except WaiterError:
                    print("  Instance not running after waiting 1 minute.")
                    print("    Check the instance's state in a minute.")
                    continue

                print("  Instance started. The server will be available soon.")
            elif instance_state == "running":
                print("  Instance is already running. Just join the server.")

            instance_dns = ec2_client.describe_instances(
                InstanceIds=[instance["id"]]
            )["Reservations"][0]["Instances"][0]["PublicDnsName"]

            print("  Instance DNS: " + instance_dns)
            if config.SERVERS_DAT is not None:
                manage_titles.update_dns(
                    instance["region"], instance["id"], instance_dns)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:StartInstances"
        ])
