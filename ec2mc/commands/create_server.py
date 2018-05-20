from ruamel.yaml import YAML
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
                "region" (str): EC2 region to create instance in.
                "name" (str): Tag value for instance tag key "Name".
                "tags" (list): Additional instance tag key-value pair(s).
                "confirm" (bool): Whether to actually create the instance.
        """

        inst_templates = quit_out.parse_json(config.INSTANCE_TEMPLATES_JSON)
        try:
            inst_template = next(template for template in inst_templates
                if template["TemplateName"] == kwargs["template"])
        except StopIteration:
            quit_out.err(["Template " + kwargs["template"] + " not found."])

        self.verify_type_and_size_allowed(
            inst_template["InstanceType"], inst_template["VolumeSize"])

        # Verify the specified region
        aws.get_regions([kwargs["region"]])
        self.ec2_client = aws.ec2_client(kwargs["region"])

        creation_kwargs = self.parse_run_instance_args(
            kwargs["region"], kwargs["name"], kwargs["tags"],
            inst_template["InstanceType"], inst_template["VolumeSize"],
            inst_template["SecurityGroups"])

        # Instance creation dry run to verify IAM permissions
        try:
            self.create_instance(creation_kwargs, dry_run=True)
        except ClientError as e:
            if not e.response["Error"]["Code"] == "DryRunOperation":
                quit_out.err([str(e)])

        # Actual instance creation occurs after this confirmation.
        if not kwargs["confirm"]:
            print("")
            print("Specified instance creation args verified as permitted.")
            quit_out.q(["Please append the -c argument to confirm."])


    def parse_run_instance_args(self,
            region, inst_name, inst_tags, inst_type, vol_size, inst_sgs):
        """parse arguments for run_instances from argparse kwargs

        Args:
            "region" (str): EC2 region to create instance in.
            "inst_name" (str): Tag value for instance tag key "Name".
            "inst_tags" (list): Additional instance tag key-value pair(s).
            "inst_type" (str): EC2 instance type to create.
            "vol_size" (int): EC2 instance volume size (GiB).
            "inst_sgs" (list[str]): VPC SG(s) to assign to instance.

        Returns:
            dict: Arguments needed for instance creation.
                "instance_type" (str): EC2 instance type to create.
                "storage_size" (int): EC2 instance size in GiB.
                "tags" (list[dict]): All instance tag key-value pair(s).
                "sg_ids" (list[str]): ID(s) of VPC SG(s) to assign to instance.
                "subnet_id" (str): ID of VPC subnet to assign to instance.
        """

        ec2_client = aws.ec2_client(region)
        creation_kwargs = {}

        creation_kwargs["instance_type"] = inst_type
        creation_kwargs["storage_size"] = vol_size

        creation_kwargs["tags"] = [{
            "Key": "Name",
            "Value": inst_name
        }]
        if inst_tags:
            for tag_key, tag_value in inst_tags:
                creation_kwargs["tags"].append({
                    "Key": tag_key,
                    "Value": tag_value
                })

        vpc_info = aws.get_region_vpc(region)
        if not vpc_info:
            quit_out.err(["VPC " + config.NAMESPACE + " not found.",
                "  Have you uploaded the AWS setup?"])
        vpc_id = vpc_info[0]["VpcId"]
        vpc_sgs = aws.get_region_security_groups(region, vpc_id)
        vpc_sg_ids = [sg["GroupId"] for sg in vpc_sgs
            if sg["GroupName"] in inst_sgs]
        creation_kwargs["sg_ids"] = vpc_sg_ids

        vpc_subnets = ec2_client.describe_subnets(
            Filters=[{
                "Name": "vpc-id",
                "Values": [vpc_id]
            }]
        )["Subnets"]
        vpc_subnets.sort(key=lambda x: x["AvailabilityZone"])
        creation_kwargs["subnet_id"] = vpc_subnets[0]["SubnetId"]

        return creation_kwargs


    def parse_user_data(self):
        """add b64 bash scripts to config's user_data write_files"""
        pass


    def create_instance(self, creation_kwargs, *, dry_run=True):
        """create EC2 instance

        Args:
            creation_kwargs (dict): See what parse_run_instance_args returns.
            dry_run (bool): If true, only test if IAM user is allowed to.
        """

        return self.ec2_client.run_instances(
            DryRun=dry_run,
            MinCount=1, MaxCount=1,
            ImageId=config.EC2_OS_AMI,
            InstanceType=creation_kwargs["instance_type"],
            BlockDeviceMappings=[{
                "DeviceName": config.DEVICE_NAME,
                "Ebs": {
                    "VolumeSize": creation_kwargs["storage_size"]
                }
            }],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": creation_kwargs["tags"]
            }],
            SecurityGroupIds=creation_kwargs["sg_ids"],
            SubnetId=creation_kwargs["subnet_id"]
        )


    def verify_type_and_size_allowed(self, instance_type, storage_size):
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
            "template", help="name of config instance setup template to use")
        cmd_parser.add_argument(
            "region", help="EC2 region for the instance to be created in")
        cmd_parser.add_argument(
            "name", help="instance Name tag value")
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="confirm instance creation")
        cmd_parser.add_argument(
            "-t", dest="tags", nargs=2, action="append", metavar="",
            help="instance tag key-value pair to attach to instance")


    def blocked_actions(self, _):
        denied_actions = []
        denied_actions.extend(simulate_policy.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
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
