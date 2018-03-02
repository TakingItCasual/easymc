import os
import json

from ec2mc import config
from ec2mc import abstract_command
from ec2mc.verify import verify_aws
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

        self.iam_client = verify_aws.iam_client()

        self.verify_policies()

        # Actual uploading occurs after this confirmation.
        if not kwargs["confirm"]:
            quit_out.q(["Please append the -c argument to confirm upload."])


    def verify_policies(self):
        """check that the policies in AWS and the ones in aws_setup match"""

        # Verify that iam_setup.json exists, and read it to a dict
        iam_setup_file = config.AWS_SETUP_DIR + "iam_setup.json"
        if not os.path.isfile(iam_setup_file):
            quit_out.q(["Error: iam_setup.json not found from config."])
        self.iam_setup = json.loads(open(iam_setup_file).read())

        policies_dir = os.path.join(config.AWS_SETUP_DIR + "iam_policies", "")

        # Policies described in aws_setup/iam_setup.json
        setup_policy_list = [
            policy["Name"] for policy in self.iam_setup["Policies"]
        ]
        # Actual policies located aws_setup/iam_policies/
        iam_policy_files = [
            json_file[:-5] for json_file in os.listdir(policies_dir)
        ]

        # Quit if iam_setup.json describes policies not found in iam_policies
        if not set(setup_policy_list).issubset(set(iam_policy_files)):
            quit_out.q([
                "Error: Following policy(s) not found from iam_policies:",
                *[("  " + policy + ".json") for policy in 
                    set(setup_policy_list).difference(set(iam_policy_files))]
            ])

        # Warn if iam_policies has policies not described by iam_setup.json
        if not set(iam_policy_files).issubset(set(setup_policy_list)):
            print("")
            print("Warning: Unused policy(s) found from iam_policies.")

        # Policies already attached to the AWS account
        policies_on_aws = self.iam_client.list_policies(
            PathPrefix="/",
            OnlyAttached=False,
            Scope="Local"
        )["Policies"]

        print("")
        pp.pprint(policies_on_aws)

        #for policy in policies:
        #    pp.pprint(self.iam_client.get_policy_version(
        #        PolicyArn=policy["Arn"],
        #        VersionId=policy["DefaultVersionId"]
        #    )["PolicyVersion"]["Document"])


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
