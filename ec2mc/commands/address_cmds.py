from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.address_sub import list_cmd
from ec2mc.commands.address_sub import release_cmd

class Address(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            list_cmd.ListAddresses(),
            release_cmd.ReleaseAddress()
        ]


    def main(self, kwargs):
        """commands to manage elastic IPs for instances"""
        super().main(kwargs)
