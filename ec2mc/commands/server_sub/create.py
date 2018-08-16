import os
import base64
from time import sleep
from ruamel import yaml
from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc.commands.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.verify import verify_perms

class CreateServer(CommandBase):

    def main(self, kwargs):
        """create and initialize a new EC2 instance

        Args:
            kwargs (dict):
                "template" (str): Config instance setup template name.
                "region" (str): AWS region to create instance in.
                "name" (str): Tag value for instance tag key "Name".
                "confirm" (bool): Whether to actually create the instance.
                "elastic_ip" (bool): Whether to associate a new elastic IP.
                "tags" (list): Additional instance tag key-value pair(s).
        """
        template_yaml_files = os2.list_dir_files(config.USER_DATA_DIR)
        if f"{kwargs['template']}.yaml" not in template_yaml_files:
            halt.err(f"Template {kwargs['template']} not found.")

        inst_template = os2.parse_yaml(f"{config.USER_DATA_DIR}"
            f"{kwargs['template']}.yaml")['ec2mc_template_info']

        self.verify_type_and_size_allowed(
            inst_template['instance_type'], inst_template['volume_size'])

        # Verify the specified region
        if kwargs['region'] not in aws.get_regions():
            halt.err(f"{kwargs['region']} is not a valid region.")
        self.ec2_client = aws.ec2_client(kwargs['region'])

        creation_kwargs = self.parse_run_instance_args(kwargs, inst_template)
        user_data = self.process_user_data(kwargs['template'], inst_template)

        # Instance creation dry run to verify IAM permissions
        try:
            self.create_instance(creation_kwargs, user_data, dry_run=True)
        except ClientError as e:
            if not e.response['Error']['Code'] == "DryRunOperation":
                halt.err(str(e))

        # Actual instance creation occurs after this confirmation.
        if kwargs['confirm'] is False:
            print("")
            print("Specified instance creation args verified as permitted.")
            halt.q("Please append the -c argument to confirm.")

        print("")
        instance = self.create_instance(
            creation_kwargs, user_data, dry_run=False)['Instances'][0]
        print("Instance created.")

        if kwargs['elastic_ip'] is True:
            halt.assert_empty(verify_perms.blocked(actions=[
                "ec2:AllocateAddress",
                "ec2:AssociateAddress"
            ]))
            self.create_and_associate_elastic_ip(instance['InstanceId'])
            print("New elastic IP associated with created instance.")


    def parse_run_instance_args(self, kwargs, instance_template):
        """parse arguments for run_instances from argparse kwargs and template

        Args:
            kwargs (dict):
                "region" (str): AWS region to create instance in.
                "name" (str): Tag value for instance tag key "Name".
                "tags" (list): Additional instance tag key-value pair(s).
            instance_template (dict):
                "AMI_info" (dict):
                    "AMI_ID" (str): EC2 AMI (determines instance OS).
                    "device_name" (str): Device Name for operating system (?).
                    "default_user" (str): AMI's default user (for SSH).
                "instance_type" (str): EC2 instance type to create.
                "volume_size" (int): EC2 instance volume size (GiB).
                "elastic_address" (bool): Whether to associate elastic IP.
                "security_groups" (list[str]): VPC SG(s) to assign to instance.

        Returns:
            dict: Arguments needed for instance creation.
                "ec2_ami" (str): EC2 AMI (determines instance OS).
                "device_name" (str): Device Name for operating system (?).
                "instance_type" (str): EC2 instance type to create.
                "volume_size" (int): EC2 instance size (GiB).
                "tags" (list[dict]): All instance tag key-value pair(s).
                "sg_ids" (list[str]): ID(s) of VPC SG(s) to assign to instance.
                "subnet_id" (str): ID of VPC subnet to assign to instance.
                "key_name" (str): Name of EC2 key pair to assign (for SSH).
        """
        region = kwargs['region']
        ec2_client = aws.ec2_client(region)
        creation_kwargs = {}

        # TODO: Update template AMI to AWS Linux 2 LTS when it comes out
        creation_kwargs.update({
            'ec2_ami': instance_template['AMI_info']['AMI_ID'],
            'device_name': instance_template['AMI_info']['device_name'],
            'instance_type': instance_template['instance_type'],
            'volume_size': instance_template['volume_size']
        })

        creation_kwargs['tags'] = [{
            'Key': "Name",
            'Value': kwargs['name']
        }]
        creation_kwargs['tags'].append({
            'Key': "DefaultUser",
            'Value': instance_template['AMI_info']['default_user']
        })
        if kwargs['tags']:
            for tag_key, tag_value in kwargs['tags']:
                creation_kwargs['tags'].append({
                    'Key': tag_key,
                    'Value': tag_value
                })

        vpc_info = aws.get_region_vpc(region)
        if vpc_info is None:
            halt.err(f"VPC {config.NAMESPACE} not found.",
                "  Have you uploaded the AWS setup?")
        vpc_id = vpc_info['VpcId']
        vpc_sgs = aws.get_region_security_groups(region, vpc_id)
        creation_kwargs['sg_ids'] = [sg['GroupId'] for sg in vpc_sgs
            if sg['GroupName'] in instance_template['security_groups']]

        vpc_subnets = ec2_client.describe_subnets(Filters=[{
            'Name': "vpc-id",
            'Values': [vpc_id]
        }])['Subnets']
        vpc_subnets.sort(key=lambda x: x['AvailabilityZone'])
        creation_kwargs['subnet_id'] = vpc_subnets[0]['SubnetId']

        ec2_key_pairs = ec2_client.describe_key_pairs(Filters=[{
            'Name': "key-name",
            'Values': [config.NAMESPACE]
        }])['KeyPairs']
        if not ec2_key_pairs:
            halt.err(f"EC2 key pair {config.NAMESPACE} not found.",
                "  Have you uploaded the AWS setup?")
        creation_kwargs['key_name'] = ec2_key_pairs[0]['KeyName']

        return creation_kwargs


    def process_user_data(self, template_name, template):
        """add b64 bash scripts to config's user_data write_files

        Args:
            template_name (str): Name of the YAML instance template.
            template (dict):
                "write_directories" (str): Info on directory(s) to copy files 
                    from to user_data's write_files.

        Returns:
            str: YAML file string to initialize instance on first boot.
        """
        user_data = os2.parse_yaml(
            f"{config.USER_DATA_DIR}{template_name}.yaml")

        if 'write_directories' in template:
            template_dir = os.path.join(
                f"{config.USER_DATA_DIR}{template_name}", "")

            write_files = []
            for write_dir in template['write_directories']:
                dir_files = os2.list_dir_files(os.path.join(
                    f"{template_dir}{write_dir['local_dir']}", ""))
                for dir_file in dir_files:
                    file_path = os.path.join(
                        f"{template_dir}{write_dir['local_dir']}", dir_file)
                    with open(file_path) as f:
                        file_b64 = base64.b64encode(bytes(f.read(), "utf-8"))
                    write_files.append({
                        'encoding': "b64",
                        'content': file_b64,
                        'path': f"{write_dir['instance_dir']}{dir_file}"
                    })
                    if 'owner' in write_dir:
                        write_files[-1]['owner'] = write_dir['owner']
                    if 'chmod' in write_dir:
                        write_files[-1]['permissions'] = write_dir['chmod']

            if write_files:
                if 'write_files' not in user_data:
                    user_data['write_files'] = []
                user_data['write_files'].extend(write_files)

        # Halt if write_files has duplicate paths
        if 'write_files' in user_data:
            write_file_paths = [entry['path'] for entry
                in user_data['write_files']]
            if len(write_file_paths) != len(set(write_file_paths)):
                halt.err("Duplicate template write_files paths.")

        # Make user_data valid cloud-config by removing additional setup info
        del user_data['ec2mc_template_info']
        return yaml.dump(user_data, Dumper=yaml.RoundTripDumper)


    def create_instance(self, creation_kwargs, user_data, *, dry_run):
        """create EC2 instance and initialize with user_data

        Args:
            creation_kwargs (dict): See what parse_run_instance_args returns.
            user_data (str): YAML file string to initialize instance on boot.
            dry_run (bool): If True, only test if IAM user is allowed to.
        """
        return self.ec2_client.run_instances(
            DryRun=dry_run,
            KeyName=creation_kwargs['key_name'],
            MinCount=1, MaxCount=1,
            ImageId=creation_kwargs['ec2_ami'],
            InstanceType=creation_kwargs['instance_type'],
            BlockDeviceMappings=[{
                'DeviceName': creation_kwargs['device_name'],
                'Ebs': {'VolumeSize': creation_kwargs['volume_size']}
            }],
            TagSpecifications=[{
                'ResourceType': "instance",
                'Tags': creation_kwargs['tags']
            }],
            SecurityGroupIds=creation_kwargs['sg_ids'],
            SubnetId=creation_kwargs['subnet_id'],
            UserData=user_data
        )


    def create_and_associate_elastic_ip(self, instance_id):
        """attempt to assign elastic IP to instance for 60 seconds"""
        allocation_id = self.ec2_client.allocate_address(
            Domain="vpc")['AllocationId']
        for _ in range(60):
            try:
                self.ec2_client.associate_address(
                    AllocationId=allocation_id,
                    InstanceId=instance_id
                )
                break
            except ClientError as e:
                if e.response['Error']['Code'] != "InvalidInstanceID":
                    halt.err(str(e))
                sleep(1)
        else:
            halt.err("Couldn't assign elastic IP to instance.")


    def verify_type_and_size_allowed(self, instance_type, volume_size):
        """verify user is allowed to create instance with type and size"""
        if verify_perms.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:instance/*"],
                context={'ec2:InstanceType': [instance_type]}):
            halt.err(f"Instance type {instance_type} not permitted.")
        if verify_perms.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:volume/*"],
                context={'ec2:VolumeSize': [volume_size]}):
            halt.err(f"Volume size {volume_size}GiB is too large.")


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "template", help="name of config instance setup template to use")
        cmd_parser.add_argument(
            "region", help="AWS region to create the instance in")
        cmd_parser.add_argument(
            "name", help="value for instance tag key \"Name\"")
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="confirm instance creation")
        cmd_parser.add_argument(
            "-e", "--elastic_ip", action="store_true",
            help="create and associate elastic IP to instance")
        cmd_parser.add_argument(
            "-t", dest="tags", nargs=2, action="append", metavar="",
            help="instance tag key-value pair to attach to instance")


    def blocked_actions(self):
        denied_actions = []
        denied_actions.extend(verify_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeKeyPairs",
            "ec2:CreateTags"
        ]))
        denied_actions.extend(verify_perms.blocked(
            actions=["ec2:RunInstances"],
            resources=["arn:aws:ec2:*:*:instance/*"],
            context={'ec2:InstanceType': ["t2.nano"]}
        ))
        return denied_actions
