from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.validate import validate_perms

class ReleaseAddress(CommandBase):

    def main(self, cmd_args):
        """release elastic IP address (give up possession)

        Args:
            cmd_args (namedtuple): See add_documentation method.
        """
        address = find_addresses.main(cmd_args.ip)
        ec2_client = aws.ec2_client(address['region'])

        if 'association_id' in address and cmd_args.force is False:
            halt.err(f"Elastic IP address {address['ip']} currently in use.",
                "  Append the -f argument to force disassociation.")

        print("")
        if 'association_id' in address:
            ec2_client.disassociate_address(
                AssociationId=address['association_id'])
        ec2_client.release_address(
            AllocationId=address['allocation_id'])

        if 'association_id' in address:
            print(f"Elastic IP address {address['ip']} "
                "disassociated and released.")
        else:
            print(f"Elastic IP address {address['ip']} released.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to be released")
        cmd_parser.add_argument(
            "-f", "--force", action="store_true",
            help="disassociate address if it is in use")


    def blocked_actions(self, cmd_args):
        needed_actions = [
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:ReleaseAddress"
        ]
        if cmd_args.force is True:
            needed_actions.append("ec2:DisassociateAddress")
        return validate_perms.blocked(actions=needed_actions)
