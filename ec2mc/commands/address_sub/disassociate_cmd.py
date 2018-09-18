from botocore.exceptions import ClientError

from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.validate import validate_perms

class DisassociateAddress(CommandBase):

    def main(self, cmd_args):
        """disassociate elastic IP address from its instance

        Args:
            cmd_args (dict): See add_documentation method.
        """
        address = find_addresses.main(cmd_args['ip'])
        ec2_client = aws.ec2_client(address['region'])

        if 'association_id' not in address:
            halt.err("Elastic IP address not associated to anything.")

        try:
            ec2_client.disassociate_address(
                AssociationId=address['association_id'])
        except ClientError as e:
            halt.err(str(e))

        print("")
        print("Elastic IP address disassociated.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to disassociate")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:DisassociateAddress"
        ])
