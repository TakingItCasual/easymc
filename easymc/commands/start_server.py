import boto3

from stuff import arg_parse
from stuff import manage_titles
from stuff import simulate_policy

def main(user_info, args):
    """Start instance(s) if stopped & update client's server list.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        args (list): See stuff/arg_parse.py for documentation.
    """

    instances = arg_parse.get_instances(user_info, args)

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


def blocked_actions(user_info):
    """Returns list of denied AWS actions needed to run the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances", 
        "ec2:StartInstances"
    ])
