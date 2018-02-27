from ec2mc import abstract_command
from ec2mc.stuff import simulate_policy

class GetBackup(abstract_command.CommandBase):

    def main(self, kwargs):
        """download server's world folder as a zip file"""
        pass


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "ec2:DescribeInstances", 
            "ssm:RunCommand"
        ])


    def module_name(self):
        return super().module_name(__name__)
