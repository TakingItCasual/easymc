from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff.threader import Threader
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class VPCSetup(update_template.BaseClass):

    def verify_component(self):
        """determine region(s) where VPC(s) need to be created

        Returns:
            vpc_names (dict): 
                VPC name(s) (dict):
                    "ToCreate" (list): AWS region(s) to create VPC in.
                    "Existing" (list): AWS region(s) already containing VPC.
        """

        all_regions = aws.get_regions()

        # Read VPC(s) from aws_setup.json to list
        self.vpc_setup = quit_out.parse_json(
            config.AWS_SETUP_JSON)["EC2"]["VPCs"]
        if next((vpc for vpc in self.vpc_setup
                if vpc["Name"] == config.NAMESPACE), None) is None:
            self.vpc_setup.append({
                "Name": config.NAMESPACE,
                "Description": (
                    "Default VPC for the " + config.NAMESPACE + " namespace.")
            })

        # Names of local VPCs described in aws_setup.json, with region info
        vpc_names = {vpc["Name"]: {
            "ToCreate": all_regions,
            "Existing": []
        } for vpc in self.vpc_setup}

        threader = Threader()
        for region in all_regions:
            threader.add_thread(
                self.get_region_vpcs, (region, list(vpc_names.keys())))
        # VPCs already present on AWS
        aws_vpcs = threader.get_results(return_dict=True)

        # Check all regions for VPC(s) described by aws_setup.json
        for region in all_regions:
            ec2_client = aws.ec2_client(region)

            # Check if VPC(s) already in region
            for local_vpc in vpc_names.keys():
                for aws_vpc in aws_vpcs[region]:
                    if next((tag for tag in aws_vpc["Tags"]
                            if tag["Key"] == "Name" and
                            tag["Value"] == local_vpc), None) is not None:
                        vpc_names[local_vpc]["ToCreate"].remove(region)
                        vpc_names[local_vpc]["Existing"].append(region)

        return vpc_names


    def notify_state(self, vpc_names):
        total_regions = str(len(aws.get_regions()))
        for vpc, region_info in vpc_names.items():
            existing = str(len(region_info["Existing"]))
            print("Local VPC " + vpc + " exists in " + existing + " of " +
                total_regions + " AWS regions.")


    def upload_component(self, vpc_names):
        """create VPC(s) in AWS region(s) where not already present

        Args:
            vpc_names (dict): See what verify_component returns
        """

        all_regions = aws.get_regions()
        for region in all_regions:
            for vpc, vpc_regions in vpc_names.items():
                if region in vpc_regions["ToCreate"]:
                    self.create_vpc(region, vpc)


    def delete_component(self, _):
        """delete VPC(s) with Namespace tag of config.NAMESPACE from AWS

        Args:
            vpc_names (dict): See what verify_component returns
        """

        all_regions = aws.get_regions()
        for region in all_regions:
            ec2_client = aws.ec2_client(region)
            for vpc in self.get_region_vpcs(region)[1]:
                ec2_client.delete_vpc(VpcId=vpc["VpcId"])


    def get_region_vpcs(self, region, vpc_names=None):
        """get VPC(s) from region with correct Namespace tag (threaded)

        Args:
            region (str): AWS region to search from.
            vpc_names (list): Name(s) of VPC(s) to filter for.

        Returns:
            (tuple): 
                AWS region (str)
                VPC(s) matching filter(s) (list of dicts)
        """

        tag_filter = [{
            "Name": "tag:Namespace",
            "Values": [config.NAMESPACE]
        }]
        if vpc_names is not None:
            tag_filter.append({
                "Name": "tag:Name",
                "Values": vpc_names
            })

        return (region, aws.ec2_client(region).describe_vpcs(
            Filters=tag_filter)["Vpcs"])


    def create_vpc(self, region, vpc_name):
        """create vpc in region, and create Namespace and Name tags for it"""
        ec2_client = aws.ec2_client(region)
        vpc_id = ec2_client.create_vpc(
            CidrBlock="172.31.0.0/16",
            AmazonProvidedIpv6CidrBlock=False
        )["Vpc"]["VpcId"]
        ec2_client.get_waiter("vpc_exists").wait(VpcIds=[vpc_id])
        ec2_client.create_tags(
            Resources=[vpc_id],
            Tags=[
                {
                    "Key": "Namespace",
                    "Value": config.NAMESPACE
                },
                {
                    "Key": "Name",
                    "Value": vpc_name
                }
            ]
        )


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "ec2:DescribeVpcs"
        ]
        self.upload_actions = [
            "ec2:CreateVpc",
            "ec2:CreateTags"
        ]
        self.delete_actions = [
            "ec2:DeleteVpc"
        ]
        return super().blocked_actions(sub_command)
