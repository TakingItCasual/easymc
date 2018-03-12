from ec2mc import config
from ec2mc import command_template
from ec2mc.verify import verify_instances
from ec2mc.stuff import aws
from ec2mc.stuff import manage_titles
from ec2mc.stuff import simulate_policy

class CheckServer(command_template.BaseClass):

    def main(self, kwargs):
        """check instance status(es) & update client's server list

        Args:
            kwargs (dict): See stuff.verify_instances:main for documentation
        """

        instances = verify_instances.main(kwargs)

        for instance in instances:
            print("")
            print("Checking instance " + instance["id"] + "...")

            ec2_client = aws.ec2_client(instance["region"])

            response = ec2_client.describe_instances(
                InstanceIds=[instance["id"]]
            )["Reservations"][0]["Instances"][0]
            instance_state = response["State"]["Name"]
            instance_dns = response["PublicDnsName"]

            print("  Instance is currently " + instance_state + ".")

            if instance_state == "running":
                print("  Instance DNS: " + instance_dns)
                if config.SERVERS_DAT is not None:
                    manage_titles.update_dns(
                        instance["region"], instance["id"], instance_dns)


    def add_documentation(self, argparse_obj):
        cmd_parser = super().add_documentation(argparse_obj)
        verify_instances.argparse_args(cmd_parser)


    def blocked_actions(self):
        return simulate_policy.blocked(actions=[
            "ec2:DescribeInstances"
        ])


    def module_name(self):
        return super().module_name(__name__)
