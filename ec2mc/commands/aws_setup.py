import os

from ec2mc import config
from ec2mc import command_template
from ec2mc.update import *
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

class AWSSetup(command_template.BaseClass):

    def __init__(self):
        super().__init__()
        self.aws_components = [
            iam_setup.IAMSetup()
        ]


    def main(self, kwargs):
        """(re)upload AWS setup files located in ~/.ec2mc/ to AWS

        Args:
            kwargs (dict):
                "confirm" (bool): Whether to actually upload aws_setup
        """

        if not os.path.isdir(config.AWS_SETUP_DIR):
            quit_out.q(["Error: aws_setup directory not found from config.",
                "  (This should not be possible. Try again.)"])

        for component in self.aws_components:
            component.verify_component(kwargs["action"])

        # Actual uploading occurs after this confirmation.
        if kwargs["action"] == "check":
            quit_out.q(["Change \"check\" to \"upload\" to upload setup."])
        elif kwargs["action"] == "upload":
            for component in self.aws_components:
                component.upload_component()
        elif kwargs["action"] == "delete":
            for component in self.aws_components:
                component.delete_component()


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        actions = cmd_parser.add_subparsers(metavar="{action}", dest="action")
        action_args = actions.add_parser(
            "check", usage="ec2mc " + self.module_name() + " check [-h]",
            help="check differences between local and AWS config")
        action_args = actions.add_parser(
            "upload", usage="ec2mc " + self.module_name() + " upload [-h]",
            help="configure AWS with ~/.ec2mc/aws_setup")
        action_args = actions.add_parser(
            "delete", usage="ec2mc " + self.module_name() + " delete [-h]",
            help="delete ec2mc configuration from AWS")


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
