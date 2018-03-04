import os

from ec2mc import config
from ec2mc import command_template
from ec2mc.uploads import *
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

class AWSSetup(command_template.BaseClass):

    def main(self, kwargs):
        """(re)upload AWS setup files located in ~/.ec2mc/ to AWS

        Args:
            kwargs (dict):
                "confirm" (bool): Whether to actually upload aws_setup
        """

        if not os.path.isdir(config.AWS_SETUP_DIR):
            quit_out.q(["Error: aws_setup directory not found from config.",
                "  (This should not be possible. Try again.)"])

        aws_components = [
            iam_policy.IAMPolicy()
        ]

        for component in aws_components:
            component.verify(kwargs["confirm"])

        # Actual uploading occurs after this confirmation.
        if not kwargs["confirm"]:
            quit_out.q(["Please append the -c argument to confirm upload."])

        for component in aws_components:
            component.upload()


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="configure AWS with ~/.ec2mc/aws_setup")


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "iam:ListPolicies",
            "iam:ListPolicyVersions",
            "iam:GetPolicyVersion",
            "iam:CreatePolicy",
            "iam:CreatePolicyVersion",
            "iam:DeletePolicyVersion"
        ])


    def module_name(self):
        return super().module_name(__name__)
