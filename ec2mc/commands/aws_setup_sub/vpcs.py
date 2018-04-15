from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class VPCSetup(update_template.BaseClass):

    def verify_component(self):
        """determine which VCPs need creating/updating, and which don't

        Returns:
            group_names (dict):
                "ToCreate": VCPs that do not (yet) exist on AWS
                "Existing": VCPs on AWS and up to date with local versions
        """

        all_regions = aws.get_regions()

        # Read VCPs from aws_setup.json to list
        self.vpc_setup = quit_out.parse_json(
            config.AWS_SETUP_JSON)["EC2"]["VPCs"]
        if next((vpc for vpc in self.vpc_setup
                if vpc["Name"] == config.NAMESPACE), None) is None:
            self.vpc_setup.append({
                "Name": config.NAMESPACE,
                "Description": (
                    "Default VPC for the " + config.NAMESPACE + " namespace.")
            })

        # Names of local VPCs described in aws_setup.json with region info
        vpc_names = {vpc["Name"]: {
            "ToCreate": all_regions,
            "Existing": []
        } for vpc in self.vpc_setup}

        for region in all_regions:
            ec2_client = aws.ec2_client(region)

            # VCPs already present on AWS
            #aws_vpcs = ec2_client.describe_vpcs()

        return vpc_names


    def notify_state(self, vpc_names):
        total_regions = str(len(aws.get_regions()))
        for vpc, region_info in vpc_names.items():
            existing = str(len(region_info["Existing"]))
            print("Local VPC " + vpc + " exists in " + existing + " of " +
                total_regions + " AWS regions.")


    def upload_component(self, component_info):
        pass


    def delete_component(self, component_info):
        pass


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "ec2:DescribeVpcs"
        ]
        self.upload_actions = []
        self.delete_actions = []
        return super().blocked_actions(sub_command)
