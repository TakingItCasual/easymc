from ec2mc.commands.base_classes import ParentCommand

from ec2mc import config
from ec2mc.commands.servers_sub import check
from ec2mc.commands.servers_sub import start
from ec2mc.commands.servers_sub import stop

class Servers(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            check.CheckServer(),
            start.StartServer(),
            stop.StopServer()
        ]


    def main(self, kwargs):
        """commands to interact with a one or more existing instances"""
        if kwargs['action'] in ["check", "start"]:
            if config.SERVERS_DAT is None:
                print("")
                print("Config missing valid path for MC client's servers.dat.")
                print("  Minecraft client's server list will not be updated.")

        super().main(kwargs)
