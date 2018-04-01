import os
import json
from deepdiff import DeepDiff

from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class IAMPolicySetup(update_template.BaseClass):

    def verify_component(self):
        """determine which policies need creating/updating, and which don't

        Returns:
            policy_names (dict):
                "AWSExtra": Extra policies on AWS found under same namespace
                "ToCreate": Policies that do not (yet) exist on AWS
                "ToUpdate": Policies on AWS, but not the same as local versions
                "UpToDate": Policies on AWS and up-to-date with local versions
        """

        self.iam_client = aws.iam_client()
        self.policy_dir = os.path.join(
            (config.AWS_SETUP_DIR + "iam_policies"), "")
        self.path_prefix = "/" + config.NAMESPACE + "/"

        # Verify that aws_setup.json exists, and read it to a dict
        iam_setup_file = config.AWS_SETUP_DIR + "aws_setup.json"
        if not os.path.isfile(iam_setup_file):
            quit_out.err(["aws_setup.json not found from config."])
        with open(iam_setup_file) as f:
            self.iam_setup = json.loads(f.read())["IAM"]

        # Policies already attached to the AWS account
        aws_policies = self.get_aws_policies()

        policy_names = {
            "AWSExtra": [],
            "ToCreate": self.verify_iam_setup(self.policy_dir),
            "ToUpdate": [],
            "UpToDate": []
        }

        # See if AWS has policies not described by aws_setup.json
        for aws_policy in aws_policies:
            if aws_policy["PolicyName"] not in policy_names["ToCreate"]:
                policy_names["AWSExtra"].append(aws_policy["PolicyName"])

        # Check if policy(s) described by aws_setup.json already on AWS
        for local_policy in policy_names["ToCreate"][:]:
            for aws_policy in aws_policies:
                if local_policy == aws_policy["PolicyName"]:
                    # Policy already exists on AWS, so next check if to update
                    policy_names["ToCreate"].remove(local_policy)
                    policy_names["ToUpdate"].append(local_policy)
                    continue

        # Check if policy(s) on AWS need to be updated
        for local_policy in policy_names["ToUpdate"][:]:

            with open(self.policy_dir + local_policy + ".json") as f:
                local_policy_document = json.loads(f.read())

            aws_policy_desc = next(aws_policy for aws_policy in aws_policies
                if aws_policy["PolicyName"] == local_policy)
            aws_policy_document = self.iam_client.get_policy_version(
                PolicyArn=aws_policy_desc["Arn"],
                VersionId=aws_policy_desc["DefaultVersionId"]
            )["PolicyVersion"]["Document"]

            policy_differences = DeepDiff(
                local_policy_document, aws_policy_document, ignore_order=True)

            if not policy_differences:
                # Local policy and AWS policy match, so no need to update
                policy_names["ToUpdate"].remove(local_policy)
                policy_names["UpToDate"].append(local_policy)

        return policy_names


    def notify_state(self, policy_names):
        print("")
        for policy in policy_names["AWSExtra"]:
            print("IAM policy " + policy + " found on AWS but not locally.")
        for policy in policy_names["ToCreate"]:
            print("IAM policy " + policy + " to be created on AWS.")
        for policy in policy_names["ToUpdate"]:
            print("IAM policy " + policy + " to be updated on AWS.")
        for policy in policy_names["UpToDate"]:
            print("IAM policy " + policy + " on AWS is up to date.")


    def upload_component(self, policy_names):
        """create policies on AWS that don't exist, update policies that do

        Args:
            policy_names (dict): See what verify_component returns
        """

        print("")

        for local_policy in policy_names["ToCreate"]:
            self.create_policy(local_policy)

        aws_policies = self.get_aws_policies()
        for local_policy in policy_names["ToUpdate"]:
            self.update_policy(local_policy, aws_policies)

        for local_policy in policy_names["UpToDate"]:
            print("IAM policy " + local_policy + " on AWS is up to date.")


    def delete_component(self, _):
        """remove attachments, delete old versions, then delete policies"""

        print("")

        aws_policies = self.get_aws_policies()
        if not aws_policies:
            print("No IAM policies on AWS to delete.")

        for aws_policy in aws_policies:
            attachments = self.iam_client.list_entities_for_policy(
                PolicyArn=aws_policy["Arn"])

            # ec2mc only attaches policies to groups, but just to be safe
            for attached_group in attachments["PolicyGroups"]:
                self.iam_client.detach_group_policy(
                    GroupName=attached_group["GroupName"],
                    PolicyArn=aws_policy["Arn"]
                )
            for attached_role in attachments["PolicyRoles"]:
                self.iam_client.detach_role_policy(
                    RoleName=attached_role["RoleName"],
                    PolicyArn=aws_policy["Arn"]
                )
            for attached_user in attachments["PolicyUsers"]:
                self.iam_client.detach_user_policy(
                    UserName=attached_user["UserName"],
                    PolicyArn=aws_policy["Arn"]
                )

            self.delete_old_policy_versions(aws_policy["Arn"])
            self.iam_client.delete_policy(PolicyArn=aws_policy["Arn"])

            print("IAM policy " + aws_policy["PolicyName"] + " deleted.")


    def create_policy(self, policy_name):
        """create a new policy on AWS"""
        with open(self.policy_dir + policy_name + ".json") as f:
            local_policy_document = json.loads(f.read())
        policy_description = next(
            policy["Description"] for policy in self.iam_setup["Policies"]
                if policy["Name"] == policy_name)

        self.iam_client.create_policy(
            PolicyName=policy_name,
            Path=self.path_prefix,
            PolicyDocument=json.dumps(local_policy_document),
            Description=policy_description
        )

        print("IAM policy " + policy_name + " created on AWS.")


    def update_policy(self, policy_name, aws_policies):
        """update policy that already exists on AWS"""
        with open(self.policy_dir + policy_name + ".json") as f:
            local_policy_document = json.loads(f.read())

        aws_policy_desc = next(aws_policy for aws_policy in aws_policies
            if aws_policy["PolicyName"] == policy_name)

        # Delete beforehand to avoid error of 5 versions already existing
        self.delete_old_policy_versions(aws_policy_desc["Arn"])
        self.iam_client.create_policy_version(
            PolicyArn=aws_policy_desc["Arn"],
            PolicyDocument=json.dumps(local_policy_document),
            SetAsDefault=True
        )

        print("IAM policy " + policy_name + " updated on AWS.")


    def delete_old_policy_versions(self, policy_arn):
        """delete non-default IAM policy version(s)"""
        policy_versions = self.iam_client.list_policy_versions(
            PolicyArn=policy_arn
        )["Versions"]

        for policy_version in policy_versions:
            if not policy_version["IsDefaultVersion"]:
                self.iam_client.delete_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy_version["VersionId"]
                )


    def verify_iam_setup(self, policy_dir):
        """verify that aws_setup.json reflects the contents of iam_policies

        Args:
            policy_dir (str): Directory containing local policies

        Returns:
            list: Policy names described in aws_setup.json
        """

        # Policies described in aws_setup/aws_setup.json
        setup_policy_list = [
            policy["Name"] for policy in self.iam_setup["Policies"]
        ]
        # Actual policies located aws_setup/iam_policies/
        iam_policy_files = [
            json_file[:-5] for json_file in os.listdir(policy_dir)
                if json_file.endswith(".json")
        ]

        # Quit if iam_setup.json describes policies not found in iam_policies
        if not set(setup_policy_list).issubset(set(iam_policy_files)):
            quit_out.err([
                "Following policy(s) not found from iam_policies dir:",
                *[(policy + ".json") for policy in setup_policy_list
                    if policy not in iam_policy_files]
            ])

        # Warn if iam_policies has policies not described by aws_setup.json
        if not set(iam_policy_files).issubset(set(setup_policy_list)):
            print("")
            print("Warning: Unused policy(s) found from iam_policies dir.")

        return setup_policy_list


    def get_aws_policies(self):
        """returns policies on AWS under set namespace"""
        return self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.path_prefix
        )["Policies"]


    def blocked_actions(self, kwargs):
        self.check_actions = [
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
        return simulate_policy.blocked(actions=super().blocked_actions(kwargs))
