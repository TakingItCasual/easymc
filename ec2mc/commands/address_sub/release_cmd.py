from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.validate import validate_perms

class ReleaseAddress(CommandBase):

    def main(self, kwargs):
        """release elastic IP address (give up ownership)

        Args:
            kwargs (dict): See add_documentation method.
        """
        ec2_client = aws.ec2_client(kwargs['region'])

        addresses = ec2_client.describe_addresses(Filters=[
            {'Name': "domain", 'Values': ["vpc"]},
            {'Name': "tag:Namespace", 'Values': [consts.NAMESPACE]},
            {'Name': "public-ip", 'Values': [kwargs['ip']]}
        ])['Addresses']

        if not addresses:
            halt.err("You do not own the specified elastic IP address.")
        address = addresses[0]

        if 'AssociationId' in address and kwargs['force'] is False:
            halt.err("Elastic IP address is currently in use.",
                "Append the -f argument to force disassociation.")

        print("")
        if 'AssociationId' in address:
            ec2_client.disassociate_address(
                AssociationId=address['AssociationId'])
            print(f"Elastic IP address disassociated.")

        ec2_client.release_address(
            AllocationId=address['AllocationId'])
        print(f"Elastic IP address {kwargs['ip']} released.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="AWS region of elastic IP address to be released")
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to be released")
        cmd_parser.add_argument(
            "-f", "--force", action="store_true",
            help="disassociate address if it is in use")


    def blocked_actions(self, kwargs):
        needed_actions = [
            "ec2:DescribeRegions",
            "ec2:DescribeAddresses",
            "ec2:ReleaseAddress"
        ]
        if kwargs['force'] is True:
            needed_actions.append("ec2:DisassociateAddress")
        return validate_perms.blocked(actions=needed_actions)
