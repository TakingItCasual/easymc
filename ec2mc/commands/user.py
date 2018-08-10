from ec2mc.commands.base_classes import ParentCommand

from ec2mc.commands.user_sub import create
from ec2mc.commands.user_sub import delete

class User(ParentCommand):

    def __init__(self):
        super().__init__()
        self.sub_commands = [
            create.CreateUser(),
            delete.DeleteUser()
        ]

    def main(self, kwargs):
        """manage IAM users and their group attachments"""
        super().main(kwargs)
