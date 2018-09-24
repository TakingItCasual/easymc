from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils.base_classes import CommandBase
from ec2mc.validate import validate_perms

class SetUserGroup(CommandBase):

    def main(self, cmd_args):
        """change what IAM group an IAM user is a part of"""
        iam_client = aws.iam_client()
        path_prefix = f"/{consts.NAMESPACE}/"
        user_name = aws.validate_user_exists(path_prefix, cmd_args['name'])
        group_name = aws.validate_group_exists(path_prefix, cmd_args['group'])

        user_groups = iam_client.list_groups_for_user(
            UserName=user_name)['Groups']
        for user_group in user_groups:
            iam_client.remove_user_from_group(
                GroupName=user_group['GroupName'],
                UserName=user_name
            )

        iam_client.add_user_to_group(
            GroupName=group_name,
            UserName=user_name
        )

        print("")
        print(f"{user_name}'s group set to the {group_name} IAM group.")


    @classmethod
    def add_documentation(cls, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "name", help="name of IAM user")
        cmd_parser.add_argument(
            "group", help="name of IAM group to reassign IAM user to")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "iam:ListUsers",
            "iam:ListGroups",
            "iam:ListGroupsForUser",
            "iam:RemoveUserFromGroup",
            "iam:AddUserToGroup"
        ])
