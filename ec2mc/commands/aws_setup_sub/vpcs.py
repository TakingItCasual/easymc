from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff.threader import Threader

class VPCSetup(update_template.BaseClass):

    def verify_component(self, config_aws_setup):
        """determine region(s) where VPC(s) need to be created

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            vpc_names (dict): 
                VPC name(s) (dict):
                    "ToCreate" (list): AWS region(s) to create VPC in.
                    "Existing" (list): AWS region(s) already containing VPC.
        """

        all_regions = aws.get_regions()

        # Read VPC(s) from aws_setup.json to list
        vpc_setup = config_aws_setup["EC2"]["VPCs"]
        if next((vpc for vpc in vpc_setup
                if vpc["Name"] == config.NAMESPACE), None) is None:
            vpc_setup.append({"Name": config.NAMESPACE})

        # Names of local VPCs described in aws_setup.json, with region info
        vpc_names = {vpc["Name"]: {
            "ToCreate": [],
            "Existing": []
        } for vpc in vpc_setup}

        threader = Threader()
        for region in all_regions:
            threader.add_thread(
                self.get_region_vpcs, (region, list(vpc_names.keys())))
        # VPCs already present on AWS
        aws_vpcs = threader.get_results(return_dict=True)

        # Check all regions for VPC(s) described by aws_setup.json
        for region in all_regions[:]: # Note to self, remove() is weird
            for local_vpc in vpc_names.keys():
                for aws_vpc in aws_vpcs[region]:
                    if {"Key": "Name", "Value": local_vpc} in aws_vpc["Tags"]:
                        vpc_names[local_vpc]["Existing"].append(region)
                        break
                else:
                    vpc_names[local_vpc]["ToCreate"].append(region)

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

        for region in aws.get_regions():
            threader = Threader()
            for vpc_name, region_info in vpc_names.items():
                if region in region_info["ToCreate"]:
                    threader.add_thread(self.create_vpc, (region, vpc_name))
            threader.get_results()

        for vpc_name, region_info in vpc_names.items():
            create_count = len(region_info["ToCreate"])
            if create_count > 0:
                print("Local VPC " + vpc_name + " created in " +
                    str(create_count) + " region(s).")
            else:
                print("Local VPC " + vpc_name + " already present in all "
                    "regions. ")


    def delete_component(self, _):
        """delete VPC(s) with Namespace tag of config.NAMESPACE from AWS"""

        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(self.delete_region_vpcs, (region,))
        threader.get_results()

        # TODO: Give proper message for what's been deleted
        print("All VPCs under the " + config.NAMESPACE + " namespace deleted "
            "from AWS.")


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
        """create VPC in region and attach tags (threaded)"""
        ec2_client = aws.ec2_client(region)
        vpc_id = ec2_client.create_vpc(
            CidrBlock="172.31.0.0/16",
            AmazonProvidedIpv6CidrBlock=False
        )["Vpc"]["VpcId"]
        # TODO: Attach tags on VPC creation when (if) it becomes supported
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


    def delete_region_vpcs(self, region):
        """create VPC(s) from region with right Namespace tag (threaded)"""
        for vpc in self.get_region_vpcs(region)[1]:
            aws.ec2_client(region).delete_vpc(VpcId=vpc["VpcId"])


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
