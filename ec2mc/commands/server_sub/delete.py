import os.path

from ec2mc import consts
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.validate import validate_perms

class DeleteServer(CommandBase):

    def main(self, kwargs):
        """terminate an EC2 instance, given its region, ID, and name

        Args:
            kwargs (dict):
                "region" (str): AWS region to terminate instance from.
                "id" (str): ID of instance to terminate.
                "name" (str): Tag value for instance tag key "Name".
        """
        # Validate specified region
        if kwargs['region'] not in aws.get_regions():
            halt.err(f"{kwargs['region']} is not a valid region.")
        ec2_client = aws.ec2_client(kwargs['region'])

        reservations = ec2_client.describe_instances(Filters=[
            {'Name': "instance-id", 'Values': [kwargs['id']]},
            {'Name': "tag:Name", 'Values': [kwargs['name']]}
        ])['Reservations']
        if not reservations:
            halt.err("No instances matching given parameters found.")
        instance_state = reservations[0]['Instances'][0]['State']['Name']
        if instance_state in ("shutting-down", "terminated"):
            halt.err("Instance has already been terminated.")

        elastic_ips = ec2_client.describe_addresses(Filters=[{
            'Name': "instance-id",
            'Values': [kwargs['id']]
        }])['Addresses']
        # If elastic IP(s) associated with instance, disassociate and release
        print("")
        if elastic_ips:
            halt.assert_empty(validate_perms.blocked(actions=[
                "ec2:DisassociateAddress",
                "ec2:ReleaseAddress"
            ]))

            for elastic_ip in elastic_ips:
                ec2_client.disassociate_address(
                    AssociationId=elastic_ip['AssociationId'])
                if kwargs['save_ip'] is False:
                    ec2_client.release_address(
                        AllocationId=elastic_ip['AllocationId'])
                    print(f"Elastic IP {elastic_ip['PublicIp']} "
                        "disassociated and released.")
                else:
                    print(f"Elastic IP {elastic_ip['PublicIp']} "
                        "disassociated but preserved.")
        elif kwargs['save_ip'] is True:
            print("No elastic IPs associated with instance.")

        ec2_client.terminate_instances(InstanceIds=[kwargs['id']])
        print("Instance terminated.")

        # Remove instance entry from server_titles.json, if present
        if os.path.isfile(consts.SERVER_TITLES_JSON):
            titles_dict = os2.parse_json(consts.SERVER_TITLES_JSON)
            for index, server_title in enumerate(titles_dict['Instances']):
                if (server_title['region'] == kwargs['region'] and
                        server_title['id'] == kwargs['id']):
                    del titles_dict['Instances'][index]
                    os2.save_json(titles_dict, consts.SERVER_TITLES_JSON)


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


    def blocked_actions(self):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:TerminateInstances"
        ])
