from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.user_sub import list_cmd
from ec2mc.commands.user_sub import create_cmd
from ec2mc.commands.user_sub import rotate_key_cmd
from ec2mc.commands.user_sub import delete_cmd

# TODO: Add command to change user's group
class User(ParentCommand):

    sub_commands = [
        list_cmd.ListUsers,
        create_cmd.CreateUser,
        rotate_key_cmd.RotateUserKey,
        delete_cmd.DeleteUser
    ]

    def main(self, cmd_args):
        """manage IAM users"""
        super().main(cmd_args)
