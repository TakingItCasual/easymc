from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.validate import validate_perms

class ListUsers(CommandBase):

    def main(self, kwargs):
        """list IAM groups and IAM users under them"""
        iam_client = aws.iam_client()
        path_prefix = f"/{consts.NAMESPACE}/"

        iam_group_names = [iam_group['GroupName'] for iam_group
            in iam_client.list_groups(PathPrefix=path_prefix)['Groups']]
        if not iam_group_names:
            halt.err("No Namespace IAM groups found from AWS.",
                "  Have you uploaded the AWS setup?")

        print("")
        print(f"{len(iam_group_names)} IAM group(s) found from AWS:")
        for group_name in iam_group_names:
            group_users = iam_client.get_group(GroupName=group_name)['Users']
            if group_users:
                print(f"{group_name}: {len(group_users)} user(s) in group:")
                for group_user in group_users:
                    print(f"  {group_user['UserName']}")
            else:
                print(f"{group_name}: 0 users in group.")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "iam:ListGroups",
            "iam:GetGroup"
        ])
