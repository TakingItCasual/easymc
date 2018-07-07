from ec2mc import command_template

from ec2mc.commands.server_sub import create
from ec2mc.commands.server_sub import delete
from ec2mc.commands.server_sub import ssh

class Server(command_template.BaseClass):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            create.CreateServer(),
            delete.DeleteServer(),
            ssh.SSHServer()
        ]


    def main(self, kwargs):
        """commands to interact with a single instance

        Args:
            kwargs (dict): Command's argparse arguments
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
