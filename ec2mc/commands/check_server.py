import boto3

from verify import verify_instances
from stuff import manage_titles
from stuff import simulate_policy

def main(user_info, kwargs):
    """Check instance status(es) & update client's server list

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        kwargs (dict): See stuff.verify_instances:main for documentation.
    """

    instances = verify_instances.main(user_info, kwargs)

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


def add_documentation(argparse_obj, module_name):
    cmd_parser = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])
    add_documentation_args(cmd_parser)


def add_documentation_args(cmd_parser):
    cmd_parser.add_argument(
        "-r", "--region", dest="regions", action='append', metavar="", 
        help=("AWS EC2 region(s) to probe for instances. If not "
            "set, all regions will be probed."))
    cmd_parser.add_argument(
        "-k", "--tagkey", metavar="", 
        help=("Instance tag key to filter instances by. If not "
            "set, no filter will be applied."))
    cmd_parser.add_argument(
        "-v", "--tagvalue", dest="tagvalues", action='append', metavar="", 
        help=("Instance tag value(s) to filter by (requires tag "
            "key filter to be set)."))


def blocked_actions(user_info):
    """Returns list of denied AWS actions used in the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances"
    ])
