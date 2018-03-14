from ec2mc import config
from ec2mc import command_template
from ec2mc.commands.server_sub import *
from ec2mc.verify import verify_instances
from ec2mc.stuff import aws
from ec2mc.stuff import manage_titles
from ec2mc.stuff import simulate_policy

class Server(command_template.BaseClass):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            check.CheckServer(),
            start.StartServer(),
            ssh.SSHServer(),
            #stop.StopServer()
        ]


    def main(self, kwargs):
        """various subcommands to interact with existing instances

        Args:
            kwargs (dict): See stuff.verify_instances:main for documentation
        """

        chosen_cmd = next(cmd for cmd in self.sub_commands
            if cmd.module_name() == kwargs["action"])        
        chosen_cmd.main(kwargs)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        actions = cmd_parser.add_subparsers(metavar="{action}", dest="action")
        actions.required = True
        for sub_command in self.sub_commands:
            sub_command.add_documentation(actions)


    def blocked_actions(self, kwargs):
        chosen_cmd = next(cmd for cmd in self.sub_commands
            if cmd.module_name() == kwargs["action"])
        return chosen_cmd.blocked_actions()


    def module_name(self):
        return super().module_name(__name__)
