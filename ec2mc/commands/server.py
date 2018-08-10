from ec2mc.commands.base_classes import ParentCommand

from ec2mc.commands.server_sub import create
from ec2mc.commands.server_sub import delete
from ec2mc.commands.server_sub import ssh

class Server(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            create.CreateServer(),
            delete.DeleteServer(),
            ssh.SSHServer()
        ]


    def main(self, kwargs):
        """commands to interact with a single instance"""
        super().main(kwargs)
