from ec2mc.commands.base_classes import ParentCommand

from ec2mc.commands.user_sub import create
from ec2mc.commands.user_sub import delete
from ec2mc.commands.user_sub import groups

class User(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            create.CreateUser(),
            delete.DeleteUser(),
            groups.UserGroups()
        ]

    def main(self, kwargs):
        """manage IAM users and their group attachments"""
        super().main(kwargs)
