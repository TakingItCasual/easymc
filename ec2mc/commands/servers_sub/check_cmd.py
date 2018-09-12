from ec2mc.utils.base_classes import CommandBase
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

            instance_state, instance_ip = validate_instances.get_state_and_ip(
                instance['region'], instance['id'])

            print(f"  Instance is currently {instance_state}.")
            if instance_state == "running":
                print(f"  Instance IP: {instance_ip}")
                handle_ip.main(instance, instance_ip)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        validate_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances"
        ])
