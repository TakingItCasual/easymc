from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc import command_template
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

        self.check_type_size_permissions(kwargs["type"], kwargs["size"])

        # Verify the specified region
        aws.get_regions([kwargs["region"]])
        self.ec2_client = aws.ec2_client(kwargs["region"])

        creation_kwargs = self.parse_run_instance_args(kwargs)

        # Instance creation dry run to verify IAM permissions
        try:
            self.create_instance(creation_kwargs, dry_run=True)
        except ClientError as e:
            if not e.response["Error"]["Code"] == "DryRunOperation":
                quit_out.err([e])

        # Actual instance creation occurs after this confirmation.
        if not kwargs["confirm"]:
            print("")
            print("Specified instance creation args verified as permitted.")
            quit_out.q(["Please append the -c argument to confirm."])


    def parse_run_instance_args(self, kwargs):
        """parse arguments for run_instances from argparse kwargs

        Args:
            kwargs (dict):
                "region": EC2 region to create instance in.
                "name": Tag value for instance tag key "Name".
                "type": EC2 instance type to create.
                "size": EC2 instance size in GiB.
                "tags" (list): Additional instance tag key-value pair(s).

        Returns:
            creation_kwargs (dict):
                "availability_zone": EC2 region's availability zone to create 
                    instance in.
                "instance_type": EC2 instance type to create.
                "storage_size": EC2 instance size in GiB.
                "tags" (list): Additional instance tag key-value pair(s).
                "sg_id": ID of VPC security group to attach to instance.
        """

        creation_kwargs = {}

        # TODO: Figure out some way to filter VPCs
        vpc_stuff = self.ec2_client.describe_network_interfaces(
        )["NetworkInterfaces"]
        if not vpc_stuff:
            quit_out.err(["Default VPC not found."])
        elif len(vpc_stuff) > 1:
            quit_out.err(["Multiple VPCs found."])
        creation_kwargs["availability_zone"] = vpc_stuff[0]["AvailabilityZone"]

        creation_kwargs["instance_type"] = kwargs["type"]
        creation_kwargs["storage_size"] = kwargs["size"]

        creation_kwargs["tags"] = [{
            "Key": "Name",
            "Value": kwargs["name"]
        }]
        if kwargs["tags"]:
            for tag_key, tag_value in kwargs["tags"]:
                creation_kwargs["tags"].append({
                    "Key": tag_key,
                    "Value": tag_value
                })

        creation_kwargs["sg_id"] = aws.security_group_id(kwargs["region"])

        return creation_kwargs


    def create_instance(self, kwargs, *, dry_run=True):
        """create EC2 instance

        Args:
            kwargs (dict): See what parse_run_instance_args returns
            dry_run (bool): If true, only test if IAM user is allowed to
        """

        return self.ec2_client.run_instances(
            DryRun=dry_run,
            MinCount=1, MaxCount=1,
            ImageId=config.EC2_OS_AMI,
            #Placement={"AvailabilityZone": kwargs["availability_zone"]},
            InstanceType=kwargs["instance_type"],
            BlockDeviceMappings=[{
                "DeviceName": config.DEVICE_NAME,
                "Ebs": {
                    "VolumeSize": kwargs["storage_size"]
                }
            }],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": kwargs["tags"]
            }],
            SecurityGroupIds=[kwargs["sg_id"]]
        )


    def check_type_size_permissions(self, instance_type, storage_size):
        """verify user is allowed to create instance with type and size"""
        if simulate_policy.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:instance/*"],
                context={"ec2:InstanceType": [instance_type]}):
            quit_out.err([
                "Instance type " + instance_type + " not permitted."])
        if simulate_policy.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:volume/*"],
                context={"ec2:VolumeSize": [storage_size]}):
            quit_out.err([
                "Storage amount " + str(storage_size) + "GiB too large."])


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
            help="instance tag key-value pair to attach to instance")
        cmd_parser.add_argument(
            "--sg", dest="sec_grp", metavar="",
            help="VPC security group to place instance under")


    def blocked_actions(self, _):
        denied_actions = []
        denied_actions.extend(simulate_policy.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DescribeSecurityGroups",
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
