from ec2mc import config
from ec2mc import command_template
from ec2mc.stuff import quit_out

from ec2mc.commands.aws_setup_sub import iam_policies
from ec2mc.commands.aws_setup_sub import iam_groups
from ec2mc.commands.aws_setup_sub import vpcs

class AWSSetup(command_template.BaseClass):

    def __init__(self):
        super().__init__()
        self.aws_components = [
            iam_policies.IAMPolicySetup(),
            iam_groups.IAMGroupSetup(),
            vpcs.VPCSetup()
        ]


    def main(self, kwargs):
        """check/(re)upload AWS setup files located in ~/.ec2mc/

        Args:
            kwargs (dict):
                "action": Whether to check, upload, or delete setup on AWS
        """

        # AWS setup JSON config dictionary
        config_aws_setup = quit_out.parse_json(config.AWS_SETUP_JSON)

        for component in self.aws_components:
            component_info = component.verify_component(config_aws_setup)
            print("")
            if kwargs["action"] == "check":
                component.notify_state(component_info)
            elif kwargs["action"] == "upload":
                component.upload_component(component_info)
            elif kwargs["action"] == "delete":
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
            denied_actions.extend(component.blocked_actions(kwargs["action"]))
        return denied_actions
