from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

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

        for region in all_regions():
            ec2_client = aws.ec2_client([region])

            # VCPs already present on AWS
            aws_vpcs = ec2_client.describe_vpcs()

            # Names of local VPCs described in aws_setup.json
            sg_names = {
                "ToCreate": [vpc["Name"] for vpc in self.vpc_setup],
                "Existing": []
            }

        return sg_names


    def notify_state(self, vpc_names):
        for vpc in vpc_names["ToCreate"]:
            print("Local VPC " + vpc + " to be created on AWS.")
        for vpc in vpc_names["Existing"]:
            print("VPC " + vpc + " on AWS already exists.")


    def upload_component(self, component_info):
        pass


    def delete_component(self, component_info):
        pass


    def blocked_actions(self, kwargs):
        self.describe_actions = [
            "ec2:DescribeVpcs"
        ]
        self.upload_actions = []
        self.delete_actions = []
        return simulate_policy.blocked(actions=super().blocked_actions(kwargs))
