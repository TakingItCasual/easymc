from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

class VPCSecurityGroupSetup(update_template.BaseClass):

    def verify_component(self):
        """determine which SGs need creating/updating, and which don't

        Returns:
            group_names (dict):
                "AWSExtra": Extra SGs on AWS found with same prefix
                "ToCreate": SGs that do not (yet) exist on AWS
                "ToUpdate": SGs on AWS, but not the same as local versions
                "UpToDate": SGs on AWS and up to date with local versions
        """

        self.ec2_client = aws.ec2_client()

        # Read VCP security groups from aws_setup.json to list
        self.vpc_security_group_setup = quit_out.parse_json(
            config.AWS_SETUP_JSON)["EC2"]["SecurityGroups"]

        # VCP security groups already present on AWS
        aws_groups = self.ec2_client().describe_security_groups()

        # Names of local security groups described in aws_setup.json
        sg_names = {
            "AWSExtra": [],
            "ToCreate": [sg["Name"] for sg in self.vpc_security_group_setup],
            "ToUpdate": [],
            "UpToDate": []
        }

        return sg_names


    def notify_state(self, security_group_names):
        for sg in security_group_names["AWSExtra"]:
            print("VPC SG " + sg + " found on AWS but not locally.")
        for sg in security_group_names["ToCreate"]:
            print("Local VPC SG " + sg + " to be created on AWS.")
        for sg in security_group_names["ToUpdate"]:
            print("VPC SG " + sg + " on AWS to be updated.")
        for sg in security_group_names["UpToDate"]:
            print("VPC SG " + sg + " on AWS is up to date.")


    def upload_component(self, component_info):
        pass


    def delete_component(self, component_info):
        pass


    def blocked_actions(self, kwargs):
        self.describe_actions = [
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeVpcs"
        ]
        self.upload_actions = [
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress"
        ]
        self.delete_actions = []
        return simulate_policy.blocked(actions=super().blocked_actions(kwargs))
