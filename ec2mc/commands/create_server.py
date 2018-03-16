from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc import command_template
from ec2mc.verify import verify_aws
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class CreateServer(command_template.BaseClass):

    def main(self, kwargs):
        """create and initialize a new Minecraft instance/server

        Args:
            kwargs (dict):
                "region": EC2 region to create instance in
                "name": Tag value for instance tag key "Name"
                "type": EC2 instance type to create
                "tags": list: Additional instance tag key-value pair(s)
                "confirm" (bool): Whether to actually create the instance
        """

        # Verify the specified region
        aws.get_regions([kwargs["region"]])[0]
        self.ec2_client = aws.ec2_client(kwargs["region"])

        self.init_run_instance_args(kwargs)

        # Instance creation dry run to verify IAM permissions
        try:
            self.create_instance(dry_run=True)
        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                print("")
                pp.pprint(aws.decode_error_msg(e.response))
                quit_out.err(["Missing action/resource/context IAM "
                    "permission(s).",
                    "  The above JSON is the decoded error message.",
                    "  Maybe specified instance storage/type was too large?"])
            elif not e.response["Error"]["Code"] == "DryRunOperation":
                quit_out.q([e])

        # Actual instance creation occurs after this confirmation.
        if not kwargs["confirm"]:
            print("")
            print("Specified instance creation args verified as permitted.")
            quit_out.q(["Please append the -c argument to confirm."])


    def init_run_instance_args(self, kwargs):
        """initialize the necessary arguments for run_instances

        Args:
            kwargs (dict):
                "region": EC2 region to create instance in
                "name": Tag value for instance tag key "Name"
                "type": EC2 instance type to create
                "tags": list: Additional instance tag key-value pair(s)
        """

        # TODO: Figure out some way to filter VPCs
        vpc_stuff = self.ec2_client.describe_network_interfaces(
        )["NetworkInterfaces"]
        if not vpc_stuff:
            quit_out.err(["Default VPC not found."])
        elif len(vpc_stuff) > 1:
            quit_out.err(["Multiple VPCs found."])
        self.availability_zone = vpc_stuff[0]["AvailabilityZone"]

        self.instance_type = kwargs["type"]

        self.storage_amount = kwargs["size"]

        self.tags = [{
            "Key": "Name",
            "Value": kwargs["name"]
        }]
        if kwargs["tags"]:
            for tag_key, tag_value in kwargs["tags"]:
                self.tags.append({
                    "Key": tag_key,
                    "Value": tag_value
                })

        self.security_group_id = verify_aws.security_group(kwargs["region"])


    def create_instance(self, *, dry_run=True):
        """create an EC2 instance

        Args:
            dry_run (bool): If true, only test if IAM user is allowed to
        """
        # TODO: Figure out how to limit EBS volume size with the IAM policy
        return self.ec2_client.run_instances(
            DryRun=dry_run,
            MinCount=1, MaxCount=1,
            ImageId=config.EC2_OS_AMI,
            Placement={"AvailabilityZone": self.availability_zone},
            InstanceType=self.instance_type,
            BlockDeviceMappings=[{
                "DeviceName": config.DEVICE_NAME,
                "Ebs": {
                    "VolumeSize": self.storage_amount
                }
            }],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": self.tags
            }],
            SecurityGroupIds=[self.security_group_id]
        )


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="EC2 region for the instance to be created in")
        cmd_parser.add_argument(
            "name", help="instance Name tag value")
        cmd_parser.add_argument(
            "type", help="instance type (larger is more expensive)")
        cmd_parser.add_argument(
            "size", help="instance storage amount (in GiB)", type=int)
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="confirm instance creation")
        cmd_parser.add_argument(
            "-t", dest="tags", nargs=2, action="append", metavar="",
            help="instance tag key and tag value to attach to instance")


    def blocked_actions(self, _):
        denied_actions = []
        denied_actions.extend(simulate_policy.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:DescribeNetworkInterfaces",
            "ec2:CreateTags"
        ]))
        denied_actions.extend(simulate_policy.blocked(actions=[
            "ec2:RunInstances"
        ], resources=[
            "arn:aws:ec2:*:*:instance/*"
        ], context={
            "ec2:InstanceType": ["t2.nano"]
        }))
        return denied_actions


    def module_name(self):
        return super().module_name(__name__)
