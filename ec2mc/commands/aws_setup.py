import os

from ec2mc import config
from ec2mc import command_template
from ec2mc.commands.aws_setup_sub import *
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
            quit_out.err(["aws_setup directory not found from config.",
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
        actions.required = True
        actions.add_parser(
            "check", help="check differences between local and AWS config")
        actions.add_parser(
            "upload", help="configure AWS with ~/.ec2mc/aws_setup")
        actions.add_parser(
            "delete", help="delete ec2mc configuration from AWS")


    def blocked_actions(self, kwargs):
        denied_actions = []
        for component in self.aws_components:
            denied_actions.extend(component.blocked_actions(kwargs))
        return denied_actions


    def module_name(self):
        return super().module_name(__name__)
