import os
import base64
from ruamel import yaml
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc import command_template
from ec2mc.stuff import aws
from ec2mc.stuff import os2
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import halt

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

        inst_templates = os2.parse_json(config.INSTANCE_TEMPLATES_JSON)
        try:
            inst_template = next(template for template in inst_templates
                if template["TemplateName"] == kwargs["template"])
        except StopIteration:
            halt.err(["Template " + kwargs["template"] + " not found."])

        self.verify_type_and_size_allowed(
            inst_template["InstanceType"], inst_template["VolumeSize"])

        # Verify the specified region
        self.ec2_client = aws.ec2_client(
            aws.get_regions([kwargs["region"]])[0])

        creation_kwargs = self.parse_run_instance_args(kwargs, inst_template)
        user_data = self.process_user_data(inst_template)

        # Instance creation dry run to verify IAM permissions
        try:
            self.create_instance(creation_kwargs, user_data, dry_run=True)
        except ClientError as e:
            if not e.response["Error"]["Code"] == "DryRunOperation":
                halt.err([str(e)])

        # Actual instance creation occurs after this confirmation.
        if kwargs["confirm"] is False:
            print("")
            print("Specified instance creation args verified as permitted.")
            halt.q(["Please append the -c argument to confirm."])

        instance = self.create_instance(
            creation_kwargs, user_data, dry_run=False)["Instances"][0]


    def parse_run_instance_args(self, kwargs, instance_template):
        """parse arguments for run_instances from argparse kwargs and template

        Args:
            kwargs (dict):
                "region" (str): EC2 region to create instance in.
                "name" (str): Tag value for instance tag key "Name".
                "tags" (list): Additional instance tag key-value pair(s).
            instance_template (dict):
                "AmazonMachineImage" (str): EC2 AMI (determines instance OS).
                "DeviceName" (str): Device Name for operating system (?).
                "InstanceType" (str): EC2 instance type to create.
                "VolumeSize" (int): EC2 instance volume size (GiB).
                "DefaultUser" (str): AMI's default user (for SSH).
                "SecurityGroups" (list[str]): VPC SG(s) to assign to instance.

        Returns:
            dict: Arguments needed for instance creation.
                "ec2_ami" (str): EC2 AMI (determines instance OS).
                "device_name" (str): Device Name for operating system (?).
                "instance_type" (str): EC2 instance type to create.
                "volume_size" (int): EC2 instance size (GiB).
                "tags" (list[dict]): All instance tag key-value pair(s).
                "sg_ids" (list[str]): ID(s) of VPC SG(s) to assign to instance.
                "subnet_id" (str): ID of VPC subnet to assign to instance.
        """

        region = kwargs["region"]
        ec2_client = aws.ec2_client(region)
        creation_kwargs = {}

        # TODO: Update template AMI to AWS Linux 2 LTS when it comes out
        creation_kwargs["ec2_ami"] = instance_template["AmazonMachineImage"]
        creation_kwargs["device_name"] = instance_template["DeviceName"]
        creation_kwargs["instance_type"] = instance_template["InstanceType"]
        creation_kwargs["volume_size"] = instance_template["VolumeSize"]

        creation_kwargs["tags"] = [{
            "Key": "Name",
            "Value": kwargs["name"]
        }]
        creation_kwargs["tags"].append({
            "Key": "DefaultUser",
            "Value": instance_template["DefaultUser"]
        })
        if kwargs["tags"]:
            for tag_key, tag_value in kwargs["tags"]:
                creation_kwargs["tags"].append({
                    "Key": tag_key,
                    "Value": tag_value
                })

        vpc_info = aws.get_region_vpc(region)
        if vpc_info is None:
            halt.err(["VPC " + config.NAMESPACE + " not found.",
                "  Have you uploaded the AWS setup?"])
        vpc_id = vpc_info["VpcId"]
        vpc_sgs = aws.get_region_security_groups(region, vpc_id)
        vpc_sg_ids = [sg["GroupId"] for sg in vpc_sgs
            if sg["GroupName"] in instance_template["SecurityGroups"]]
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


    def process_user_data(self, template):
        """add b64 bash scripts to config's user_data write_files

        Args:
            template (dict):
                "TemplateName": (str): Name of the user data YAML file.
                "WriteFilesPath" (str): Where to place write_files on instance.

        Returns:
            str: YAML file string to initialize instance on first boot.
        """

        user_data_dir = os.path.join((config.AWS_SETUP_DIR + "user_data"), "")
        user_data_dict = os2.parse_yaml(
            user_data_dir + template["TemplateName"] + ".yaml")

        if "WriteDirectories" in template:
            template_dir = os.path.join(
                (user_data_dir + template["TemplateName"]), "")

            write_files = []
            for write_dir in template["WriteDirectories"]:
                dir_files = os2.list_dir_files(
                    template_dir + write_dir["LocalDir"])
                for dir_file in dir_files:
                    file_path = os.path.join(
                        (template_dir + write_dir["LocalDir"]), dir_file)
                    with open(file_path) as f:
                        file_b64 = base64.b64encode(bytes(f.read(), "utf-8"))
                    write_files.append({
                        "encoding": "b64",
                        "content": file_b64,
                        "path": template["WriteFilesPath"] + dir_file
                    })
                    if "Owner" in write_dir:
                        write_files[-1]["owner"] = write_dir["Owner"]
                    if "chmod" in write_dir:
                        write_files[-1]["permissions"] = write_dir["chmod"]

            if write_files:
                if "write_files" not in user_data_dict:
                    user_data_dict["write_files"] = []
                user_data_dict["write_files"].extend(write_files)

        return yaml.dump(user_data_dict, Dumper=yaml.RoundTripDumper)


    def create_instance(self, creation_kwargs, user_data, *, dry_run):
        """create EC2 instance

        Args:
            creation_kwargs (dict): See what parse_run_instance_args returns.
            user_data (str): YAML file string to initialize instance on boot.
            dry_run (bool): If True, only test if IAM user is allowed to.
        """

        return self.ec2_client.run_instances(
            DryRun=dry_run,
            MinCount=1, MaxCount=1,
            ImageId=creation_kwargs["ec2_ami"],
            InstanceType=creation_kwargs["instance_type"],
            BlockDeviceMappings=[{
                "DeviceName": creation_kwargs["device_name"],
                "Ebs": {"VolumeSize": creation_kwargs["volume_size"]}
            }],
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": creation_kwargs["tags"]
            }],
            SecurityGroupIds=creation_kwargs["sg_ids"],
            SubnetId=creation_kwargs["subnet_id"],
            UserData=user_data
        )


    def verify_type_and_size_allowed(self, instance_type, volume_size):
        """verify user is allowed to create instance with type and size"""
        if simulate_policy.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:instance/*"],
                context={"ec2:InstanceType": [instance_type]}):
            halt.err(["Instance type " + instance_type + " not permitted."])
        if simulate_policy.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:volume/*"],
                context={"ec2:VolumeSize": [volume_size]}):
            halt.err(["Volume size " + str(volume_size) + "GiB is too large."])


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
