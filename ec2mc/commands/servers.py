from ec2mc.commands.base_classes import ParentCommand

from ec2mc.commands.servers_sub import check
from ec2mc.commands.servers_sub import start
from ec2mc.commands.servers_sub import stop

class Servers(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            check.CheckServers(),
            start.StartServers(),
            stop.StopServers()
        ]


    def main(self, kwargs):
        """commands to interact with a one or more existing instances"""
        super().main(kwargs)
