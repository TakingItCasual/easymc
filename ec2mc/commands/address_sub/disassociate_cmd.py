from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.validate import validate_perms

class DisassociateAddress(CommandBase):

    def main(self, kwargs):
        """disassociate elastic IP address from any association

        Args:
            kwargs (dict): See add_documentation method.
        """
        addresses = find_addresses.probe_regions()
        try:
            address = next(address for address in addresses
                if address['ip'] == kwargs['ip'])
        except StopIteration:
            halt.err("You do not possess the specified elastic IP address.")

        ec2_client = aws.ec2_client(address['region'])


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to disassociate")


    def blocked_actions(self, kwargs):
        return validate_perms.blocked(actions=["ec2:DescribeAddresses"])
