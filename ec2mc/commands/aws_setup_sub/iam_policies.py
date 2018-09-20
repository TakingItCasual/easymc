import json
from deepdiff import DeepDiff

from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import os2
from ec2mc.utils.base_classes import ComponentSetup

class IAMPolicySetup(ComponentSetup):

    def check_component(self, config_aws_setup):
        """determine which policies need creating/updating, and which don't

        Args:
            config_aws_setup (dict): Config dict loaded from user's config.

        Returns:
            dict: IAM customer managed policy information.
                'AWSExtra': Extra policies on AWS found under same namespace.
                'ToCreate': Policies that do not (yet) exist on AWS.
                'ToUpdate': Policies on AWS not the same as local versions.
                'UpToDate': Policies on AWS up to date with local versions.
        """
        self.iam_client = aws.iam_client()
        self.policy_dir = consts.AWS_SETUP_DIR / "iam_policies"
        self.path_prefix = f"/{consts.NAMESPACE}/"

        # Local IAM policy(s) list
        self.iam_policy_setup = config_aws_setup['IAM']['Policies']

        # IAM Policies already present on AWS
        aws_policies = self.get_iam_policies()

        # Names of local policies described in aws_setup.json
        policy_names = {
            'AWSExtra': [],
            'ToCreate': [policy_name for policy_name in self.iam_policy_setup],
            'ToUpdate': [],
            'UpToDate': []
        }

        # See if AWS has policies not described by aws_setup.json
        for aws_policy in aws_policies:
            if aws_policy['PolicyName'] not in policy_names['ToCreate']:
                policy_names['AWSExtra'].append(aws_policy['PolicyName'])

        # Check if policy(s) described by aws_setup.json already on AWS
        for local_policy in policy_names['ToCreate'][:]:
            for aws_policy in aws_policies:
                if local_policy == aws_policy['PolicyName']:
                    # Policy already exists on AWS, so next check if to update
                    policy_names['ToCreate'].remove(local_policy)
                    policy_names['ToUpdate'].append(local_policy)
                    break

        # Check if policy(s) on AWS need to be updated
        for local_policy in policy_names['ToUpdate'][:]:
            local_policy_document = os2.parse_json(
                self.policy_dir / f"{local_policy}.json")

            aws_policy_desc = next(aws_policy for aws_policy in aws_policies
                if aws_policy['PolicyName'] == local_policy)
            aws_policy_document = self.iam_client.get_policy_version(
                PolicyArn=aws_policy_desc['Arn'],
                VersionId=aws_policy_desc['DefaultVersionId']
            )['PolicyVersion']['Document']

            policy_differences = DeepDiff(
                local_policy_document, aws_policy_document, ignore_order=True)

            if not policy_differences:
                # Local policy and AWS policy match, so no need to update
                policy_names['ToUpdate'].remove(local_policy)
                policy_names['UpToDate'].append(local_policy)

        return policy_names


    def notify_state(self, policy_names):
        for policy in policy_names['AWSExtra']:
            print(f"IAM policy {policy} found from AWS but not locally.")
        for policy in policy_names['ToCreate']:
            print(f"Local IAM policy {policy} not found from AWS.")
        for policy in policy_names['ToUpdate']:
            print(f"IAM policy {policy} on AWS to be updated.")
        for policy in policy_names['UpToDate']:
            print(f"IAM policy {policy} on AWS is up to date.")


    def upload_component(self, policy_names):
        """create policies on AWS that don't exist, update policies that do

        Args:
            policy_names (dict): See what check_component returns.
        """
        for local_policy in policy_names['ToCreate']:
            self.create_policy(local_policy)
            print(f"IAM policy {local_policy} created on AWS.")

        aws_policies = self.get_iam_policies()
        for local_policy in policy_names['ToUpdate']:
            self.update_policy(local_policy, aws_policies)
            print(f"IAM policy {local_policy} on AWS updated.")

        for local_policy in policy_names['UpToDate']:
            print(f"IAM policy {local_policy} on AWS already up to date.")


    def delete_component(self):
        """remove attachments, delete old versions, then delete policies"""
        aws_policies = self.get_iam_policies()
        if not aws_policies:
            print("No IAM policies on AWS to delete.")

        for aws_policy in aws_policies:
            self.delete_policy(aws_policy['Arn'])
            print(f"IAM policy {aws_policy['PolicyName']} deleted from AWS.")


    def create_policy(self, policy_name):
        """create new IAM policy on AWS"""
        local_policy_document = os2.parse_json(
            self.policy_dir / f"{policy_name}.json")
        policy_description = self.iam_policy_setup[policy_name]

        self.iam_client.create_policy(
            PolicyName=policy_name,
            Path=self.path_prefix,
            PolicyDocument=json.dumps(local_policy_document),
            Description=policy_description
        )


    def update_policy(self, policy_name, aws_policies):
        """update IAM policy that already exists on AWS"""
        local_policy_document = os2.parse_json(
            self.policy_dir / f"{policy_name}.json")

        aws_policy_desc = next(aws_policy for aws_policy in aws_policies
            if aws_policy['PolicyName'] == policy_name)

        # Delete beforehand to avoid error of 5 versions already existing
        self.delete_old_policy_versions(aws_policy_desc['Arn'])
        self.iam_client.create_policy_version(
            PolicyArn=aws_policy_desc['Arn'],
            PolicyDocument=json.dumps(local_policy_document),
            SetAsDefault=True
        )


    def delete_policy(self, policy_arn):
        """delete IAM policy from AWS"""
        self.remove_attachments(policy_arn)
        self.delete_old_policy_versions(policy_arn)
        self.iam_client.delete_policy(PolicyArn=policy_arn)


    def delete_old_policy_versions(self, policy_arn):
        """delete non-default IAM policy version(s)"""
        policy_versions = self.iam_client.list_policy_versions(
            PolicyArn=policy_arn
        )['Versions']

        for policy_version in policy_versions:
            if not policy_version['IsDefaultVersion']:
                self.iam_client.delete_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy_version['VersionId']
                )


    def remove_attachments(self, policy_arn):
        """remove group, role, and user attachments from IAM policy"""
        attachments = self.iam_client.list_entities_for_policy(
            PolicyArn=policy_arn)

        # ec2mc only attaches policies to groups, but just to be safe
        for attached_group in attachments['PolicyGroups']:
            self.iam_client.detach_group_policy(
                GroupName=attached_group['GroupName'],
                PolicyArn=policy_arn
            )
        for attached_role in attachments['PolicyRoles']:
            self.iam_client.detach_role_policy(
                RoleName=attached_role['RoleName'],
                PolicyArn=policy_arn
            )
        for attached_user in attachments['PolicyUsers']:
            self.iam_client.detach_user_policy(
                UserName=attached_user['UserName'],
                PolicyArn=policy_arn
            )


    def get_iam_policies(self):
        """returns IAM policy(s) on AWS under set namespace"""
        return self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.path_prefix
        )['Policies']


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "iam:ListPolicies",
            "iam:ListPolicyVersions",
            "iam:GetPolicyVersion"
        ]
        self.upload_actions = [
            "iam:CreatePolicy",
            "iam:CreatePolicyVersion",
            "iam:DeletePolicyVersion"
        ]
        self.delete_actions = [
            "iam:ListEntitiesForPolicy",
            "iam:DetachGroupPolicy",
            "iam:DetachRolePolicy",
            "iam:DetachUserPolicy",
            "iam:DeletePolicyVersion",
            "iam:DeletePolicy"
        ]
        return super().blocked_actions(sub_command)
