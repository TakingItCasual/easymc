from botocore.exceptions import ClientError

from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.validate import validate_perms

class RequestAddress(CommandBase):

    def main(self, kwargs):
        """attempt to allocate an elastic IP address from AWS

        Args:
            kwargs (dict): See add_documentation method.
        """
        self.ec2_client = aws.ec2_client(kwargs['region'])

        if kwargs['ip'] is not None:
            response = self.request_specific_address(
                kwargs['region'], kwargs['ip'])
        else:
            response = self.request_random_address()

        aws.attach_tags(kwargs['region'], response['AllocationId'])
        public_ip = response['PublicIp']

        print("")
        print(f"Elastic IP address {public_ip} successfully allocated.")


    def request_specific_address(self, region, ipv4_ip):
        """request specific IPv4 elastic IP address from AWS"""
        for address in find_addresses.probe_regions():
            if address['ip'] == ipv4_ip:
                if region is not None and region != address['region']:
                    halt.err("You already possess this elastic IP address.",
                        f"  It is located in the {address['region']} region.")
                halt.err("You already possess this elastic IP address.")

        try:
            return self.ec2_client.allocate_address(
                Domain="vpc",
                Address=ipv4_ip
            )
        except ClientError as e:
            if e.response['Error']['Code'] == "InvalidParameterValue":
                halt.err(f"\"{ipv4_ip}\" is not a valid IPv4 address.")
            if e.response['Error']['Code'] == "InvalidAddress.NotFound":
                halt.err(f"IP \"{ipv4_ip}\" not available.")
            halt.err(str(e))


    def request_random_address(self):
        """request random IPv4 elastic IP address from AWS"""
        try:
            return self.ec2_client.allocate_address(Domain="vpc")
        except ClientError as e:
            halt.err(str(e))


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", nargs="?", help="IP of elastic IP address to request")
        cmd_parser.add_argument(
            "-r", dest="region", metavar="",
            help="AWS region to place address in")


    def blocked_actions(self, kwargs):
        return validate_perms.blocked(actions=[
            "ec2:DescribeAddresses",
            "ec2:AllocateAddress"
        ])
