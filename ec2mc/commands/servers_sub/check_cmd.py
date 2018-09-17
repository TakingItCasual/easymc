from ec2mc.utils import handle_ip
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

class CheckServers(CommandBase):

    def main(self, kwargs):
        """check instance status(es)

        Args:
            kwargs (dict): See utils.find.find_instances:argparse_args
        """
        instances = find_instances.main(kwargs)

        for instance in instances:
            print("")
            print(f"Checking {instance['name']} ({instance['id']})...")

            instance_state, instance_ip = find_instances.get_state_and_ip(
                instance['region'], instance['id'])

            print(f"  Instance is currently {instance_state}.")
            if instance_state == "running":
                print(f"  Instance IP: {instance_ip}")
                handle_ip.main(instance, instance_ip)


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        find_instances.argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=["ec2:DescribeInstances"])
