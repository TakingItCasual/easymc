import boto3

from stuff import simulate_policy
from stuff import quit_out

def main(user_info, args):
    """Wrapper for probe_regions(), which prints information to the console.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        args (dict):
            "region": list: AWS region(s) to probe. If None, probe all.
            "tagkey": Instance tag key to filter. If None, don't filter.
            "tagvalue": list: Instance tag value(s) to filter (needs tagkey).

    Returns:
        list: dicts of instances: 
            "region": AWS region that an instance is in
            "id": ID of instance
            "tags": dict: Instance tag key-value pairs
    """

    region_filter = args["regions"]
    regions = get_regions(user_info, region_filter)

    tag_filter = None
    if args["tagkey"] and args["tagvalues"]:
        tag_filter = {args["tagkey"]: args["tagvalues"]}

    print("")
    print("Probing " + str(len(regions)) + " AWS region(s) for instances...")
    offset = max(len(region) for region in regions) + 1

    all_instances = []
    for region_instances in probe_regions(user_info, region_filter, tag_filter):
        region = region_instances["region"]
        region_instances = region_instances["instances"]
        offset_str = " "*(offset-len(region))
        if region_instances:
            print(region + ":" + offset_str + 
                str(len(region_instances)) + " instance(s) found:")
            for instance in region_instances:
                print("  " + instance["id"])
                for tag_key, tag_value in instance["tags"].items():
                    print("    " + tag_key + ": " + tag_value)

                all_instances.append({
                    "region": region, 
                    "id": instance["id"], 
                    "tags": instance["tags"]
                })
        else:
            print(region + ":" + offset_str + "0 instance(s) found")

    if not all_instances:
        if region_filter and not tag_filter:
            quit_out.q(["Error: No instances found from specified region(s).", 
                "  Try removing the region filter."])
        if not region_filter and tag_filter:
            quit_out.q(["Error: No instances with specified tag(s) found.", 
                "  Try removing the tag key filter."])
        if region_filter and tag_filter:
            quit_out.q([("Error: No instances with specified tag(s) "
                "found from specified region(s)."), 
                "  Try removing the region filter and/or the tag key filter."])
        quit_out.q(["Error: No instances found."])

    return all_instances


def probe_regions(user_info, region_filter=None, tag_filter=None):
    """Probe EC2 region(s) for instances, and yield dicts of found instances.
    
    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        region_filter (list): Probe regions listed in the filter. 
            If None, probe all regions.
        tag_filter (dict): Filter out instances that don't have tags matching
            the filter. If None, filter not used.

    Yields: Yields for each region probed
        dict: Found instance(s) in region matching the tag filter
            "region": EC2 region containing instance(s)
            "instances": list: dicts of instances:
                "id": ID of instance
                "tags": Instance tags
    """

    quit_out.assert_empty(simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeRegions", 
        "ec2:DescribeInstances"
    ]))

    if tag_filter:
        # Converts dict to what describe_instances' Filters takes.
        for tag_filter_key in tag_filter:
            tag_filter = [{
                "Name": "tag:"+tag_filter_key, 
                "Values": tag_filter[tag_filter_key]
            }]
            break # tag_filter should have only one key-value pair
    else:
        tag_filter = []

    regions = get_regions(user_info, region_filter)
    for region in regions:
        response = boto3.client("ec2", 
            aws_access_key_id=user_info["iam_id"], 
            aws_secret_access_key=user_info["iam_secret"], 
            region_name=region
        ).describe_instances(Filters=tag_filter)["Reservations"]

        region_instances = {
            "region": region, 
            "instances": []
        }

        if response:
            instances = response[0]["Instances"]
            for instance in instances:
                region_instances["instances"].append({
                    "id": instance["InstanceId"], 
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in instance["Tags"]
                    }
                })

        yield region_instances


def get_regions(user_info, region_filter=None):
    """Returns list of EC2 regions, or region_filter if not empty and valid."""
    region_list = []
    for region in boto3.client("ec2", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"],
        region_name="us-east-1" # Why must listing regions require knowing one
    ).describe_regions()["Regions"]:
        region_list.append(region["RegionName"])

    # Script can't handle an empty region list, so the filter must be valid.
    if region_filter:
        if set(region_filter).issubset(set(region_list)):
            return region_filter
        quit_out.q(["Error: Invalid region(s) specified."])
    return region_list
