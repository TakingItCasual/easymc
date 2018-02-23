import boto3

from ec2mc.stuff import simulate_policy
from ec2mc.stuff.threader import Threader
from ec2mc.stuff import quit_out

def main(user_info, kwargs):
    """Wrapper for probe_regions(). Prints found instances to the CLI.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        kwargs (dict):
            "region": list: AWS region(s) to probe. If None, probe all.
            "tagfilter": Instance tag key-value pair(s) to filter by. If None, 
                don't filter. If only a key is given, filter by key.

    Returns:
        list: dict(s): Found instance(s).
            "region": AWS region that an instance is in.
            "id": ID of instance.
            "tags": dict: Instance tag key-value pairs.
    """

    quit_out.assert_empty(simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeRegions", 
        "ec2:DescribeInstances"
    ]))

    region_filter = kwargs["regions"]
    regions = get_regions(user_info, region_filter)

    tag_filter = []
    if kwargs["tagfilter"]:
        # Convert dict(s) list to what describe_instances' Filters expects.
        for tag_kv_pair in kwargs["tagfilter"]:
            # Filter instances based on the tag key-value pair(s).
            if len(tag_kv_pair) > 1:
                tag_filter.append({
                    "Name": "tag:"+tag_kv_pair[0], 
                    "Values": tag_kv_pair[1:]
                })
            # If filter tag value(s) not specified, filter by the tag key.
            else:
                tag_filter.append({
                    "Name": "tag-key", 
                    "Values": [tag_kv_pair[0]]
                })

    print("")
    print("Probing " + str(len(regions)) + " AWS region(s) for instances...")

    all_instances = probe_regions(user_info, regions, tag_filter)

    for region in regions:
        instances = [instance for instance in all_instances 
            if instance["region"] == region]
        if not instances:
            continue
        print(region + ": " + str(len(instances)) + " instance(s) found:")
        for instance in instances:
            print("  " + instance["id"])
            for tag_key, tag_value in instance["tags"].items():
                print("    " + tag_key + ": " + tag_value)

    if not all_instances:
        if region_filter and not tag_filter:
            quit_out.q(["Error: No instances found from specified region(s).", 
                "  Try removing the region filter."])
        if not region_filter and tag_filter:
            quit_out.q(["Error: No instances with specified tag(s) found.", 
                "  Try removing the tag filter."])
        if region_filter and tag_filter:
            quit_out.q([("Error: No instances with specified tag(s) "
                "found from specified region(s)."), 
                "  Try removing the region filter and/or the tag filter."])
        quit_out.q(["Error: No instances found."])

    return all_instances


def probe_regions(user_info, regions, tag_filter=None):
    """Probe EC2 region(s) for instances, and return dicts of found instances.
    
    Uses multithreading to probe all regions simultaneously.

    Args:
        user_info (dict): iam_id and iam_secret are needed.
        regions (list): List of EC2 regions to probe.
        tag_filter (dict): Passed to probe_region

    Returns:
        list: dict(s): Found instance(s).
            "region": AWS region that an instance is in.
            "id": ID of instance.
            "tags": dict: Instance tag key-value pairs.
    """

    threader = Threader()
    for region in regions:
        threader.add_thread(probe_region, (user_info, region, tag_filter))
    results = threader.get_results()

    all_instances = []
    for region_instances in results:
        region = region_instances["region"]
        region_instances = region_instances["instances"]
        for instance in region_instances:
            all_instances.append({
                "region": region, 
                "id": instance["id"], 
                "tags": instance["tags"]
            })

    return all_instances


def probe_region(user_info, region, tag_filter=None):
    """Probes a single EC2 region for instances. Usually threaded.

    Args:
        user_info (dict): iam_id and iam_secret are needed.
        region (str): EC2 region to probe
        tag_filter (dict): Filter out instances that don't have tags matching
            the filter. If None, filter not used.

    Returns:
        dict:
            "region": Probed EC2 region.
            "instances": list: dict(s): Found instance(s) matching tag filter.
                "id": ID of instance.
                "tags": Instance tags.
    """

    response = boto3.client("ec2", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"], 
        region_name=region
    ).describe_instances(Filters=tag_filter)["Reservations"]

    region_instances = {
        "region": region, 
        "instances": []
    }

    for instance in response:
        instance = instance["Instances"][0]
        region_instances["instances"].append({
            "id": instance["InstanceId"], 
            "tags": {
                tag["Key"]: tag["Value"] for tag in instance["Tags"]
            }
        })

    return region_instances


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
            return list(set(region_filter))
        quit_out.q(["Error: Invalid region(s) specified."])
    return region_list
