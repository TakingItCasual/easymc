import os.path
from deepdiff import DeepDiff

from ec2mc import consts
from ec2mc.commands.base_classes import ComponentSetup
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import os2
from ec2mc.utils.threader import Threader

class VPCSetup(ComponentSetup):

    def check_component(self, config_aws_setup):
        """determine statuses for VPC(s) and SG(s) on AWS

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            tuple:
                dict: Which regions Namespace VPC exists in.
                    'ToCreate' (list): AWS region(s) to create VPC in.
                    'Existing' (list): AWS region(s) already containing VPC.
                dict: VPC security group status(es) for each region.
                    Name of security group (dict):
                        'ToCreate' (list): AWS region(s) to create SG in.
                        'ToUpdate' (list): AWS region(s) to update SG in.
                        'UpToDate' (list): AWS region(s) SG is up to date in.
        """
        regions = aws.get_regions()

        # Region(s) to create VPC in, and region(s) already containing VPC
        vpc_regions = {
            'ToCreate': regions[:],
            'Existing': []
        }

        self.security_group_setup = config_aws_setup['VPC']['SecurityGroups']
        # Status for each SG in each region
        sg_names = {sg_name: {
            'ToCreate': regions[:],
            'ToUpdate': [],
            'UpToDate': []
        } for sg_name in self.security_group_setup}

        vpc_threader = Threader()
        for region in regions:
            vpc_threader.add_thread(aws.get_region_vpc, (region,))
        # VPCs already present in AWS regions
        aws_vpcs = vpc_threader.get_results(return_dict=True)

        # Check each region has VPC with correct Name tag value
        for region in regions:
            if aws_vpcs[region] is not None:
                if ({'Key': "Name", 'Value': consts.NAMESPACE}
                        in aws_vpcs[region]['Tags']):
                    vpc_regions['ToCreate'].remove(region)
                    vpc_regions['Existing'].append(region)
        # TODO: Detect and repair incomplete VPCs (missing subnets, etc.)

        sg_threader = Threader()
        for region in regions:
            if aws_vpcs[region] is not None:
                sg_threader.add_thread(aws.get_vpc_security_groups,
                    (region, aws_vpcs[region]['VpcId']))
        # VPC security groups already present in AWS regions
        aws_sgs = sg_threader.get_results(return_dict=True)

        # Check each region for VPC SG(s) described by aws_setup.json
        for sg_name, sg_regions in sg_names.items():
            for region in regions:
                if aws_vpcs[region] is not None:
                    if any(aws_sg['GroupName'] == sg_name
                            for aws_sg in aws_sgs[region]):
                        sg_regions['ToCreate'].remove(region)
                        sg_regions['ToUpdate'].append(region)

                # Check if existing VPC SG needs to be updated
                if region in sg_regions['ToUpdate']:
                    local_sg_ingress = self.get_json_sg_ingress(sg_name)
                    aws_sg_ingress = next(sg['IpPermissions'] for sg
                        in aws_sgs[region] if sg['GroupName'] == sg_name)

                    sg_ingress_diffs = DeepDiff(
                        local_sg_ingress, aws_sg_ingress, ignore_order=True)

                    if not sg_ingress_diffs:
                        sg_regions['ToUpdate'].remove(region)
                        sg_regions['UpToDate'].append(region)

        return (vpc_regions, sg_names)


    def notify_state(self, vpc_and_sg_info):
        vpc_regions, sg_names = vpc_and_sg_info

        total_regions = len(aws.get_regions())
        existing = len(vpc_regions['Existing'])
        print(f"VPC {consts.NAMESPACE} exists in {existing} of "
            f"{total_regions} AWS regions.")

        for sg_name, sg_regions in sg_names.items():
            to_update_num = len(sg_regions['ToUpdate'])
            exists_num = len(sg_regions['UpToDate']) + to_update_num
            print(f"Local SG {sg_name} exists in {exists_num} of "
                f"{total_regions} AWS regions.")
            if to_update_num > 0:
                print(f"  SG to be updated in {to_update_num} of "
                    f"{exists_num} AWS regions.")


    def upload_component(self, vpc_and_sg_info):
        """create VPC(s) and create/update SG(s) in AWS region(s)

        Args:
            vpc_and_sg_info (dict): See what check_component returns.
        """
        vpc_regions, sg_names = vpc_and_sg_info

        vpc_threader = Threader()
        for region in vpc_regions['ToCreate']:
            vpc_threader.add_thread(self.create_vpc, (region,))
        vpc_threader.get_results()

        create_num = len(vpc_regions['ToCreate'])
        if create_num > 0:
            print(f"VPC {consts.NAMESPACE} created in {create_num} region(s).")
        else:
            print(f"VPC {consts.NAMESPACE} already present in all regions.")

        vpc_ids = {}
        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(aws.get_region_vpc, (region,))
        for region, vpc in threader.get_results(return_dict=True).items():
            if vpc is None:
                halt.err(f"Namespace VPC not created in {region} region.")
            vpc_ids[region] = vpc['VpcId']

        sg_threader = Threader()
        for sg_name, sg_regions in sg_names.items():
            sg_desc = self.security_group_setup[sg_name]
            for region in sg_regions['ToCreate']:
                sg_threader.add_thread(self.create_sg,
                    (region, sg_name, sg_desc, vpc_ids[region]))
            for region in sg_regions['ToUpdate']:
                sg_threader.add_thread(self.update_sg,
                    (region, sg_name, vpc_ids[region]))
        sg_threader.get_results()

        for sg_name, sg_regions in sg_names.items():
            if sg_regions['ToCreate']:
                print(f"VPC SG {sg_name} created in "
                    f"{len(sg_regions['ToCreate'])} region(s).")
            if sg_regions['ToUpdate']:
                print(f"VPC SG {sg_name} updated in "
                    f"{len(sg_regions['ToUpdate'])} region(s).")
            if not sg_regions['ToCreate'] and not sg_regions['ToUpdate']:
                print(f"VPC SG {sg_name} already up to date in all regions.")


    def delete_component(self):
        """delete VPC(s) and associated SG(s) from AWS"""
        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(self.delete_region_vpc, (region,))
        deleted_vpcs = threader.get_results()

        if any(deleted_vpcs):
            print(f"VPC {consts.NAMESPACE} deleted from all AWS regions.")
        else:
            print("No VPCs to delete.")


    @classmethod
    def create_vpc(cls, region):
        """create VPC with subnet(s) in region and attach tags"""
        ec2_client = aws.ec2_client(region)
        vpc_id = ec2_client.create_vpc(
            CidrBlock="172.31.0.0/16",
            AmazonProvidedIpv6CidrBlock=False
        )['Vpc']['VpcId']
        aws.attach_tags(region, vpc_id, consts.NAMESPACE)
        ec2_client.modify_vpc_attribute(
            EnableDnsSupport={'Value': True},
            VpcId=vpc_id
        )
        ec2_client.modify_vpc_attribute(
            EnableDnsHostnames={'Value': True},
            VpcId=vpc_id
        )

        route_table_id = cls.create_internet_gateway(region, vpc_id)
        cls.create_vpc_subnets(region, vpc_id, route_table_id)


    @classmethod
    def delete_region_vpc(cls, region):
        """delete VPC from AWS region with correct Namespace tag"""
        region_vpc = aws.get_region_vpc(region)
        if region_vpc is not None:
            cls.delete_vpc_sgs(region, region_vpc['VpcId'])
            cls.delete_vpc_subnets(region, region_vpc['VpcId'])
            cls.delete_vpc_internet_gateways(region, region_vpc['VpcId'])
            aws.ec2_client(region).delete_vpc(VpcId=region_vpc['VpcId'])
            return True
        return False


    @staticmethod
    def create_internet_gateway(region, vpc_id):
        """create internet gateway, attach it to VPC, and configure route"""
        ec2_client = aws.ec2_client(region)
        ig_id = ec2_client.create_internet_gateway(
            )['InternetGateway']['InternetGatewayId']
        aws.attach_tags(region, ig_id, consts.NAMESPACE)
        ec2_client.attach_internet_gateway(
            InternetGatewayId=ig_id,
            VpcId=vpc_id
        )

        # VPC's automatically created main route table is used
        rt_id = ec2_client.describe_route_tables(Filters=[
            {'Name': "vpc-id", 'Values': [vpc_id]},
            {'Name': "association.main", 'Values': ["true"]}
        ])['RouteTables'][0]['RouteTableId']
        aws.attach_tags(region, rt_id, consts.NAMESPACE)
        ec2_client.create_route(
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=ig_id,
            RouteTableId=rt_id
        )

        return rt_id


    @staticmethod
    def delete_vpc_internet_gateways(region, vpc_id):
        """detach (and delete) internet gateway(s) attached (solely) to VPC"""
        ec2_client = aws.ec2_client(region)
        gateways = ec2_client.describe_internet_gateways(Filters=[{
            'Name': "attachment.vpc-id",
            'Values': [vpc_id]
        }])['InternetGateways']

        for gateway in gateways:
            ec2_client.detach_internet_gateway(
                InternetGatewayId=gateway['InternetGatewayId'],
                VpcId=vpc_id
            )
            # Only delete gateway if attached solely to Namespace VPC
            if len(gateway['Attachments']) == 1:
                ec2_client.delete_internet_gateway(
                    InternetGatewayId=gateway['InternetGatewayId'])


    @staticmethod
    def create_vpc_subnets(region, vpc_id, rt_id):
        """create VPC subnet in AWS region for each availability zone

        Args:
            region (str): Region to create subnets in.
            vpc_id (str): ID of VPC to create subnets under.
            rt_id (str): ID of route table to attach subnets to.
        """
        ec2_client = aws.ec2_client(region)
        azs = ec2_client.describe_availability_zones()['AvailabilityZones']
        for index, az in enumerate(azs):
            if az['State'] != "available":
                continue
            if index*16 >= 256:
                break
            subnet_id = ec2_client.create_subnet(
                AvailabilityZone=az['ZoneName'],
                CidrBlock=f"172.31.{index*16}.0/20",
                VpcId=vpc_id
            )['Subnet']['SubnetId']
            ec2_client.modify_subnet_attribute(
                MapPublicIpOnLaunch={'Value': True},
                SubnetId=subnet_id
            )
            ec2_client.associate_route_table(
                RouteTableId=rt_id,
                SubnetId=subnet_id
            )


    @staticmethod
    def delete_vpc_subnets(region, vpc_id):
        """delete VPC's subnet(s) from AWS region"""
        ec2_client = aws.ec2_client(region)
        vpc_subnets = ec2_client.describe_subnets(Filters=[{
            'Name': "vpc-id",
            'Values': [vpc_id]
        }])['Subnets']
        for vpc_subnet in vpc_subnets:
            ec2_client.delete_subnet(SubnetId=vpc_subnet['SubnetId'])


    @classmethod
    def create_sg(cls, region, sg_name, sg_desc, vpc_id):
        """create new VPC security group on AWS"""
        ec2_client = aws.ec2_client(region)
        sg_id = ec2_client.create_security_group(
            Description=sg_desc,
            GroupName=sg_name,
            VpcId=vpc_id
        )['GroupId']
        aws.attach_tags(region, sg_id, sg_name)

        local_sg_ingress = cls.get_json_sg_ingress(sg_name)
        if local_sg_ingress:
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=local_sg_ingress
            )


    @classmethod
    def update_sg(cls, region, sg_name, vpc_id):
        """update VPC security group that already exists on AWS"""
        ec2_client = aws.ec2_client(region)
        aws_sgs = aws.get_vpc_security_groups(region, vpc_id)

        sg_id = next(sg['GroupId'] for sg in aws_sgs
            if sg['GroupName'] == sg_name)
        aws_sg_ingress = next(sg['IpPermissions'] for sg in aws_sgs
            if sg['GroupName'] == sg_name)
        ec2_client.revoke_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=aws_sg_ingress
        )

        local_sg_ingress = cls.get_json_sg_ingress(sg_name)
        if local_sg_ingress:
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=local_sg_ingress
            )


    @staticmethod
    def delete_vpc_sgs(region, vpc_id):
        """delete VPC's security group(s) from AWS region"""
        ec2_client = aws.ec2_client(region)
        aws_sgs = aws.get_vpc_security_groups(region, vpc_id)
        for aws_sg in aws_sgs:
            ec2_client.delete_security_group(GroupId=aws_sg['GroupId'])


    @staticmethod
    def get_json_sg_ingress(sg_name):
        """retrieve local security group ingress rule(s) dict"""
        security_group_dir = os.path.join(
            f"{consts.AWS_SETUP_DIR}vpc_security_groups", "")
        return os2.parse_json(f"{security_group_dir}{sg_name}.json")['Ingress']


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "ec2:DescribeRegions",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeAvailabilityZones",
            "ec2:DescribeRouteTables",
            "ec2:DescribeInternetGateways"
        ]
        self.upload_actions = [
            "ec2:CreateVpc",
            "ec2:CreateTags",
            "ec2:ModifyVpcAttribute",
            "ec2:CreateInternetGateway",
            "ec2:AttachInternetGateway",
            "ec2:CreateRouteTable",
            "ec2:CreateRoute",
            "ec2:CreateSubnet",
            "ec2:ModifySubnetAttribute",
            "ec2:AssociateRouteTable",
            "ec2:CreateSecurityGroup",
            "ec2:RevokeSecurityGroupIngress",
            "ec2:AuthorizeSecurityGroupIngress"
        ]
        self.delete_actions = [
            "ec2:DeleteSecurityGroup",
            "ec2:DeleteSubnet",
            "ec2:DetachInternetGateway",
            "ec2:DeleteInternetGateway",
            "ec2:DeleteVpc"
        ]
        return super().blocked_actions(sub_command)
