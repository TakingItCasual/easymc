from botocore.exceptions import ClientError

from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.validate import validate_perms

class RequestAddress(CommandBase):

    def main(self, kwargs):
        """attempt to allocate an elastic IP address from AWS

        Args:
            kwargs (dict): See add_documentation method.
        """
        ec2_client = aws.ec2_client(kwargs['region'])

        try:
            allocation_id = ec2_client.allocate_address(
                Domain="vpc",
                Address=kwargs['ip']
            )['AllocationId']
        except ClientError as e:
            if e.response['Error']['Code'] == "InvalidParameterValue":
                halt.err(f"\"{kwargs['ip']}\" is not a valid IPv4 address.")
            if e.response['Error']['Code'] == "InvalidAddress.NotFound":
                halt.err(f"IP \"{kwargs['ip']}\" not available.")
            halt.err(str(e))

        aws.attach_tags(kwargs['region'], allocation_id)

        print("")
        print(f"Elastic IP address {kwargs['ip']} successfully allocated.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to request")
        cmd_parser.add_argument(
            "-r", dest="region", metavar="",
            help="AWS region to place address in")


    def blocked_actions(self, kwargs):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeAddresses",
            "ec2:AllocateAddress"
        ])
