from ec2mc.commands.base_classes import ParentCommand

from ec2mc.commands.servers_sub import check_cmd
from ec2mc.commands.servers_sub import start_cmd
from ec2mc.commands.servers_sub import stop_cmd

class Servers(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            check_cmd.CheckServers(),
            start_cmd.StartServers(),
            stop_cmd.StopServers()
        ]


    def main(self, kwargs):
        """commands to interact with a one or more existing instances"""
        super().main(kwargs)
