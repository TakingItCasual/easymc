from botocore.exceptions import ClientError

from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

class AssociateAddress(CommandBase):

    def main(self, cmd_args):
        """associate elastic IP address to an (other) instance

        Args:
            cmd_args (dict): See add_documentation method.
        """
        address = find_addresses.main(cmd_args['ip'])
        ec2_client = aws.ec2_client(address['region'])

        all_instances = find_instances.probe_regions()
        try:
            instance = next(instance for instance in all_instances
                if instance['name'] == cmd_args['name'])
        except StopIteration:
            halt.err(f"Instance named \"{cmd_args['name']}\" not found.")

        if instance['region'] != address['region']:
            halt.err("Instance and address are in different regions.")
        if 'instance_name' in address:
            if instance['name'] == address['instance_name']:
                halt.err("Address already associated with specified instance.")

        if 'association_id' in address and cmd_args['force'] is False:
            halt.err(f"Elastic IP address {address['ip']} currently in use.",
                "  Append the -f argument to force disassociation.")

        try:
            if 'association_id' in address:
                ec2_client.disassociate_address(
                    AssociationId=address['association_id'])
            ec2_client.associate_address(
                AllocationId=address['allocation_id'],
                InstanceId=instance['id']
            )
        except ClientError as e:
            halt.err(str(e))

        print("")
        print("Address associated with instance.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "ip", help="IP of elastic IP address to (re)associate")
        cmd_parser.add_argument(
            "name", help="name of instance to associate address with")
        cmd_parser.add_argument(
            "-f", "--force", action="store_true",
            help="disassociate address if it is in use")


    def blocked_actions(self, cmd_args):
        needed_actions = [
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:AssociateAddress"
        ]
        if cmd_args['force'] is True:
            needed_actions.append("ec2:DisassociateAddress")
        return validate_perms.blocked(actions=needed_actions)
