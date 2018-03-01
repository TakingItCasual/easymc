import os
import json

from ec2mc import config
from ec2mc import abstract_command
from ec2mc.verify import verify_aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class AWSSetup(abstract_command.CommandBase):

    def main(self, kwargs):
        """(re)upload AWS setup files located in ~/.ec2mc/ to AWS"""
        if not kwargs["confirm"]:
            quit_out.q(["Please append the -c argument to confirm."])

        if not os.path.isdir(config.AWS_SETUP_DIR):
            quit_out.q(["Error: aws_setup directory not found from config.", 
                "  (This should not be possible. Try again.)"])

        iam_client = verify_aws.iam_client()
        
        policies = iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False
        )["Policies"]

        pp.pprint(policies)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument("-c", "--confirm", 
            action="store_true", help="configure AWS with ~/.ec2mc/aws_setup")


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "iam:ListPolicies", 
            "iam:ListPolicyVersions", 
            "iam:CreatePolicy", 
            "iam:CreatePolicyVersion", 
            "iam:DeletePolicyVersion"
        ])


    def module_name(self):
        return super().module_name(__name__)
