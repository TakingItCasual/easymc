import os
import json
from deepdiff import DeepDiff

from ec2mc import config
from ec2mc import update_template
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

class IAMPolicySetup(update_template.BaseClass):

    def verify_component(self):
        """determine which policies need creating/updating, and which don't

        Returns:
            policy_dict (dict):
                "ToCreate": Policies that do not (yet) exist on AWS
                "ToUpdate": Policies on AWS, but not the same as local versions
                "UpToDate": Policies on AWS and up-to-date with local versions
        """

        self.iam_client = aws.iam_client()
        self.policy_dir = os.path.join(
            (config.AWS_SETUP_DIR + "iam_policies"), "")
        self.path_prefix = "/" + config.NAMESPACE + "/"

        # Verify that iam_setup.json exists, and read it to a dict
        iam_setup_file = config.AWS_SETUP_DIR + "aws_setup.json"
        if not os.path.isfile(iam_setup_file):
            quit_out.err(["iam_setup.json not found from config."])
        with open(iam_setup_file) as f:
            self.iam_setup = json.loads(f.read())["IAM"]

        # Policies already attached to the AWS account
        policies_on_aws = self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.path_prefix
        )["Policies"]

        policy_dict = {
            "ToCreate": self.verify_iam_setup_json(self.policy_dir),
            "ToUpdate": [],
            "UpToDate": []
        }

        # Check if policy(s) described by iam_setup.json already on AWS
        for local_policy in policy_dict["ToCreate"][:]:
            for aws_policy in policies_on_aws:
                if local_policy == aws_policy["PolicyName"]:
                    # Policy already exists on AWS, so next check if to update
                    policy_dict["ToCreate"].remove(local_policy)
                    policy_dict["ToUpdate"].append(local_policy)

        # Check if policy(s) on AWS need to be updated
        for local_policy in policy_dict["ToUpdate"][:]:

            with open(self.policy_dir + local_policy + ".json") as f:
                local_policy_document = json.loads(f.read())

            aws_policy_desc = next(aws_policy for aws_policy in policies_on_aws
                if aws_policy["PolicyName"] == local_policy)
            aws_policy_document = self.iam_client.get_policy_version(
                PolicyArn=aws_policy_desc["Arn"],
                VersionId=aws_policy_desc["DefaultVersionId"]
            )["PolicyVersion"]["Document"]

            policy_differences = DeepDiff(
                local_policy_document, aws_policy_document, ignore_order=True)

            if not policy_differences:
                # Local policy and AWS policy match, so no need to update
                policy_dict["ToUpdate"].remove(local_policy)
                policy_dict["UpToDate"].append(local_policy)

        return policy_dict


    def notify_state(self, policy_dict):
        print("")
        for policy in policy_dict["ToCreate"]:
            print("IAM policy " + policy + " to be created.")
        for policy in policy_dict["ToUpdate"]:
            print("IAM policy " + policy + " to be updated.")
        for policy in policy_dict["UpToDate"]:
            print("IAM policy " + policy + " is up-to-date.")


    def upload_component(self, policy_dict):
        """create policies on AWS that don't exist, update policies that do

        Args:
            policy_dict (dict): See what verify_component returns
        """

        print("")

        for local_policy in policy_dict["ToCreate"]:

            with open(self.policy_dir + local_policy + ".json") as f:
                local_policy_document = json.loads(f.read())
            policy_description = next(
                policy["Description"] for policy in self.iam_setup["Policies"]
                    if policy["Name"] == local_policy)

            self.iam_client.create_policy(
                PolicyName=local_policy,
                Path=self.path_prefix,
                PolicyDocument=json.dumps(local_policy_document),
                Description=policy_description
            )

            print("IAM policy " + local_policy + " created.")

        policies_on_aws = self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.path_prefix
        )["Policies"]
        for local_policy in policy_dict["ToUpdate"]:

            with open(self.policy_dir + local_policy + ".json") as f:
                local_policy_document = json.loads(f.read())

            aws_policy_desc = next(aws_policy for aws_policy in policies_on_aws
                if aws_policy["PolicyName"] == local_policy)

            # Delete beforehand to avoid error of 5 versions already existing
            self.delete_old_policy_versions(aws_policy_desc["Arn"])
            self.iam_client.create_policy_version(
                PolicyArn=aws_policy_desc["Arn"],
                PolicyDocument=json.dumps(local_policy_document),
                SetAsDefault=True
            )

            print("IAM policy " + local_policy + " updated.")

        for local_policy in policy_dict["UpToDate"]:
            print("IAM policy " + local_policy + " is already up-to-date.")


    def delete_component(self, _):
        """remove attachments, delete old versions, then delete policies"""

        print("")

        policies_on_aws = self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.path_prefix
        )["Policies"]

        if not policies_on_aws:
            print("No IAM policies on AWS to delete.")

        for aws_policy in policies_on_aws:
            attachments = self.iam_client.list_entities_for_policy(
                PolicyArn=aws_policy["Arn"])

            # ec2mc only attaches policies to groups, but just to be safe
            for attached_group in attachments["PolicyGroups"]:
                self.iam_client.detach_group_policy(
                    GroupName=attached_group["GroupName"],
                    PolicyArn=aws_policy["Arn"]
                )
            for attached_group in attachments["PolicyRoles"]:
                self.iam_client.detach_role_policy(
                    RoleName=attached_group["RoleName"],
                    PolicyArn=aws_policy["Arn"]
                )
            for attached_group in attachments["PolicyUsers"]:
                self.iam_client.detach_user_policy(
                    UserName=attached_group["UserName"],
                    PolicyArn=aws_policy["Arn"]
                )

            self.delete_old_policy_versions(aws_policy["Arn"])
            self.iam_client.delete_policy(PolicyArn=aws_policy["Arn"])

            print("IAM policy " + aws_policy["PolicyName"] + " deleted.")


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


    def verify_iam_setup_json(self, policy_dir):
        """verify that iam_setup.json reflects the contents of iam_policies

        Args:
            policy_dir (str): Directory containing local policies

        Returns:
            list: Policy names described in iam_setup.json
        """

        # Policies described in aws_setup/iam_setup.json
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

        # Warn if iam_policies has policies not described by iam_setup.json
        if not set(iam_policy_files).issubset(set(setup_policy_list)):
            print("")
            print("Warning: Unused policy(s) found from iam_policies dir.")

        return setup_policy_list


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