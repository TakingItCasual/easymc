from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.validate import validate_perms

class ReleaseAddress(CommandBase):

    def main(self, kwargs):
        """release elastic IP address (give up ownership)

        Args:
            kwargs (dict):
                'region' (str): Region of elastic IP address to be released.
                'ip' (str): IP of elastic IP address to be released.
        """
        ec2_client = aws.ec2_client(kwargs['region'])

        addresses = ec2_client.describe_addresses(Filters=[
            {'Name': "domain", 'Values': ["vpc"]},
            {'Name': "tag:Namespace", 'Values': [consts.NAMESPACE]},
            {'Name': "public-ip", 'Values': [kwargs['ip']]}
        ])['Addresses']

        if not addresses:
            halt.err("You do not own the specified elastic IP address.")

        print("")
        if 'AssociationId' in addresses[0]:
            ec2_client.disassociate_address(
                AssociationId=addresses[0]['AssociationId'])
            print(f"Elastic IP address disassociated.")

        ec2_client.release_address(
            AllocationId=addresses[0]['AllocationId'])
        print(f"Elastic IP address {kwargs['ip']} released.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="region of elastic IP address to be released")
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to be released")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeAddresses",
            "ec2:DisassociateAddress",
            "ec2:ReleaseAddress"
        ])
