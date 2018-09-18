from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.user_sub import create_cmd
from ec2mc.commands.user_sub import delete_cmd
from ec2mc.commands.user_sub import list_cmd

# TODO: Add command to change user's group
# TODO: Add command to rotate user's access key
class User(ParentCommand):

    sub_commands = [
        create_cmd.CreateUser,
        delete_cmd.DeleteUser,
        list_cmd.ListUsers
    ]

    def main(self, cmd_args):
        """commands to manage IAM users"""
        super().main(cmd_args)
