import os.path
import base64
from time import sleep
from ruamel import yaml
from botocore.exceptions import ClientError

from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils import pem
from ec2mc.validate import validate_instances
from ec2mc.validate import validate_perms

# TODO: Consider allowing elastic IP address reassociation
class CreateServer(CommandBase):

    def main(self, kwargs):
        """create and initialize a new EC2 instance

        Args:
            kwargs (dict):
                'template' (str): Config instance setup template name.
                'region' (str): AWS region to create instance in.
                'name' (str): Tag value for instance tag key "Name".
                'confirm' (bool): Whether to actually create the instance.
                'elastic_ip' (bool): Whether to associate a new elastic IP.
                'tags' (list): Additional instance tag key-value pair(s).
        """
        template_yaml_files = os2.list_dir_files(consts.USER_DATA_DIR)
        if f"{kwargs['template']}.yaml" not in template_yaml_files:
            halt.err(f"Template {kwargs['template']} not found from config.")

        self.ec2_client = aws.ec2_client(kwargs['region'])

        self.validate_name_is_unique(kwargs['name'])

        inst_template = os2.parse_yaml(f"{consts.USER_DATA_DIR}"
            f"{kwargs['template']}.yaml")['ec2mc_template_info']

        self.validate_type_and_size_allowed(
            inst_template['instance_type'], inst_template['volume_size'])
        if kwargs['use_ip'] is not None:
            self.validate_address_available(kwargs['use_ip'])

        creation_kwargs = self.parse_run_instance_args(kwargs, inst_template)
        user_data = self.process_user_data(kwargs['template'], inst_template)

        # Instance creation dry run to validate template and IAM permissions
        try:
            self.create_instance(creation_kwargs, user_data, dry_run=True)
        except ClientError as e:
            if not e.response['Error']['Code'] == "DryRunOperation":
                halt.err(str(e))

        print("")
        if kwargs['confirm'] is False:
            print("Instance template validated.")
            print("Please append the -c argument to confirm.")
        else:
            instance = self.create_instance(
                creation_kwargs, user_data, dry_run=False)
            print("Instance created. It may take a few minutes to initialize.")
            if consts.USE_HANDLER is True:
                print("  Utilize IP handler with \"ec2mc servers check\".")

            if kwargs['elastic_ip'] is True:
                self.create_elastic_ip(
                    kwargs['region'], instance['InstanceId'])
                print("New elastic IP associated with created instance.")
            elif kwargs['use_ip'] is not None:
                self.reuse_elastic_ip(
                    instance['InstanceId'], kwargs['use_ip'])
                print("Existing elastic IP associated with created instance.")


    def parse_run_instance_args(self, kwargs, instance_template):
        """parse arguments for run_instances from argparse kwargs and template

        Args:
            kwargs (dict):
                'region' (str): AWS region to create instance in.
                'name' (str): Tag value for instance tag key "Name".
                'tags' (list): Additional instance tag key-value pair(s).
            instance_template (dict):
                'AMI_info' (dict):
                    'AMI_name' (str): EC2 image name (determines instance OS).
                    'default_user' (str): AMI's default user (for SSH).
                'instance_type' (str): EC2 instance type to create.
                'volume_size' (int): EC2 instance volume size (GiB).
                'security_groups' (list[str]): VPC SG(s) to assign to instance.
                'ip_handler' (str): Local IpHandler script to handle IPs with.

        Returns:
            dict: Arguments needed for instance creation.
                'ami_id' (str): EC2 image ID (determines instance OS).
                'device_name' (str): Device Name for operating system (?).
                'instance_type' (str): EC2 instance type to create.
                'volume_size' (int): EC2 instance size (GiB).
                'tags' (list[dict]): All instance tag key-value pair(s).
                'sg_ids' (list[str]): ID(s) of VPC SG(s) to assign to instance.
                'subnet_id' (str): ID of VPC subnet to assign to instance.
                'key_name' (str): Name of EC2 key pair to assign (for SSH).
        """
        region = kwargs['region']
        creation_kwargs = {}

        creation_kwargs.update({
            'instance_type': instance_template['instance_type'],
            'volume_size': instance_template['volume_size']
        })

        aws_images = self.ec2_client.describe_images(Filters=[{
            'Name': "name",
            'Values': [instance_template['AMI_info']['AMI_name']]
        }])['Images']
        if not aws_images:
            halt.err("Template's AWS image name not found from AWS.")
        creation_kwargs.update({
            'ami_id': aws_images[0]['ImageId'],
            'device_name': aws_images[0]['RootDeviceName']
        })

        vpc_info = aws.get_region_vpc(region)
        if vpc_info is None:
            halt.err(f"VPC {consts.NAMESPACE} not found from AWS region.",
                "  Have you uploaded the AWS setup?")
        vpc_id = vpc_info['VpcId']

        creation_kwargs.update({
            'tags': self.parse_tags(kwargs, instance_template),
            'key_name': self.validate_ec2_key_pair(),
            'sg_ids': self.template_security_groups(
                region, vpc_id, instance_template['security_groups']),
            'subnet_id': self.first_subnet_id(vpc_id)
        })

        return creation_kwargs


    @staticmethod
    def process_user_data(template_name, template):
        """add b64 template files to user_data's write_files

        Args:
            template_name (str): Name of the YAML instance template.
            template (dict):
                'write_directories' (str): Info on template subdirectory(s) to
                    copy files from to user_data's write_files.

        Returns:
            str: YAML file string to initialize instance on first boot.
        """
        user_data = os2.parse_yaml(
            f"{consts.USER_DATA_DIR}{template_name}.yaml")

        if 'write_directories' in template:
            template_dir = os.path.join(
                f"{consts.USER_DATA_DIR}{template_name}", "")

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
                        'content': file_b64.decode("utf-8"),
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
        user_data_str = yaml.dump(user_data, Dumper=yaml.RoundTripDumper)

        return f"#cloud-config\n{user_data_str}"


    def create_instance(self, creation_kwargs, user_data, *, dry_run):
        """create EC2 instance and initialize with user_data

        Args:
            creation_kwargs (dict): See what parse_run_instance_args returns.
            user_data (str): cloud-config to initialize instance on boot.
            dry_run (bool): If True, only test if IAM user is allowed to.
        """
        return self.ec2_client.run_instances(
            DryRun=dry_run,
            KeyName=creation_kwargs['key_name'],
            MinCount=1, MaxCount=1,
            ImageId=creation_kwargs['ami_id'],
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
        )['Instances'][0]


    def create_elastic_ip(self, region, instance_id):
        """allocate new elastic IP to AWS account, and associate to instance"""
        allocation_id = self.ec2_client.allocate_address(
            Domain="vpc")['AllocationId']
        aws.attach_tags(region, allocation_id)
        self.associate_elastic_ip(instance_id, allocation_id)


    def reuse_elastic_ip(self, instance_id, elastic_ip):
        """associate already owned unassociated elastic IP to instance"""
        allocation_id = self.ec2_client.describe_addresses(
            Filters=[{'Name': "domain", 'Values': ["vpc"]}],
            PublicIps=[elastic_ip]
        )['Addresses'][0]['AllocationId']
        self.associate_elastic_ip(instance_id, allocation_id)


    def associate_elastic_ip(self, instance_id, allocation_id):
        """attempt to assign elastic IP to instance for 60 seconds"""
        for _ in range(60):
            try:
                self.ec2_client.associate_address(
                    AllocationId=allocation_id,
                    InstanceId=instance_id,
                    AllowReassociation=False
                )
                break
            except ClientError as e:
                if e.response['Error']['Code'] != "InvalidInstanceID":
                    halt.err(str(e))
                sleep(1)
        else:
            halt.err("Couldn't assign elastic IP to instance.")


    @staticmethod
    def validate_type_and_size_allowed(instance_type, volume_size):
        """validate user is allowed to create instance with type and size"""
        if validate_perms.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:instance/*"],
                context={'ec2:InstanceType': [instance_type]}):
            halt.err(f"Instance type {instance_type} not permitted.")
        if validate_perms.blocked(actions=["ec2:RunInstances"],
                resources=["arn:aws:ec2:*:*:volume/*"],
                context={'ec2:VolumeSize': [volume_size]}):
            halt.err(f"Volume size {volume_size}GiB is too large.")


    def validate_address_available(self, elastic_ip):
        """validate elastic IP address is owned and not attached to anything"""
        addresses = self.ec2_client.describe_addresses(Filters=[
            {'Name': "domain", 'Values': ["vpc"]}
        ])['Addresses']
        for address in addresses:
            if address['PublicIp'] == elastic_ip:
                if 'AssociationId' in address:
                    halt.err(f"Elastic IP {elastic_ip} currently in use.")
                break
        else:
            halt.err(f"Elastic IP {elastic_ip} not owned by AWS account.")


    @staticmethod
    def validate_name_is_unique(instance_name):
        """validate desired instance name isn't in use by another instance"""
        all_instances = validate_instances.probe_regions(consts.REGIONS)
        instance_names = [instance['name'] for instance in all_instances]
        if instance_name in instance_names:
            halt.err(f"Instance name {instance_name} already in use.")


    @staticmethod
    def parse_tags(kwargs, instance_template):
        """handle tag parsing for parse_run_instance_args method"""
        instance_tags = [
            {
                'Key': "Name",
                'Value': kwargs['name']
            },
            {
                'Key': "Namespace",
                'Value': consts.NAMESPACE
            },
            {
                'Key': "DefaultUser",
                'Value': instance_template['AMI_info']['default_user']
            }
        ]
        if kwargs['tags']:
            for tag_key, tag_value in kwargs['tags']:
                instance_tags.append({
                    'Key': tag_key,
                    'Value': tag_value
                })
        if instance_template['ip_handler'] is not None:
            instance_tags.append({
                'Key': "IpHandler",
                'Value': instance_template['ip_handler']
            })
        return instance_tags


    @staticmethod
    def template_security_groups(region, vpc_id, security_groups):
        """return VPC security group ID(s)"""
        vpc_sgs = aws.get_vpc_security_groups(region, vpc_id)
        return [sg['GroupId'] for sg in vpc_sgs
            if sg['GroupName'] in security_groups]


    def first_subnet_id(self, vpc_id):
        """return ID of VPC's first subnet (alphabetically ordered)"""
        vpc_subnets = self.ec2_client.describe_subnets(Filters=[{
            'Name': "vpc-id",
            'Values': [vpc_id]
        }])['Subnets']
        vpc_subnets.sort(key=lambda k: k['AvailabilityZone'])
        return vpc_subnets[0]['SubnetId']


    def validate_ec2_key_pair(self):
        """validate EC2 key pair exists, and matches local RSA key file"""
        ec2_key_pairs = self.ec2_client.describe_key_pairs(Filters=[{
            'Name': "key-name",
            'Values': [consts.NAMESPACE]
        }])['KeyPairs']
        if not ec2_key_pairs:
            halt.err(f"EC2 key pair {consts.NAMESPACE} not found from AWS.",
                "  Have you uploaded the AWS setup?")
        if not os.path.isfile(consts.RSA_PRIV_KEY_PEM):
            rsa_key_file = os.path.basename(consts.RSA_PRIV_KEY_PEM)
            halt.err(f"{rsa_key_file} not found from config.")
        if pem.local_key_fingerprint() != ec2_key_pairs[0]['KeyFingerprint']:
            halt.err("Local RSA key fingerprint doesn't match EC2 key pair's.")
        return ec2_key_pairs[0]['KeyName']


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="AWS region to create the instance in")
        cmd_parser.add_argument(
            "template", help="instance setup template in config to use")
        cmd_parser.add_argument(
            "name", help="value for instance's tag key \"Name\"")
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="confirm instance creation")
        cmd_parser.add_argument(
            "-t", dest="tags", nargs=2, action="append", metavar="",
            help="instance tag key-value pair to attach to instance")
        elastic_ip_group = cmd_parser.add_mutually_exclusive_group()
        elastic_ip_group.add_argument(
            "-e", "--elastic_ip", action="store_true",
            help="create new elastic IP and associate to instance")
        elastic_ip_group.add_argument(
            "--use_ip", metavar="",
            help="owned elastic IP address to associate to instance")


    def blocked_actions(self, kwargs):
        denied_actions = validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeKeyPairs",
            "ec2:DescribeImages",
            "ec2:CreateTags"
        ])
        denied_actions.extend(validate_perms.blocked(
            actions=["ec2:RunInstances"],
            resources=["arn:aws:ec2:*:*:instance/*"],
            context={'ec2:InstanceType': ["t2.nano"]}
        ))
        if kwargs['elastic_ip'] is True:
            denied_actions.extend(validate_perms.blocked(actions=[
                "ec2:AllocateAddress",
                "ec2:AssociateAddress"
            ]))
        elif kwargs['use_ip'] is not None:
            denied_actions.extend(validate_perms.blocked(actions=[
                "ec2:DescribeAddresses",
                "ec2:AssociateAddress"
            ]))
        return denied_actions
