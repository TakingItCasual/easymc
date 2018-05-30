from ec2mc import command_template
from ec2mc.verify import verify_instances
from ec2mc.verify import verify_perms

class GetBackup(command_template.BaseClass):

    def main(self, kwargs):
        """download server's world folder as a zip file

        Args:
            kwargs (dict): See verify.verify_instances:argparse_args
        """

        pass


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return verify_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeInstances",
            "ssm:SendCommand"
        ])
