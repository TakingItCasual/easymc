from botocore.exceptions import WaiterError

from ec2mc.commands.base_classes import CommandBase
from ec2mc.stuff import manage_titles
from ec2mc.utils import aws
from ec2mc.validate import validate_instances
from ec2mc.validate import validate_perms

class StartServer(CommandBase):

    def main(self, kwargs):
        """start stopped instance(s) & update client's server list

        Args:
            kwargs (dict): See validate.validate_instances:argparse_args
        """
        instances = validate_instances.main(kwargs)

        for instance in instances:
            print("")
            if instance['name'] is not None:
                print(f"Attempting to start {instance['name']} "
                    f"({instance['id']})...")
            else:
                print(f"Attempting to start instance {instance['id']}...")

            ec2_client = aws.ec2_client(instance['region'])

            instance_state = ec2_client.describe_instances(
                InstanceIds=[instance['id']]
            )['Reservations'][0]['Instances'][0]['State']['Name']

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

                print("  Instance started. The server will be available soon.")
            elif instance_state == "running":
                print("  Instance is already running. Just join the server.")

            instance_dns = ec2_client.describe_instances(
                InstanceIds=[instance['id']]
            )['Reservations'][0]['Instances'][0]['PublicDnsName']

            print(f"  Instance DNS: {instance_dns}")
            manage_titles.update_title_dns(
                instance['region'], instance['id'], instance_dns)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        validate_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:StartInstances"
        ])
