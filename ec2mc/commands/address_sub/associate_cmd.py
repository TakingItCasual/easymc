from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.validate import validate_perms

class AssociateAddress(CommandBase):

    def main(self, kwargs):
        """associate elastic IP address with (another) instance

        Args:
            kwargs (dict): See add_documentation method.
        """
        ec2_client = aws.ec2_client(kwargs['region'])


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to (re)associate")
        cmd_parser.add_argument(
            "id", help="ID of instance to associate address to")
        cmd_parser.add_argument(
            "-r", dest="region", metavar="",
            help="AWS region the address is located in")


    def blocked_actions(self, kwargs):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeAddresses"
        ])
