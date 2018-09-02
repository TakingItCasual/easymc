from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import handle_ip
from ec2mc.validate import validate_instances
from ec2mc.validate import validate_perms

class CheckServers(CommandBase):

    def main(self, kwargs):
        """check instance status(es)

        Args:
            kwargs (dict): See validate.validate_instances:argparse_args
        """
        instances = validate_instances.main(kwargs)

        for instance in instances:
            print("")
            print(f"Checking {instance['name']} ({instance['id']})...")

            ec2_client = aws.ec2_client(instance['region'])

            response = ec2_client.describe_instances(
                InstanceIds=[instance['id']]
            )['Reservations'][0]['Instances'][0]
            instance_state = response['State']['Name']
            instance_dns = response['PublicDnsName']

            print(f"  Instance is currently {instance_state}.")
            if instance_state == "running":
                print(f"  Instance DNS: {instance_dns}")
                handle_ip.main(instance, instance_dns)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        validate_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances"
        ])
