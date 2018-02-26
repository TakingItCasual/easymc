import boto3
from botocore.exceptions import ClientError

from ec2mc import const
from ec2mc import abstract_command
from ec2mc.verify.verify_instances import get_regions
from ec2mc.verify import verify_aws_setup
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class CreateServer(abstract_command.CommandBase):

    def main(self, user_info, kwargs):
        """Creates and initializes a new instance."""

        # Verify that a security group exists
        verify_aws_setup.main()

        # Verify the specified region
        region = get_regions(user_info, [kwargs["region"]])[0]
        availability_zone = region+"a"

        ec2_client = boto3.client("ec2", 
            aws_access_key_id=user_info["iam_id"], 
            aws_secret_access_key=user_info["iam_secret"], 
            region_name=region
        )

        #pp.pprint(ec2_client.describe_security_groups()["SecurityGroups"])
        #quit_out.q(["blah"])

        try:
            reservation = ec2_client.run_instances(
                DryRun=True, 
                MinCount=1, MaxCount=1, 
                ImageId=const.AWS_LINUX_AMI, 
                Placement={"AvailabilityZone": availability_zone}, 
                InstanceType=kwargs["type"], 
                TagSpecifications=[{
                    "ResourceType": "instance", 
                    "Tags": [{
                        "Key": "Name",
                        "Value": kwargs["name"]
                    }]
                }], 
                #security_groups = [ SECGROUP_HANDLE ], 
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
