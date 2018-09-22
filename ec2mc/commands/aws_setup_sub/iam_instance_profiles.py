import json

from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.base_classes import ComponentSetup

class IAMInstanceProfileSetup(ComponentSetup):

    def check_component(self, _):
        """check if namespace IAM instance profile exists

        Returns:
            bool: Whether namespace instance profile exists.
        """
        self.iam_client = aws.iam_client()
        self.profile_name = consts.NAMESPACE
        self.path_prefix = f"/{self.profile_name}/"

        return self.get_namespace_instance_profile() is not None


    def notify_state(self, instance_profile_exists):
        if instance_profile_exists:
            print(f"IAM instance profile {self.profile_name} exists on AWS.")
        else:
            print(f"IAM instance profile {self.profile_name} "
                "not found from AWS.")


    def upload_component(self, instance_profile_exists):
        """create namespace IAM instance profile

        Args:
            instance_profile_exists (bool): See what check_component returns.
        """
        if instance_profile_exists:
            print(f"IAM instance profile {self.profile_name} "
                "already exists on AWS.")
            return

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }

        iam_role = self.iam_client.create_role(
            Path=self.path_prefix,
            RoleName=self.profile_name,
            AssumeRolePolicyDocument=json.dumps(policy_document),
        )['Role']
        instance_profile = self.iam_client.create_instance_profile(
            InstanceProfileName=iam_role['RoleName'],
            Path=iam_role['Path']
        )['InstanceProfile']

        self.iam_client.attach_role_policy(
            RoleName=iam_role['RoleName'],
            PolicyArn=self.get_ssm_policy_arn()
        )
        self.iam_client.add_role_to_instance_profile(
            InstanceProfileName=instance_profile['InstanceProfileName'],
            RoleName=iam_role['RoleName']
        )

        print(f"IAM instance profile {self.profile_name} created on AWS.")


    def delete_component(self):
        """remove namespace IAM instance profile from AWS"""
        instance_profile = self.get_namespace_instance_profile()
        if instance_profile is None:
            print("No IAM instance templates to delete.")
            return

        for iam_role in instance_profile['Roles']:
            self.iam_client.remove_role_from_instance_profile(
                InstanceProfileName=instance_profile['InstanceProfileName'],
                RoleName=iam_role['RoleName']
            )
        iam_role = self.get_namespace_role()
        iam_role_policies = self.iam_client.list_attached_role_policies(
            RoleName=iam_role['RoleName'])['AttachedPolicies']
        for iam_role_policy in iam_role_policies:
            self.iam_client.detach_role_policy(
                RoleName=iam_role['RoleName'],
                PolicyArn=iam_role_policy['PolicyArn']
            )

        self.iam_client.delete_role(RoleName=iam_role['RoleName'])
        self.iam_client.delete_instance_profile(
            InstanceProfileName=instance_profile['InstanceProfileName'])

        print(f"IAM instance profile {self.profile_name} deleted from AWS.")


    def get_ssm_policy_arn(self):
        """return ARN of the AmazonEC2RoleforSSM policy"""
        aws_policies = self.iam_client.list_policies(
            Scope="AWS",
            PolicyUsageFilter="PermissionsPolicy"
        )['Policies']
        return next(policy['Arn'] for policy in aws_policies
            if policy['PolicyName'] == "AmazonEC2RoleforSSM")


    def get_namespace_instance_profile(self):
        """return namespace IAM instance profile, or None if non-existent"""
        instance_profiles = self.iam_client.list_instance_profiles(
            PathPrefix=self.path_prefix)['InstanceProfiles']
        try:
            return next(profile for profile in instance_profiles
                if profile['InstanceProfileName'] == self.profile_name)
        except StopIteration:
            return None


    def get_namespace_role(self):
        """return namespace IAM role, or None if non-existent"""
        iam_roles = self.iam_client.list_roles(
            PathPrefix=self.path_prefix)['Roles']
        try:
            return next(iam_role for iam_role in iam_roles
                if iam_role['RoleName'] == self.profile_name)
        except StopIteration:
            halt.err("Namespace IAM instance profile's IAM role not found.")


    def blocked_actions(self, sub_command):
        self.describe_actions = [
            "iam:ListInstanceProfiles",
            "iam:ListRoles"
        ]
        self.upload_actions = [
            "iam:CreateRole",
            "iam:CreateInstanceProfile",
            "iam:ListPolicies",
            "iam:AttachRolePolicy",
            "iam:PassRole",
            "iam:AddRoleToInstanceProfile"
        ]
        self.delete_actions = [
            "iam:RemoveRoleFromInstanceProfile",
            "iam:ListAttachedRolePolicies",
            "iam:DetachRolePolicy",
            "iam:DeleteRole",
            "iam:DeleteInstanceProfile"
        ]
        return super().blocked_actions(sub_command)
