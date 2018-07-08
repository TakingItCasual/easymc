from ec2mc.commands import template
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.verify import verify_perms

class DeleteServer(template.BaseClass):

    def main(self, kwargs):
        """terminate an EC2 instance, given its region, ID, and name

        Args:
            kwargs (dict):
                "region" (str): AWS region to terminate instance from.
                "id" (str): ID of instance to terminate.
                "name" (str): Tag value for instance tag key "Name".
        """

        # Verify the specified region
        if kwargs["region"] not in aws.get_regions():
            halt.err(kwargs["region"] + " is not a valid region.")
        ec2_client = aws.ec2_client(kwargs["region"])

        reservations = ec2_client.describe_instances(Filters=[
            {
                "Name": "instance-id",
                "Values": [kwargs["id"]]
            },
            {
                "Name": "tag:Name",
                "Values": [kwargs["name"]]
            }
        ])["Reservations"]
        if not reservations:
            halt.err("No instances matching given parameters found.")

        elastic_ips = ec2_client.describe_addresses(Filters=[{
            "Name": "instance-id",
            "Values": [kwargs["id"]]
        }])["Addresses"]
        # If instance has an associated elastic IP, disassociate and release
        print("")
        if elastic_ips:
            halt.assert_empty(verify_perms.blocked(actions=[
                "ec2:DisassociateAddress",
                "ec2:ReleaseAddress"
            ]))

            ec2_client.disassociate_address(
                AssociationId=elastic_ips[0]["AssociationId"])
            ec2_client.release_address(
                AllocationId=elastic_ips[0]["AllocationId"])
            print("Instance's elastic IP disassociated and released.")

        ec2_client.terminate_instances(InstanceIds=[kwargs["id"]])
        print("Instance terminated.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="region of instance to be terminated")
        cmd_parser.add_argument(
            "id", help="ID of instance to terminate")
        cmd_parser.add_argument(
            "name", help="value for instance's tag key \"Name\"")


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses",
            "ec2:TerminateInstances"
        ])
