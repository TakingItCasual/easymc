from ec2mc.utils.base_classes import ParentCommand

from ec2mc.commands.user_sub import list_cmd
from ec2mc.commands.user_sub import be_cmd
from ec2mc.commands.user_sub import create_cmd
from ec2mc.commands.user_sub import set_group_cmd
from ec2mc.commands.user_sub import rotate_key_cmd
from ec2mc.commands.user_sub import delete_cmd

class User(ParentCommand):

    _sub_commands = [
        list_cmd.ListUsers,
        be_cmd.BeUser,
        create_cmd.CreateUser,
        set_group_cmd.SetUserGroup,
        rotate_key_cmd.RotateUserKey,
        delete_cmd.DeleteUser
    ]

    def main(self, cmd_args):
        """manage IAM users"""
        super().main(cmd_args)
