from threading import Thread
import boto3

from stuff import simulate_policy
from stuff import quit_out

def main(user_info, args):
    """Wrapper for probe_regions(). Prints found instances to the console.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        args (dict):
            "region": list: AWS region(s) to probe. If None, probe all.
            "tagkey": Instance tag key to filter. If None, don't filter.
            "tagvalue": list: Instance tag value(s) to filter (needs tagkey).

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

    region_filter = args["regions"]
    regions = get_regions(user_info, region_filter)

    tag_filter = []
    if args["tagkey"] and args["tagvalues"]:
        # Converts dict to what describe_instances' Filters takes.
        tag_filter.append({
            "Name": "tag:"+args["tagkey"], 
            "Values": args["tagvalues"]
        })

    print("")
    print("Probing " + str(len(regions)) + " AWS region(s) for instances...")
    offset = max(len(region) for region in regions) + 1

    empty_regions = 0
    all_instances = []
    for region_instances in probe_regions(user_info, regions, tag_filter):
        region = region_instances["region"]
        region_instances = region_instances["instances"]
        if not region_instances:
            empty_regions += 1
            continue
        for instance in region_instances:
            all_instances.append({
                "region": region, 
                "id": instance["id"], 
                "tags": instance["tags"]
            })

    if empty_regions:
        print("No instances found in " + str(empty_regions) + " region(s).")
    for region in regions:
        instances = [inst for inst in all_instances if inst["region"] == region]
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
    
    Makes use of multithreading to probe all regions simultaneously.

    Args:
        user_info (dict): iam_id and iam_secret are needed.
        regions (list): List of EC2 regions to probe.
        tag_filter (dict): Filter out instances that don't have tags matching
            the filter. If None, filter not used.

    Returns:
        list: dict(s):
            "region": Probed EC2 region.
            "instances": list: dict(s): Found instance(s) matching tag filter.
                "id": ID of instance.
                "tags": Instance tags.
    """

    results = []
    region_probe_threads = []
    for region in regions:
        region_probe_threads.append(
            Thread(target=probe_region, 
                args=(results, user_info, region, tag_filter)))
        region_probe_threads[-1].start()
    for thread in region_probe_threads:
        thread.join()

    return results


def probe_region(results, user_info, region, tag_filter=None):
    """Probes a single region for instances. Returns result via results arg.

    This function returns via an argument rather than a return statement, 
    because it would be more complicated to set it up so that this threaded 
    function could properly use a return statement.

    Args:
        results (list): Found instances are returned via this variable.
        user_info (dict): iam_id and iam_secret are needed.
        region (str): Probe regions listed in the filter. 
            If None, probe all regions.
        tag_filter (dict): Filter out instances that don't have tags matching
            the filter. If None, filter not used.

    Returns: (via the results arg)
        list: dict(s):
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

    if response:
        for instance in response:
            instance = instance["Instances"][0]
            region_instances["instances"].append({
                "id": instance["InstanceId"], 
                "tags": {
                    tag["Key"]: tag["Value"] for tag in instance["Tags"]
                }
            })

    results.append(region_instances)


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
