from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.address_sub import list_cmd
from ec2mc.commands.address_sub import request_cmd
from ec2mc.commands.address_sub import associate_cmd
from ec2mc.commands.address_sub import disassociate_cmd
from ec2mc.commands.address_sub import release_cmd

# TODO: Add command to move address from one region to another
class Address(ParentCommand):

    _sub_commands = [
        list_cmd.ListAddresses,
        request_cmd.RequestAddress,
        associate_cmd.AssociateAddress,
        disassociate_cmd.DisassociateAddress,
        release_cmd.ReleaseAddress
    ]

    def main(self, cmd_args):
        """manage elastic IP addresses for instances"""
        super().main(cmd_args)
