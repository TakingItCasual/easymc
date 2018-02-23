import boto3

from ec2mc import abstract_command
from ec2mc.stuff import simulate_policy

class CreateServer(abstract_command.CommandBase):

    def main(self, user_info, kwargs):
        """Creates and initializes a new instance."""
        pass


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)


    def blocked_actions(self, user_info):
        blocked_actions = []
        blocked_actions.extend(simulate_policy.blocked(user_info, actions=[
            "ec2:DescribeInstances"
        ]))
        blocked_actions.extend(simulate_policy.blocked(user_info, actions=[
            "ec2:RunInstances"
        ], context={
            "ec2:InstanceType": ["t2.small"]
        }))
        return blocked_actions


    def module_name(self):
        return super().module_name(__name__)
