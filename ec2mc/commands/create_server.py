from botocore.exceptions import ClientError

from ec2mc import config
from ec2mc import abstract_command
from ec2mc.verify import verify_aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class CreateServer(abstract_command.CommandBase):

    def main(self, user_info, kwargs):
        """create and initialize a new Minecraft instance/server

        Args:
            user_info (dict): iam_id, iam_secret, and iam_arn are needed.
            kwargs (dict):
                "region": EC2 region to create instance in
                "name": Tag value for instance tag key "Name"
                "type": EC2 instance type to create
        """

        # Verify the specified region
        region = verify_aws.get_regions(user_info, [kwargs["region"]])[0]
        self.availability_zone = region+"a"

        self.security_group = verify_aws.security_group(user_info, region)

        self.ec2_client = verify_aws.ec2_client(user_info, region)

        try:
            reservation = self.ec2_client.run_instances(
                DryRun=True, 
                MinCount=1, MaxCount=1, 
                ImageId=config.AWS_LINUX_AMI, 
                Placement={"AvailabilityZone": self.availability_zone}, 
                InstanceType=kwargs["type"], 
                TagSpecifications=[{
                    "ResourceType": "instance", 
                    "Tags": [{
                        "Key": "Name",
                        "Value": kwargs["name"]
                    }]
                }], 
                SecurityGroupIds=[self.security_group], 
                #block_device_mappings = [bdm]
            )
        except ClientError as e:
            if not e.response["Error"]["Code"] == "DryRunOperation":
                quit_out.q([e])


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "region", help="EC2 region that the instance will be located in")
        cmd_parser.add_argument(
            "name", help="Instance Name tag value")
        cmd_parser.add_argument(
            "type", help="Instance type (larger is more expensive)")


    def blocked_actions(self, user_info):
        blocked_actions = []
        blocked_actions.extend(simulate_policy.blocked(user_info, actions=[
            "ec2:DescribeInstances", 
            "ec2:DescribeSecurityGroups"
        ]))
        blocked_actions.extend(simulate_policy.blocked(user_info, actions=[
            "ec2:RunInstances"
        ], context={
            "ec2:InstanceType": ["t2.micro"]
        }))
        return blocked_actions


    def module_name(self):
        return super().module_name(__name__)
