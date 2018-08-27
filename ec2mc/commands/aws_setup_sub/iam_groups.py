from ec2mc import consts
from ec2mc.commands.base_classes import ComponentSetup
from ec2mc.utils import aws

class IAMGroupSetup(ComponentSetup):

    def check_component(self, config_aws_setup):
        """determine which groups need creating/updating, and which don't

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            dict: IAM group information.
                'AWSExtra': Extra groups on AWS found under same namespace.
                'ToCreate': Groups that do not (yet) exist on AWS.
                'ToUpdate': Groups on AWS not the same as local versions.
                'UpToDate': Groups on AWS up to date with local versions.
        """
        self.iam_client = aws.iam_client()
        self.path_prefix = f"/{consts.NAMESPACE}/"

        # Local IAM group(s) list
        self.iam_group_setup = config_aws_setup['IAM']['Groups']

        # IAM Groups already present on AWS
        aws_groups = self.get_iam_groups()

        # Names of local policies described in aws_setup.json
        group_names = {
            'AWSExtra': [],
            'ToCreate': [group_name for group_name in self.iam_group_setup],
            'ToUpdate': [],
            'UpToDate': []
        }

        # Check if group(s) described by aws_setup.json already on AWS
        for group_name in group_names['ToCreate'][:]:
            for aws_group in aws_groups:
                if group_name == aws_group['GroupName']:
                    # Group already exists on AWS, so next check if to update
                    group_names['ToCreate'].remove(group_name)
                    group_names['ToUpdate'].append(group_name)
                    break

        # Check if group(s) on AWS need attachment(s) updated
        for group_name in group_names['ToUpdate'][:]:
            aws_attachments = [policy['PolicyName'] for policy in
                self.iam_client.list_attached_group_policies(
                    GroupName=group_name,
                    PathPrefix=self.path_prefix
                )['AttachedPolicies']]

            local_attachments = self.iam_group_setup[group_name]['Policies']

            if set(aws_attachments) == set(local_attachments):
                # Local group and AWS group match, so no need to update
                group_names['ToUpdate'].remove(group_name)
                group_names['UpToDate'].append(group_name)

        return group_names


    def notify_state(self, group_names):
        for group in group_names['AWSExtra']:
            print(f"IAM group {group} found on AWS but not locally.")
        for group in group_names['ToCreate']:
            print(f"Local IAM group {group} to be created on AWS.")
        for group in group_names['ToUpdate']:
            print(f"IAM group {group} on AWS to be updated.")
        for group in group_names['UpToDate']:
            print(f"IAM group {group} on AWS is up to date.")


    def upload_component(self, group_names):
        """create groups on AWS that don't exist, update groups that do

        Args:
            group_names (dict): See what check_component returns.
        """
        for group_name in group_names['ToCreate']:
            self.create_group(group_name)
            print(f"IAM group {group_name} created on AWS.")

        for group_name in group_names['ToUpdate']:
            self.update_group(group_name)
            print(f"IAM group {group_name} on AWS updated.")

        for group_name in group_names['UpToDate']:
            print(f"IAM group {group_name} on AWS already up to date.")


    def delete_component(self):
        """remove user(s) and policy(s) from group(s), then delete group(s)"""
        aws_groups = self.get_iam_groups()
        if not aws_groups:
            print("No IAM groups on AWS to delete.")

        for aws_group in aws_groups:
            self.delete_group(aws_group['GroupName'])
            print(f"IAM group {aws_group['GroupName']} deleted from AWS.")


    def create_group(self, group_name):
        """create new IAM group on AWS"""
        self.iam_client.create_group(
            Path=self.path_prefix,
            GroupName=group_name
        )
        self.attach_group_policies(group_name)


    def update_group(self, group_name):
        """update IAM policy attachments for IAM group already on AWS"""
        self.detach_group_policies(group_name)
        self.attach_group_policies(group_name)


    def delete_group(self, group_name):
        """delete IAM group from AWS"""
        self.detach_group_policies(group_name)
        self.iam_client.delete_group(GroupName=group_name)


    def attach_group_policies(self, group_name):
        """attach IAM policy(s) described in iam_group_setup to group"""
        policy_names = self.iam_group_setup[group_name]['Policies']
        aws_policies = self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.path_prefix
        )['Policies']

        for policy_name in policy_names:
            aws_policy_arn = next(aws_policy['Arn'] for aws_policy in
                aws_policies if aws_policy['PolicyName'] == policy_name)
            self.iam_client.attach_group_policy(
                GroupName=group_name,
                PolicyArn=aws_policy_arn
            )


    def detach_group_policies(self, group_name):
        """detach IAM policy(s) from IAM group"""
        attached_policy_arns = [policy['PolicyArn'] for policy in
            self.iam_client.list_attached_group_policies(
                GroupName=group_name,
                PathPrefix=self.path_prefix
            )['AttachedPolicies']]
        for attached_policy_arn in attached_policy_arns:
            self.iam_client.detach_group_policy(
                GroupName=group_name,
                PolicyArn=attached_policy_arn
            )


    def get_iam_groups(self):
        """returns IAM group(s) on AWS under set namespace"""
        return self.iam_client.list_groups(
            PathPrefix=self.path_prefix)['Groups']


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "iam:ListGroups",
            "iam:ListAttachedGroupPolicies"
        ]
        self.upload_actions = [
            "iam:CreateGroup",
            "iam:ListPolicies",
            "iam:AttachGroupPolicy",
            "iam:DetachGroupPolicy"
        ]
        self.delete_actions = [
            "iam:DetachGroupPolicy",
            "iam:DeleteGroup"
        ]
        return super().blocked_actions(sub_command)
