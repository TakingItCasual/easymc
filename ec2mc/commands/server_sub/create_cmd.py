from time import sleep
from ruamel import yaml

from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils import pem
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.utils.find import find_instances
from ec2mc.validate import validate_perms

class CreateServer(CommandBase):

    def __init__(self, cmd_args):
        self.ec2_client = aws.ec2_client(cmd_args['region'])


    def main(self, cmd_args):
        """create and initialize a new EC2 instance

        Args:
            cmd_args (dict): See add_documentation method.
        """
        template_yaml_files = os2.dir_files(consts.USER_DATA_DIR)
        if f"{cmd_args['template']}.yaml" not in template_yaml_files:
            halt.err(f"Template {cmd_args['template']} not found from config.")

        self.validate_name_is_unique(cmd_args['name'])
        self.validate_limits_not_reached(cmd_args['elastic_ip'])

        inst_template = os2.parse_yaml(consts.USER_DATA_DIR /
            f"{cmd_args['template']}.yaml")['ec2mc_template_info']

        self.validate_type_and_size_allowed(
            inst_template['instance_type'], inst_template['volume_size'])
        if cmd_args['use_ip'] is not None:
            address = self.validate_address(
                cmd_args['use_ip'], cmd_args['region'], cmd_args['force'])

        creation_kwargs = self.parse_run_instance_args(cmd_args, inst_template)
        user_data = self.process_user_data(cmd_args['template'], inst_template)
        self.create_instance(creation_kwargs, user_data, dry_run=True)

        print("")
        if cmd_args['confirm'] is False:
            print("IAM permissions and instance template validated.")
            print("Append the -c argument to confirm instance creation.")
            return

        instance = self.create_instance(
            creation_kwargs, user_data, dry_run=False)
        print("Instance created. It may take a few minutes to initialize.")
        if consts.USE_HANDLER is True:
            print("  Utilize IP handler with \"ec2mc servers check\".")

        if cmd_args['elastic_ip'] is True:
            self.create_elastic_ip(cmd_args['region'], instance['InstanceId'])
            print("New elastic IP associated with created instance.")
        elif cmd_args['use_ip'] is not None:
            self.reuse_elastic_ip(address, instance['InstanceId'])
            print("Existing elastic IP associated with created instance.")


    def parse_run_instance_args(self, cmd_args, instance_template):
        """parse arguments for run_instances from argparse args and template

        Args:
            cmd_args (dict):
                'region' (str): AWS region to create instance in.
                'name' (str): Tag value for instance tag key "Name".
                'tags' (list): Additional instance tag key-value pair(s).
            instance_template (dict):
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
        region = cmd_args['region']
        creation_kwargs = {}

        creation_kwargs.update({
            'instance_type': instance_template['instance_type'],
            'volume_size': instance_template['volume_size']
        })

        aws_images = self.ec2_client.describe_images(Filters=[
            {'Name': "name", 'Values': [consts.AMI_NAME]}
        ])['Images']
        if not aws_images:
            halt.err("AMI name specified by script is invalid.")
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
            'tags': self.parse_tags(cmd_args, instance_template),
            'key_name': self.validate_ec2_key_pair(),
            'sg_ids': self.template_security_groups(
                region, vpc_id, instance_template['security_groups']),
            'subnet_id': self.first_subnet_id(vpc_id)
        })

        return creation_kwargs


    @classmethod
    def process_user_data(cls, template_name, template):
        """add template files to user_data's write_files

        Args:
            template_name (str): Name of the YAML instance template.
            template (dict):
                'write_directories' (str): Info on template subdirectory(s) to
                    copy files from to user_data's write_files.

        Returns:
            str: YAML file string to initialize instance on first boot.
        """
        user_data = os2.parse_yaml(
            consts.USER_DATA_DIR / f"{template_name}.yaml")

        if 'write_directories' in template:
            write_files = cls.generate_write_files(
                template_name, template['write_directories'])
            if write_files:
                if 'write_files' not in user_data:
                    user_data['write_files'] = []
                user_data['write_files'].extend(write_files)

        # Halt if write_files contains any duplicate paths
        if 'write_files' in user_data:
            write_file_paths = [write_file['path'] for write_file
                in user_data['write_files']]
            if len(write_file_paths) != len(set(write_file_paths)):
                halt.err("Duplicate template write_files paths.")

        # Make user_data valid cloud-config by removing additional setup info
        del user_data['ec2mc_template_info']
        user_data_str = yaml.dump(user_data, Dumper=yaml.RoundTripDumper)

        return f"#cloud-config\n{user_data_str}"


    # TODO: Make this recursively search local_dirs
    @staticmethod
    def generate_write_files(template_name, write_dirs):
        """fill out write_files list from template directory"""
        template_dir = consts.USER_DATA_DIR / template_name
        write_files = []
        for write_dir in write_dirs:
            dir_files = os2.dir_files(template_dir / write_dir['local_dir'])
            for dir_file in dir_files:
                file_path = template_dir / write_dir['local_dir'] / dir_file
                # Convert Windows line endings to Unix line endings
                file_bytes = file_path.read_bytes().replace(b"\r\n", b"\n")
                write_files.append({
                    'content': file_bytes,
                    'path': f"{write_dir['instance_dir']}{dir_file}"
                })
                if 'owner' in write_dir:
                    write_files[-1]['owner'] = write_dir['owner']
                if 'chmod' in write_dir:
                    write_files[-1]['permissions'] = write_dir['chmod']
        return write_files


    def create_instance(self, creation_kwargs, user_data, *, dry_run):
        """create EC2 instance and initialize with user_data

        Args:
            creation_kwargs (dict): See what parse_run_instance_args returns.
            user_data (str): cloud-config to initialize instance on boot.
            dry_run (bool): If True, only test if IAM user is allowed to.
        """
        with aws.ClientErrorHalt(allow=["DryRunOperation"]):
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
        """allocate new elastic IP address, and associate with instance"""
        with aws.ClientErrorHalt():
            allocation_id = self.ec2_client.allocate_address(
                Domain="vpc")['AllocationId']

        aws.attach_tags(region, allocation_id)
        self.associate_elastic_ip(instance_id, allocation_id)


    def reuse_elastic_ip(self, address, instance_id):
        """associate already owned elastic IP with instance"""
        if 'association_id' in address:
            self.ec2_client.disassociate_address(
                AssociationId=address['association_id'])
        self.associate_elastic_ip(instance_id, address['allocation_id'])


    def associate_elastic_ip(self, instance_id, allocation_id):
        """attempt to assign elastic IP to instance for 60 seconds"""
        for _ in range(60):
            with aws.ClientErrorHalt(allow=["InvalidInstanceID"]):
                self.ec2_client.associate_address(
                    AllocationId=allocation_id,
                    InstanceId=instance_id,
                    AllowReassociation=False
                )
                break
            sleep(1)
        else:
            halt.err("Couldn't assign elastic IP to instance.")


    @staticmethod
    def validate_name_is_unique(instance_name):
        """validate desired instance name isn't in use by another instance"""
        all_instances = find_instances.probe_regions()
        instance_names = [instance['name'] for instance in all_instances]
        if instance_name in instance_names:
            halt.err(f"Instance name \"{instance_name}\" already in use.")


    def validate_limits_not_reached(self, allocate_address):
        """validate instance/address limits haven't been reached"""
        attributes = self.ec2_client.describe_account_attributes(
            AttributeNames=["max-instances", "vpc-max-elastic-ips"]
        )['AccountAttributes']
        max_instances = int(next(
            attribute['AttributeValues'][0]['AttributeValue']
            for attribute in attributes
            if attribute['AttributeName'] == "max-instances"))
        max_addresses = int(next(
            attribute['AttributeValues'][0]['AttributeValue']
            for attribute in attributes
            if attribute['AttributeName'] == "vpc-max-elastic-ips"))

        instance_count = sum(len(reservation['Instances']) for reservation
            in self.ec2_client.describe_instances()['Reservations'])
        if instance_count >= max_instances:
            halt.err(f"You cannot possess more than {max_instances} "
                "instances in this region.")

        if allocate_address is True:
            address_count = len(self.ec2_client.describe_addresses(Filters=[
                {'Name': "domain", 'Values': ["vpc"]}
            ])['Addresses'])
            if address_count >= max_addresses:
                halt.err(f"You cannot possess more than {max_addresses} "
                    "elastic IP addresses in this region.")


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


    @staticmethod
    def validate_address(elastic_ip, region, force_disassociation):
        """validate elastic IP address exists and is available"""
        address = find_addresses.main(elastic_ip)
        if 'association_id' in address and force_disassociation is False:
            halt.err(f"Elastic IP address {elastic_ip} currently in use.",
                "  Append the -f argument to force disassociation.")
        if region is not None and region != address['region']:
            halt.err(f"Elastic IP address is not in the {region} region.")
        return address


    @staticmethod
    def parse_tags(cmd_args, instance_template):
        """handle tag parsing for parse_run_instance_args method"""
        instance_tags = [
            {'Key': "Name", 'Value': cmd_args['name']},
            {'Key': "Namespace", 'Value': consts.NAMESPACE},
            {'Key': "DefaultUser", 'Value': consts.AMI_DEFAULT_USER}
        ]
        if cmd_args['tags']:
            for tag_key, tag_value in cmd_args['tags']:
                instance_tags.append({'Key': tag_key, 'Value': tag_value})
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
        vpc_sg_names = [sg['GroupName'] for sg in vpc_sgs]
        if not set(security_groups).issubset(set(vpc_sg_names)):
            halt.err("Following template SG(s) not found from AWS:",
                *(set(security_groups) - set(vpc_sg_names)))
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
        if not consts.RSA_KEY_PEM.is_file():
            halt.err(f"{consts.RSA_KEY_PEM.name} not found from config.")
        if pem.local_key_fingerprint() != ec2_key_pairs[0]['KeyFingerprint']:
            halt.err("Local RSA key fingerprint doesn't match EC2 key pair's.")
        return ec2_key_pairs[0]['KeyName']


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="value for instance's tag key \"Name\"")
        cmd_parser.add_argument(
            "template", help="instance setup template in config to use")
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="confirm instance creation")
        cmd_parser.add_argument(
            "-t", dest="tags", nargs=2, action="append", metavar="",
            help="instance tag key-value pair to attach to instance")
        cmd_parser.add_argument(
            "-r", dest="region", metavar="",
            help="AWS region to create the instance in")
        cmd_group = cmd_parser.add_mutually_exclusive_group()
        cmd_group.add_argument(
            "--elastic_ip", action="store_true",
            help="create new elastic IP and associate with instance")
        cmd_group.add_argument(
            "--use_ip", metavar="",
            help="possessed elastic IP address to associate with instance")
        cmd_parser.add_argument(
            "-f", "--force", action="store_true",
            help="disassociate possessed elastic IP address if it is in use")


    def blocked_actions(self, cmd_args):
        needed_actions = [
            "ec2:DescribeInstances",
            "ec2:DescribeAccountAttributes",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeKeyPairs",
            "ec2:DescribeImages",
            "ec2:CreateTags"
        ]
        if cmd_args['elastic_ip'] is True:
            needed_actions.extend([
                "ec2:DescribeAddresses",
                "ec2:AllocateAddress",
                "ec2:AssociateAddress"
            ])
        elif cmd_args['use_ip'] is not None:
            needed_actions.extend([
                "ec2:DescribeAddresses",
                "ec2:AssociateAddress"
            ])
            if cmd_args['force'] is True:
                needed_actions.append("ec2:DisassociateAddress")

        denied_actions = validate_perms.blocked(actions=needed_actions)
        denied_actions.extend(validate_perms.blocked(
            actions=["ec2:RunInstances"],
            resources=["arn:aws:ec2:*:*:instance/*"],
            context={'ec2:InstanceType': ["t2.nano"]}
        ))
        return denied_actions
