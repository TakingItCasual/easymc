from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.server_sub import create_cmd
from ec2mc.commands.server_sub import delete_cmd
from ec2mc.commands.server_sub import ssh_cmd

class Server(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            create_cmd.CreateServer(),
            delete_cmd.DeleteServer(),
            ssh_cmd.SSHServer()
        ]


    def main(self, kwargs):
        """commands to interact with a single instance"""
        super().main(kwargs)
