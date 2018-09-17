from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

class AssociateAddress(CommandBase):

    def main(self, kwargs):
        """associate elastic IP address an/another instance

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
            "ip", help="IP of elastic IP address to (re)associate")
        cmd_parser.add_argument(
            "id", help="ID of instance to associate address to")


    def blocked_actions(self, kwargs):
        return validate_perms.blocked(actions=[
            "ec2:DescribeAddresses"
        ])
