from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class VPCSecurityGroupSetup(update_template.BaseClass):

    def verify_component(self, config_aws_setup):
        """determine which SGs need creating/updating, and which don't

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            dict: VPC security group information.
                Name of security group (dict):
                    "VPCName": Name tag value of VPC that SG belongs to.
                    "ToCreate": SGs that do not (yet) exist on AWS.
                    "ToUpdate": SGs on AWS not the same as local versions.
                    "UpToDate": SGs on AWS up to date with local versions.
        """

        all_regions = aws.get_regions()

        # Local VPC security groups(s) list
        vpc_security_group_setup = config_aws_setup["EC2"]["SecurityGroups"]
        # Use configured namespace as default VPC
        for vpc_sg in vpc_security_group_setup:
            if vpc_sg["VPC"] is None:
                vpc_sg["VPC"] = config.NAMESPACE

        # Names of local security groups described in aws_setup.json
        sg_names = {sg["Name"]: {
            "VPCName": sg["VPC"],
            "ToCreate": all_regions,
            "ToUpdate": [],
            "UpToDate": []
        } for sg in vpc_security_group_setup}

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
        total_regions = str(len(aws.get_regions()))
        for sg, region_info in security_group_names.items():
            up_to_date = str(len(region_info["UpToDate"]))
            print("Local SG " + sg + " up to date in " + up_to_date + " of " +
                total_regions + " AWS regions.")


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
