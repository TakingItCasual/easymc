import boto3

from verify import verify_instances
from stuff import manage_titles
from stuff import simulate_policy

def main(user_info, args):
    """Start stopped instance(s) & update client's server list

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        args (dict): See stuff.verify_instances:main for documentation.
    """

    instances = verify_instances.main(user_info, args)

    for instance in instances:
        print("")
        print("Attempting to start instance " + instance["id"] + "...")

        ec2_client = boto3.client("ec2", 
            aws_access_key_id=user_info["iam_id"], 
            aws_secret_access_key=user_info["iam_secret"], 
            region_name=instance["region"]
        )

        instance_state = ec2_client.describe_instances(
            InstanceIds=[instance["id"]]
        )["Reservations"][0]["Instances"][0]["State"]["Name"]

        if instance_state != "running" and instance_state != "stopped":
            print("  Instance is currently " + instance_state + ".")
            print("  Cannot start an instance from a transitional state.")
            return;

        if instance_state == "stopped":
            print("  Starting instance...")
            ec2_client.start_instances(InstanceIds=[instance["id"]])
            ec2_client.get_waiter('instance_running').wait(
                InstanceIds=[instance["id"]], WaiterConfig={
                    "Delay": 5, "MaxAttempts": 12
                })
        elif instance_state == "running":
            print("  Instance is already running. Just join the server.")

        instance_dns = ec2_client.describe_instances(
            InstanceIds=[instance["id"]]
        )["Reservations"][0]["Instances"][0]["PublicDnsName"]

        print("  Instance DNS: " + instance_dns)
        if "servers_dat" in user_info:
            manage_titles.update_dns(instance["region"], instance["id"], 
                user_info["servers_dat"], instance_dns)   

        # Continues from "  Starting Instance...". Instance is running by now.
        if instance_state == "stopped":
            print("  Instance started. The server should be available soon.")      


def add_documentation(argparse_obj, module_name):
    cmd_arg = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])
    cmd_arg.add_argument(
        "-r", "--region", dest="regions", action='append', metavar="", 
        help=("AWS EC2 region(s) to probe for instances. If not "
            "set, all regions will be probed."))
    cmd_arg.add_argument(
        "-k", "--tagkey", metavar="", 
        help=("Instance tag key to filter instances by. If not "
            "set, no filter will be applied."))
    cmd_arg.add_argument(
        "-v", "--tagvalue", dest="tagvalues", action='append', metavar="", 
        help=("Instance tag value(s) to filter by (requires tag "
            "key filter to be set)."))


def blocked_actions(user_info):
    """Returns list of denied AWS actions needed to run the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances", 
        "ec2:StartInstances"
    ])
