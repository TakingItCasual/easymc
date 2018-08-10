from ec2mc import config
from ec2mc.commands.base_classes import CommandBase
from ec2mc.stuff import manage_titles
from ec2mc.utils import aws
from ec2mc.verify import verify_instances
from ec2mc.verify import verify_perms

class CheckServer(CommandBase):

    def main(self, kwargs):
        """check instance status(es) & update client's server list

        Args:
            kwargs (dict): See verify.verify_instances:argparse_args
        """
        instances = verify_instances.main(kwargs)

        for instance in instances:
            print("")
            if instance['name'] is not None:
                print(f"Checking {instance['name']} ({instance['id']})...")
            else:
                print(f"Checking instance {instance['id']}...")

            ec2_client = aws.ec2_client(instance['region'])

            response = ec2_client.describe_instances(
                InstanceIds=[instance['id']]
            )['Reservations'][0]['Instances'][0]
            instance_state = response['State']['Name']
            instance_dns = response['PublicDnsName']

            print(f"  Instance is currently {instance_state}.")

            if instance_state == "running":
                print(f"  Instance DNS: {instance_dns}")
                if config.SERVERS_DAT is not None:
                    manage_titles.update_title_dns(
                        instance['region'], instance['id'], instance_dns)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances"
        ])
