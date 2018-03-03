import os
import json

from ec2mc import config
from ec2mc import abstract_command
from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
from ec2mc.stuff import quit_out

import pprint
pp = pprint.PrettyPrinter(indent=2)

class AWSSetup(abstract_command.CommandBase):

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

        self.verify_policies()

        # Actual uploading occurs after this confirmation.
        if not kwargs["confirm"]:
            quit_out.q(["Please append the -c argument to confirm upload."])


    def verify_policies(self):
        """determine which policies need creating/updating, and which don't

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

        policy_dir = os.path.join((config.AWS_SETUP_DIR + "iam_policies"), "")

        # Policies already attached to the AWS account
        policies_on_aws = self.iam_client.list_policies(
            PathPrefix=self.iam_setup["Root"],
            OnlyAttached=False,
            Scope="Local"
        )["Policies"]

        print("")
        pp.pprint(policies_on_aws)

        policy_dict = {
            "ToCreate": self.verify_iam_setup_json(policy_dir),
            "ToUpdate": [],
            "UpToDate": []
        }

        # Check if policies described by iam_setup.json already exist on AWS
        for local_policy in policy_dict["ToCreate"][:]:
            for aws_policy in policies_on_aws:
                if local_policy == aws_policy["PolicyName"]:
                    # Policy already exists on AWS, so next check if to update
                    policy_dict["ToCreate"].remove(local_policy)
                    policy_dict["ToUpdate"].append(local_policy)

        # Check if policies on AWS need to be updated
        for local_policy in policy_dict["ToUpdate"][:]:

            aws_policy = [policy for policy in policies_on_aws 
                if policy["PolicyName"] == local_policy]

            policy_json_path = policy_dir + local_policy + ".json"

            local_policy_dict = json.loads(open(policy_json_path).read())
            aws_policy_dict = self.iam_client.get_policy_version(
                PolicyArn=aws_policy["Arn"],
                VersionId=aws_policy["DefaultVersionId"]
            )["PolicyVersion"]["Document"]

            # TODO: Figure out way to reliably compare nested dictionaries
            if False:
                policy_dict["ToUpdate"].remove(local_policy)
                policy_dict["UpToDate"].append(local_policy)
        
        for policy in policies_on_aws:
            pp.pprint(self.iam_client.get_policy_version(
                PolicyArn=policy["Arn"],
                VersionId=policy["DefaultVersionId"]
            )["PolicyVersion"]["Document"])

        return policy_dict


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
                "Error: Following policy(s) not found from iam_policies:",
                *[(policy + ".json") for policy in setup_policy_list
                    if policy not in iam_policy_files]
            ])

        # Warn if iam_policies has policies not described by iam_setup.json
        if not set(iam_policy_files).issubset(set(setup_policy_list)):
            print("")
            print("Warning: Unused policy(s) found from iam_policies.")

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
