from ec2mc import abstract_command
from ec2mc.verify import verify_aws
from ec2mc.verify import verify_instances
from ec2mc.stuff import manage_titles
from ec2mc.stuff import simulate_policy

class CheckServer(abstract_command.CommandBase):

    def main(self, user_info, kwargs):
        """Check instance status(es) & update client's server list

        Args:
            user_info (dict): iam_id, iam_secret, and iam_arn are needed.
            kwargs (dict): See stuff.verify_instances:main for documentation.
        """

        instances = verify_instances.main(user_info, kwargs)

        for instance in instances:
            print("")
            print("Checking instance " + instance["id"] + "...")

            ec2_client = verify_aws.ec2_client(user_info, instance["region"])

            response = ec2_client.describe_instances(
                InstanceIds=[instance["id"]]
            )["Reservations"][0]["Instances"][0]
            instance_state = response["State"]["Name"]
            instance_dns = response["PublicDnsName"]

            print("  Instance is currently " + instance_state + ".")

            if instance_state == "running":
                print("  Instance DNS: " + instance_dns)
                if "servers_dat" in user_info:
                    manage_titles.update_dns(instance["region"], 
                        instance["id"], user_info["servers_dat"], instance_dns)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        abstract_command.args_to_filter_instances(cmd_parser)


    def blocked_actions(self, user_info):
        return simulate_policy.blocked(user_info, actions=[
            "ec2:DescribeInstances"
        ])


    def module_name(self):
        return super().module_name(__name__)
