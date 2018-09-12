from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.validate import validate_perms

class DeleteServer(CommandBase):

    def main(self, kwargs):
        """terminate an EC2 instance, given its region, ID, and name

        Args:
            kwargs (dict):
                'region' (str): AWS region to terminate instance from.
                'id' (str): ID of instance to terminate.
                'name' (str): Tag value for instance tag key "Name".
        """
        self.ec2_client = aws.ec2_client(kwargs['region'])

        reservations = self.ec2_client.describe_instances(Filters=[
            {'Name': "instance-id", 'Values': [kwargs['id']]},
            {'Name': "tag:Name", 'Values': [kwargs['name']]}
        ])['Reservations']
        if not reservations:
            halt.err("No instances matching given parameters found.")
        instance_state = reservations[0]['Instances'][0]['State']['Name']
        if instance_state in ("shutting-down", "terminated"):
            halt.err("Instance has already been terminated.")

        elastic_ips = self.ec2_client.describe_addresses(Filters=[{
            'Name': "instance-id",
            'Values': [kwargs['id']]
        }])['Addresses']
        print("")
        if elastic_ips:
            self.disassociate_addresses(elastic_ips, kwargs['save_ip'])
        elif kwargs['save_ip'] is True:
            print("No elastic IPs associated with instance.")

        self.ec2_client.terminate_instances(InstanceIds=[kwargs['id']])
        print("Instance termination process started.")


    def disassociate_addresses(self, elastic_ips, preserve_ips):
        """disassociate (and release) elastic IP(s) associated with instance"""
        needed_actions = ["ec2:DisassociateAddress"]
        if preserve_ips is False:
            needed_actions.append("ec2:ReleaseAddress")
        halt.assert_empty(validate_perms.blocked(actions=needed_actions))

        for elastic_ip in elastic_ips:
            self.ec2_client.disassociate_address(
                AssociationId=elastic_ip['AssociationId'])
            if preserve_ips is False:
                self.ec2_client.release_address(
                    AllocationId=elastic_ip['AllocationId'])
                print(f"Elastic IP {elastic_ip['PublicIp']} "
                    "disassociated and released.")
            else:
                print(f"Elastic IP {elastic_ip['PublicIp']} "
                    "disassociated but preserved.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="region of instance to be terminated")
        cmd_parser.add_argument(
            "id", help="ID of instance to terminate")
        cmd_parser.add_argument(
            "name", help="value for instance's tag key \"Name\"")
        cmd_parser.add_argument(
           "-s", "--save_ip", action="store_true",
            help="preserve any associated elastic IP")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:TerminateInstances"
        ])
