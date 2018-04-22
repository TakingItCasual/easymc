from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import quit_out

class VPCSecurityGroupSetup(update_template.BaseClass):

    def verify_component(self, config_aws_setup):
        """determine which SGs need creating/updating, and which don't

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            dict: VPC security group information.
                "AWSExtra": Extra SGs on AWS found in same namespace
                "ToCreate": SGs that do not (yet) exist on AWS
                "ToUpdate": SGs on AWS, but not the same as local versions
                "UpToDate": SGs on AWS and up to date with local versions
        """

        all_regions = aws.get_regions()

        # Local VPC security groups(s) list
        vpc_security_group_setup = config_aws_setup["EC2"]["SecurityGroups"]

        # Names of local security groups described in aws_setup.json
        sg_names = {
            "AWSExtra": [],
            "ToCreate": [sg["Name"] for sg in vpc_security_group_setup],
            "ToUpdate": [],
            "UpToDate": []
        }

        #for region in all_regions[:]:
        #    ec2_client = aws.ec2_client(region)

            # VPC security groups already present on AWS
        #    aws_groups = ec2_client.describe_security_groups(
        #        Filters=[{
        #            "Name": "tag:Namespace",
        #            "Values": [config.NAMESPACE]
        #        }]
        #    )

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


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "ec2:DescribeRegions",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeVpcs"
        ]
        self.upload_actions = [
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress"
        ]
        self.delete_actions = []
        return super().blocked_actions(sub_command)
