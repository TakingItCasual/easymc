from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class DeleteServer(CommandBase):

    def __init__(self, cmd_args):
        self._ec2_client = aws.ec2_client(cmd_args.region)


    def main(self, cmd_args):
        """terminate an EC2 instance given its ID and name

        Args:
            cmd_args (namedtuple): See add_documentation method.
        """
        reservations = self._ec2_client.describe_instances(Filters=[
            {'Name': "instance-id", 'Values': [cmd_args.id]},
            {'Name': "tag:Name", 'Values': [cmd_args.name]}
        ])['Reservations']
        if not reservations:
            halt.err("No instances matching given parameters found.")
        instance_state = reservations[0]['Instances'][0]['State']['Name']
        if instance_state in ("shutting-down", "terminated"):
            halt.err("Instance has already been terminated.")

        addresses = self._ec2_client.describe_addresses(Filters=[
            {'Name': "instance-id", 'Values': [cmd_args.id]}
        ])['Addresses']
        print("")
        if addresses:
            self._disassociate_addresses(addresses, cmd_args.save_ips)
        elif cmd_args.save_ips is True:
            print("No elastic IPs associated with instance.")

        self._ec2_client.terminate_instances(InstanceIds=[cmd_args.id])
        print("Instance termination process started.")


    def _disassociate_addresses(self, addresses, preserve_ips):
        """disassociate (and release) elastic IP(s) associated with instance"""
        needed_actions = ["ec2:DisassociateAddress"]
        if preserve_ips is False:
            needed_actions.append("ec2:ReleaseAddress")
        halt.assert_empty(validate_perms.blocked(actions=needed_actions))

        for address in addresses:
            self._ec2_client.disassociate_address(
                AssociationId=address['AssociationId'])
            if preserve_ips is False:
                self._ec2_client.release_address(
                    AllocationId=address['AllocationId'])
                print(f"Elastic IP {address['PublicIp']} "
                    "disassociated and released.")
            else:
                print(f"Elastic IP {address['PublicIp']} "
                    "disassociated but preserved.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "id", help="ID of instance to terminate")
        cmd_parser.add_argument(
            "name", help="value for instance's tag key \"Name\"")
        cmd_parser.add_argument(
            "-s", "--save_ips", action="store_true",
            help="do not release associated elastic IP address(es)")
        cmd_parser.add_argument(
            "-r", dest="region", metavar="",
            help="AWS region the instance is located in")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:TerminateInstances"
        ])
