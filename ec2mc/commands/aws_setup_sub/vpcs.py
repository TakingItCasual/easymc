import os.path

from ec2mc import config
from ec2mc.commands.aws_setup_sub import template
from ec2mc.utils import aws
from ec2mc.utils import os2
from ec2mc.utils.threader import Threader

class VPCSetup(template.BaseClass):

    def verify_component(self, config_aws_setup):
        """determine statuses for VPC(s) and SG(s) on AWS

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            tuple:
                dict: Which regions Namespace VPC exists in.
                    "ToCreate" (list): AWS region(s) to create VPC in.
                    "Existing" (list): AWS region(s) already containing VPC.
                dict: VPC security group status(es) for each region.
                    Name of security group (dict):
                        "ToCreate" (list): AWS region(s) to create SG in.
                        "ToUpdate" (list): AWS region(s) to update SG in.
                        "UpToDate" (list): AWS region(s) already containing SG.
        """

        regions = aws.get_regions()

        self.vpc_name = config.NAMESPACE
        # Region(s) to create VPC in, and region(s) already containing VPC
        vpc_regions = {
            'ToCreate': regions[:],
            'Existing': []
        }

        self.security_group_dir = os.path.join(
            f"{config.AWS_SETUP_DIR}vpc_security_groups", "")
        self.security_group_setup = config_aws_setup['EC2']['SecurityGroups']
        # Information for each SG and its status in each region
        sg_names = {sg['Name']: {
            'ToCreate': regions[:],
            'ToUpdate': [],
            'UpToDate': []
        } for sg in self.security_group_setup}

        vpc_threader = Threader()
        sg_threader = Threader()
        for region in regions:
            vpc_threader.add_thread(aws.get_region_vpc, (region,))
            sg_threader.add_thread(aws.get_region_security_groups, (region,))
        # VPCs already present in AWS regions
        aws_vpcs = vpc_threader.get_results(return_dict=True)
        # VPC security groups already present in AWS regions
        aws_sgs = sg_threader.get_results(return_dict=True)

        # Check each region for VPC with with correct Name tag value
        for region in regions:
            if aws_vpcs[region] is not None:
                if ({'Key': "Name", 'Value': self.vpc_name}
                        in aws_vpcs[region]['Tags']):
                    vpc_regions['ToCreate'].remove(region)
                    vpc_regions['Existing'].append(region)
        # TODO: Detect and create missing subnets for existing VPCs

        # Check each region for SG(s) described by aws_setup.json
        for sg_name, sg_regions in sg_names.items():
            for region in regions:
                if aws_vpcs[region] is not None:
                    if any(aws_sg['GroupName'] == sg_name and
                            aws_sg['VpcId'] == aws_vpcs[region]['VpcId']
                            for aws_sg in aws_sgs[region]):
                        sg_regions['ToCreate'].remove(region)
                        sg_regions['UpToDate'].append(region)

                if region in sg_regions['ToUpdate']:
                    # TODO: Detect if AWS security group should be updated
                    pass

        return (vpc_regions, sg_names)


    def notify_state(self, vpc_and_sg_info):
        vpc_regions, sg_names = vpc_and_sg_info

        total_regions = len(aws.get_regions())
        existing = len(vpc_regions['Existing'])
        print(f"VPC {self.vpc_name} exists in {existing} of "
            f"{total_regions} AWS regions.")

        for sg_name, sg_regions in sg_names.items():
            up_to_date = len(sg_regions['UpToDate'])
            print(f"Local SG {sg_name} exists in {up_to_date} of "
                f"{total_regions} AWS regions.")


    def upload_component(self, vpc_and_sg_info):
        """create VPC(s) and create/update SG(s) in AWS region(s)

        Args:
            vpc_and_sg_info (dict): See what verify_component returns.
        """

        vpc_regions, sg_names = vpc_and_sg_info

        vpc_threader = Threader()
        for region in vpc_regions['ToCreate']:
            vpc_threader.add_thread(self.create_vpc, (region,))
        vpc_threader.get_results()

        create_count = len(vpc_regions['ToCreate'])
        if create_count > 0:
            print(f"VPC {self.vpc_name} created in {create_count} region(s).")
        else:
            print(f"VPC {self.vpc_name} already present in all regions.")

        sg_threader = Threader()
        for sg_name, sg_regions in sg_names.items():
            for region in sg_regions['ToCreate']:
                sg_threader.add_thread(self.create_sg, (region, sg_name))
            for region in sg_regions['ToUpdate']:
                sg_threader.add_thread(self.update_sg, (region, sg_name))
        sg_threader.get_results()

        for sg_name, sg_regions in sg_names.items():
            if sg_regions['ToCreate']:
                print(f"VPC SG {sg_name} created in "
                    f"{len(sg_regions['ToCreate'])} region(s).")
            if sg_regions['ToUpdate']:
                print(f"VPC SG {sg_name} updated in "
                    f"{len(sg_regions['ToUpdate'])} region(s).")
            if not sg_regions['ToCreate'] and not sg_regions['ToUpdate']:
                print(f"VPC SG {sg_name} already present in all regions.")


    def delete_component(self):
        """delete VPC(s) and associated SG(s) from AWS"""

        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(self.delete_region_vpc, (region,))
        deleted_vpcs = threader.get_results()

        if any(deleted_vpcs):
            print(f"VPC {self.vpc_name} deleted from all AWS regions.")
        else:
            print("No VPCs to delete.")


    def create_vpc(self, region):
        """create VPC with subnet(s) in region and attach tags"""

        ec2_client = aws.ec2_client(region)
        vpc_id = ec2_client.create_vpc(
            CidrBlock="172.31.0.0/16",
            AmazonProvidedIpv6CidrBlock=False
        )['Vpc']['VpcId']
        aws.attach_tags(ec2_client, vpc_id, self.vpc_name)
        ec2_client.modify_vpc_attribute(
            EnableDnsSupport={'Value': True},
            VpcId=vpc_id
        )
        ec2_client.modify_vpc_attribute(
            EnableDnsHostnames={'Value': True},
            VpcId=vpc_id
        )

        ig_id = self.create_internet_gateway(region, vpc_id)
        rt_id = self.create_vpc_route_table(region, vpc_id, ig_id)
        self.create_vpc_subnets(region, vpc_id, rt_id)


    def delete_region_vpc(self, region):
        """delete VPC from AWS region with correct Namespace tag"""
        region_vpc = aws.get_region_vpc(region)
        if region_vpc is not None:
            self.delete_vpc_sgs(region, region_vpc['VpcId'])
            self.delete_vpc_subnets(region, region_vpc['VpcId'])
            aws.ec2_client(region).delete_vpc(VpcId=region_vpc['VpcId'])
            return True
        return False


    def create_internet_gateway(self, region, vpc_id):
        """create internet gateway and attach it to VPC"""
        ec2_client = aws.ec2_client(region)
        ig_id = ec2_client.create_internet_gateway(
            )['InternetGateway']['InternetGatewayId']
        aws.attach_tags(ec2_client, ig_id, self.vpc_name)
        ec2_client.attach_internet_gateway(
            InternetGatewayId=ig_id,
            VpcId=vpc_id
        )
        return ig_id


    def delete_vpc_internet_gateways(self, region, vpc_id):
        """delete internet gateways attached solely to VPC"""
        pass


    def create_vpc_route_table(self, region, vpc_id, ig_id):
        """create route table and configure route with internet gateway"""
        ec2_client = aws.ec2_client(region)
        rt_id = ec2_client.create_route_table(VpcId=vpc_id)['RouteTableId']
        aws.attach_tags(ec2_client, rt_id, self.vpc_name)
        ec2_client.create_route(
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=ig_id,
            RouteTableId=rt_id
        )
        return rt_id


    def delete_vpc_route_tables(self, vpc_id):
        """delete VPC route tables"""
        pass


    def create_vpc_subnets(self, region, vpc_id, rt_id):
        """create EC2 VPC subnets on AWS region in each availability zone

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
            ec2_client.associate_route_table(
                RouteTableId=rt_id,
                SubnetId=subnet_id
            )


    def delete_vpc_subnets(self, region, vpc_id):
        """delete EC2 VPC subnets from AWS region for VPC"""
        ec2_client = aws.ec2_client(region)
        vpc_subnets = ec2_client.describe_subnets(
            Filters=[{
                'Name': "vpc-id",
                'Values': [vpc_id]
            }]
        )['Subnets']
        for vpc_subnet in vpc_subnets:
            ec2_client.delete_subnet(SubnetId=vpc_subnet['SubnetId'])


    def create_sg(self, region, sg_name):
        """create new EC2 VPC security group on AWS"""
        ec2_client = aws.ec2_client(region)
        sg_id = ec2_client.create_security_group(
            Description=next(sg['Desc'] for sg in self.security_group_setup
                if sg['Name'] == sg_name),
            GroupName=sg_name,
            VpcId=aws.get_region_vpc(region)['VpcId']
        )['GroupId']
        aws.attach_tags(ec2_client, sg_id, sg_name)

        sg_filters = os2.parse_json(f"{self.security_group_dir}{sg_name}.json")

        if sg_filters['Ingress']:
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=sg_filters['Ingress']
            )
        if sg_filters['Egress']:
            ec2_client.authorize_security_group_egress(
                GroupId=sg_id,
                IpPermissions=sg_filters['Egress']
            )


    def update_sg(self, region, sg_name):
        """update EC2 VPC security group that already exists on AWS"""
        pass


    def delete_vpc_sgs(self, region, vpc_id):
        """delete EC2 VPC security group(s) from AWS region for VPC"""
        ec2_client = aws.ec2_client(region)
        aws_sgs = aws.get_region_security_groups(region, vpc_id)
        for aws_sg in aws_sgs:
            ec2_client.delete_security_group(GroupId=aws_sg['GroupId'])


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "ec2:DescribeRegions",
            "ec2:DescribeVpcs",
            "ec2:DescribeSubnets",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeAvailabilityZones"
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
            "ec2:AssociateRouteTable",
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:AuthorizeSecurityGroupEgress"
        ]
        self.delete_actions = [
            "ec2:DeleteSecurityGroup",
            "ec2:DeleteSubnet",
            "ec2:DeleteVpc"
        ]
        return super().blocked_actions(sub_command)
