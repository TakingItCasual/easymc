from ec2mc.utils import aws
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

class StopServers(CommandBase):

    def main(self, cmd_args):
        """stop instance(s)

        Args:
            cmd_args (namedtuple): See find_instances:add_argparse_args
        """
        instances = find_instances.main(cmd_args)

        instances_to_stop = False
        instances_stopping = False
        for instance in instances:
            print("")
            print(f"Attempting to stop {instance['name']} "
                f"({instance['id']})...")

            instance_state, _ = find_instances.get_state_and_ip(
                instance['region'], instance['id'])

            if instance_state == "stopped":
                print("  Instance is already stopped.")
                continue
            if instance_state == "stopping":
                instances_stopping = True
                print("  Instance is already in the process of stopping.")
                continue

            instances_to_stop = True
            aws.ec2_client(instance['region']).stop_instances(
                InstanceIds=[instance['id']])
            print(f"  Instance is now stopping.")

        print("")
        if instances_to_stop is True:
            print("Instance(s) may take a few minutes to fully stop.")
        elif instances_stopping is True:
            print("Instance(s) already stopping.")
        else:
            print("No instances to stop.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        find_instances.add_argparse_args(cmd_parser)


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:StopInstances"
        ])
