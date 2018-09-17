from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.validate import validate_perms

class ReleaseAddress(CommandBase):

    def main(self, kwargs):
        """release elastic IP address (give up ownership)

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

        if 'association_id' in address and kwargs['force'] is False:
            halt.err("Elastic IP address is currently in use.",
                "Append the -f argument to force disassociation.")

        print("")
        if 'association_id' in address:
            ec2_client.disassociate_address(
                AssociationId=address['association_id'])
            print(f"Elastic IP address {address['ip']} disassociated.")

        ec2_client.release_address(
            AllocationId=address['allocation_id'])
        print(f"Elastic IP address {address['ip']} released.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to be released")
        cmd_parser.add_argument(
            "-f", "--force", action="store_true",
            help="disassociate address if it is in use")


    def blocked_actions(self, kwargs):
        needed_actions = [
            "ec2:DescribeAddresses",
            "ec2:ReleaseAddress"
        ]
        if kwargs['force'] is True:
            needed_actions.append("ec2:DisassociateAddress")
        return validate_perms.blocked(actions=needed_actions)
