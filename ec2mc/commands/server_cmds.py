from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.server_sub import create_cmd
from ec2mc.commands.server_sub import delete_cmd
from ec2mc.commands.server_sub import ssh_cmd

class Server(ParentCommand):

    _sub_commands = [
        create_cmd.CreateServer,
        delete_cmd.DeleteServer,
        ssh_cmd.SSHServer
    ]

    def main(self, cmd_args):
        """interact with a single instance"""
        super().main(cmd_args)
