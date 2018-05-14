from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff.threader import Threader

import pprint
pp = pprint.PrettyPrinter(indent=2)

class VPCSetup(update_template.BaseClass):

    def verify_component(self, config_aws_setup):
        """determine statuses for VPC(s) and SG(s) on AWS

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            tuple:
                dict: Which regions the namespace VPC exists in.
                    "ToCreate" (list): AWS region(s) to create VPC in.
                    "Existing" (list): AWS region(s) already containing VPC.
                dict: VPC security group status(es) for each region.
                    Name of security group (dict):
                        "ToCreate" (list): AWS region(s) to create SG in.
                        "ToUpdate" (list): AWS region(s) to update SG in.
                        "UpToDate" (list): AWS region(s) already containing SG.
        """

        all_regions = aws.get_regions()

        self.vpc_name = config.NAMESPACE
        # Region(s) to create VPC in, and region(s) already containing VPC
        vpc_regions = {
            "ToCreate": all_regions,
            "Existing": []
        }

        # Information for each SG and its status in each region
        sg_names = {sg["Name"]: {
            "ToCreate": all_regions,
            "ToUpdate": [],
            "UpToDate": []
        } for sg in config_aws_setup["EC2"]["SecurityGroups"]}

        vpc_threader = Threader()
        sg_threader = Threader()
        for region in all_regions:
            vpc_threader.add_thread(aws.get_region_vpc, (region,))
            sg_threader.add_thread(self.get_region_security_groups, (region,))
        # VPCs already present in AWS regions
        aws_vpcs = vpc_threader.get_results(return_dict=True)
        # VPC security groupss already present in AWS regions
        aws_sgs = sg_threader.get_results(return_dict=True)

        # Check each region for VPC with with correct Name tag value
        for region in all_regions[:]:
            if any({"Key": "Name", "Value": self.vpc_name} in aws_vpc["Tags"]
                    for aws_vpc in aws_vpcs[region]):
                vpc_regions["ToCreate"].remove(region)
                vpc_regions["Existing"].append(region)

        # Check each region for SG(s) described by aws_setup.json
        for sg_name, sg_regions in sg_names.items():
            for region in all_regions[:]:
                if region in vpc_regions["Existing"]:
                    if any(aws_sg["GroupName"] == sg_name
                            for aws_sg in aws_sgs[region]):
                        sg_regions["ToCreate"].remove(region)
                        sg_regions["ToUpdate"].append(region)

                if region in sg_regions["ToUpdate"]:
                    pass

        return (vpc_regions, sg_names)


    def notify_state(self, vpc_and_sg_info):
        vpc_regions, sg_names = vpc_and_sg_info

        total_regions = str(len(aws.get_regions()))
        existing = str(len(vpc_regions["Existing"]))
        print("VPC " + self.vpc_name + " exists in " + existing + " of " +
            total_regions + " AWS regions.")

        print("")
        for sg_name, sg_regions in sg_names.items():
            up_to_date = str(len(sg_regions["UpToDate"]))
            print("Local SG " + sg_name + " up to date in " + up_to_date +
                " of " + total_regions + " AWS regions.")


    def upload_component(self, vpc_and_sg_info):
        """create VPC(s) and create/update SG(s) in AWS region(s)

        Args:
            vpc_and_sg_info (dict): See what verify_component returns.
        """

        vpc_regions, sg_names = vpc_and_sg_info

        threader = Threader()
        for region in aws.get_regions():
            if region in vpc_regions["ToCreate"]:
                threader.add_thread(self.create_vpc, (region,))
        threader.get_results()

        create_count = len(vpc_regions["ToCreate"])
        if create_count > 0:
            print("VPC " + self.vpc_name + " created in " +
                str(create_count) + " region(s).")
        else:
            print("VPC " + self.vpc_name + " already present in all regions. ")


    def delete_component(self):
        """delete VPC(s) and associated SG(s) from AWS"""

        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(self.delete_region_vpcs, (region,))
        deleted_vpcs = list(filter(lambda x: x != 0, threader.get_results()))

        if len(deleted_vpcs) > 0:
            print("VPC " + self.vpc_name + " deleted from all AWS regions.")
        else:
            print("No VPCs to delete.")


    def create_vpc(self, region):
        """create VPC in region and attach tags (threaded)"""
        # TODO: Attach tags on VPC creation when (if) it becomes supported
        ec2_client = aws.ec2_client(region)
        vpc_id = ec2_client.create_vpc(
            CidrBlock="172.31.0.0/16",
            AmazonProvidedIpv6CidrBlock=False
        )["Vpc"]["VpcId"]
        aws.attach_tags(ec2_client, vpc_id, self.vpc_name)


    def delete_region_vpcs(self, region):
        """create VPC(s) from region with correct Namespace tag (threaded)

        Returns:
            int: Number of VPCs deleted.
        """
        region_vpcs = aws.get_region_vpc(region)
        for vpc in region_vpcs:
            aws.ec2_client(region).delete_vpc(VpcId=vpc["VpcId"])
        return len(region_vpcs)


    def get_region_security_groups(self, region):
        return aws.ec2_client(region).describe_security_groups(
            Filters=[{
                "Name": "tag:Namespace",
                "Values": [config.NAMESPACE]
            }]
        )["SecurityGroups"]


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "ec2:DescribeRegions",
            "ec2:DescribeVpcs",
            "ec2:DescribeSecurityGroups"
        ]
        self.upload_actions = [
            "ec2:CreateVpc",
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:AuthorizeSecurityGroupEgress",
            "ec2:CreateTags"
        ]
        self.delete_actions = [
            "ec2:DeleteVpc"
        ]
        return super().blocked_actions(sub_command)
