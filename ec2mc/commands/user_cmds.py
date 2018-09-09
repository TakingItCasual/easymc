from ec2mc.commands.base_classes import ParentCommand

from ec2mc.commands.user_sub import create_cmd
from ec2mc.commands.user_sub import delete_cmd
from ec2mc.commands.user_sub import list_cmd

class User(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            create_cmd.CreateUser(),
            delete_cmd.DeleteUser(),
            list_cmd.ListUsers()
        ]

    def main(self, kwargs):
        """manage IAM users and their group attachments"""
        super().main(kwargs)
