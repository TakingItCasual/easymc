import os
import json
from deepdiff import DeepDiff

from ec2mc import config
from ec2mc import command_template
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class AWSSetup(command_template.BaseClass):

    def main(self, kwargs):
        """(re)upload AWS setup files located in ~/.ec2mc/ to AWS

        Args:
            kwargs (dict):
                "confirm" (bool): Whether to actually upload aws_setup
        """

        if not os.path.isdir(config.AWS_SETUP_DIR):
            quit_out.q(["Error: aws_setup directory not found from config.",
                "  (This should not be possible. Try again.)"])

        self.iam_client = aws.iam_client()

        policy_dir = os.path.join((config.AWS_SETUP_DIR + "iam_policies"), "")

        policy_dict = self.verify_policies(policy_dir, kwargs["confirm"])

        # Actual uploading occurs after this confirmation.
        if not kwargs["confirm"]:
            quit_out.q(["Please append the -c argument to confirm upload."])

        self.upload_policies(policy_dir, policy_dict)


    def verify_policies(self, policy_dir, upload_confirmed):
        """determine which policies need creating/updating, and which don't

        Args:
            policy_dir (str): Directory to find the IAM policies from
            upload_confirmed (bool): Whether aws_setup will be uploaded

        Returns:
            dict:
                "ToCreate": list: IAM policies that need to be created
                "ToUpdate": list: IAM policies that need to be updated
                "UpToDate": list: IAM policies that are already up-to-date
        """

        # Verify that iam_setup.json exists, and read it to a dict
        iam_setup_file = config.AWS_SETUP_DIR + "iam_setup.json"
        if not os.path.isfile(iam_setup_file):
            quit_out.q(["Error: iam_setup.json not found from config."])
        self.iam_setup = json.loads(open(iam_setup_file).read())

        # Policies already attached to the AWS account
        policies_on_aws = self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.iam_setup["Root"]
        )["Policies"]

        policy_dict = {
            "ToCreate": self.verify_iam_setup_json(policy_dir),
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

            policy_json_path = policy_dir + local_policy + ".json"
            local_policy_dict = json.loads(open(policy_json_path).read())

            aws_policy_desc = [aws_policy for aws_policy in policies_on_aws 
                if aws_policy["PolicyName"] == local_policy][0]
            aws_policy_dict = self.iam_client.get_policy_version(
                PolicyArn=aws_policy_desc["Arn"],
                VersionId=aws_policy_desc["DefaultVersionId"]
            )["PolicyVersion"]["Document"]

            policy_differences = DeepDiff(
                local_policy_dict, aws_policy_dict, ignore_order=True)

            if not policy_differences:
                # Local policy and AWS policy match, so no need to update
                policy_dict["ToUpdate"].remove(local_policy)
                policy_dict["UpToDate"].append(local_policy)

        if not upload_confirmed:
            print("")
            for policy in policy_dict["ToCreate"]:
                print("IAM policy " + policy + " to be created.")
            for policy in policy_dict["ToUpdate"]:
                print("IAM policy " + policy + " to be updated.")
            for policy in policy_dict["UpToDate"]:
                print("IAM policy " + policy + " is up-to-date.")

        return policy_dict


    def upload_policies(self, policy_dir, policy_dict):
        """create policies on AWS that don't exist, update policies that do

        Args:
            policy_dir (str): Directory to find the IAM policies from
            policy_dict (dict):
                "ToCreate": list: IAM policies that need to be created
                "ToUpdate": list: IAM policies that need to be updated
                "UpToDate": list: IAM policies that are already up-to-date
        """

        print("")

        for local_policy in policy_dict["ToCreate"]:

            policy_json_path = policy_dir + local_policy + ".json"
            policy_document = json.loads(open(policy_json_path).read())
            policy_description = [
                policy["Description"] for policy in self.iam_setup["Policies"]
                    if policy["Name"] == local_policy
            ][0]

            self.iam_client.create_policy(
                PolicyName=local_policy,
                Path=self.iam_setup["Root"],
                PolicyDocument=json.dumps(policy_document),
                Description=policy_description
            )

            print("IAM policy " + local_policy + " created.")

        policies_on_aws = self.iam_client.list_policies(
            Scope="Local",
            OnlyAttached=False,
            PathPrefix=self.iam_setup["Root"]
        )["Policies"]
        for local_policy in policy_dict["ToUpdate"]:

            policy_json_path = policy_dir + local_policy + ".json"
            local_policy_dict = json.loads(open(policy_json_path).read())

            aws_policy_desc = [aws_policy for aws_policy in policies_on_aws 
                if aws_policy["PolicyName"] == local_policy][0]

            # Delete beforehand to avoid error of 5 versions already existing
            self.delete_old_policy_versions(aws_policy_desc["Arn"])
            self.iam_client.create_policy_version(
                PolicyArn=aws_policy_desc["Arn"],
                PolicyDocument=json.dumps(local_policy_dict),
                SetAsDefault=True
            )

            print("IAM policy " + local_policy + " updated.")

        for local_policy in policy_dict["UpToDate"]:
            print("IAM policy " + local_policy + " is already up-to-date.")


    def delete_old_policy_versions(self, policy_arn):
        """delete non-default policy version(s)"""
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
        ]

        # Quit if iam_setup.json describes policies not found in iam_policies
        if not set(setup_policy_list).issubset(set(iam_policy_files)):
            quit_out.q([
                "Error: Following policy(s) not found from iam_policies dir:",
                *[(policy + ".json") for policy in setup_policy_list
                    if policy not in iam_policy_files]
            ])

        # Warn if iam_policies has policies not described by iam_setup.json
        if not set(iam_policy_files).issubset(set(setup_policy_list)):
            print("")
            print("Warning: Unused policy(s) found from iam_policies dir.")

        return setup_policy_list


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        cmd_parser.add_argument(
            "-c", "--confirm", action="store_true",
            help="configure AWS with ~/.ec2mc/aws_setup")


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "iam:ListPolicies",
            "iam:ListPolicyVersions",
            "iam:GetPolicyVersion",
            "iam:CreatePolicy",
            "iam:CreatePolicyVersion",
            "iam:DeletePolicyVersion"
        ])


    def module_name(self):
        return super().module_name(__name__)
