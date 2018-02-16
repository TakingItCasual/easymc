import boto3

from stuff import arg_parse
from stuff import manage_titles
from stuff import simulate_policy

def main(user_info, args):
    """Check if instance(s) running & update client's server list.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        args (list): See stuff/arg_parse.py for documentation.
    """

    instances = arg_parse.get_instances(user_info, args)

    for instance in instances:
        print("")
        print("Checking instance " + instance["id"] + "...")

        ec2_client = boto3.client("ec2", 
            aws_access_key_id=user_info["iam_id"], 
            aws_secret_access_key=user_info["iam_secret"], 
            region_name=instance["region"]
        )

        response = ec2_client.describe_instances(
            InstanceIds=[instance["id"]]
        )["Reservations"][0]["Instances"][0]
        instance_state = response["State"]["Name"]
        instance_dns = response["PublicDnsName"]

        print("  Instance is currently " + instance_state + ".")

        if instance_state == "running":
            print("  Instance DNS: " + instance_dns)
            if "servers_dat" in user_info:
                manage_titles.update_dns(instance["region"], instance["id"], 
                    user_info["servers_dat"], instance_dns)


def blocked_actions(user_info):
    """Returns list of denied AWS actions needed to run the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances"
    ])
