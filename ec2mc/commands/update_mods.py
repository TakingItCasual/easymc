from ec2mc import command_template
from ec2mc.stuff import simulate_policy

class UpdateMods(command_template.BaseClass):

    def main(self, kwargs):
        """update server's mods via the internet"""
        pass


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)


    def blocked_actions(self, _):
        return simulate_policy.blocked(actions=[
            "ec2:DescribeInstances",
            "ssm:SendCommand"
        ])


    def module_name(self):
        return super().module_name(__name__)
