import boto3

from stuff import simulate_policy
from stuff import quit_out

def main(user_info, region_filter=None, tag_filter=None):
    """Probe EC2 region(s) for instances, and yield dicts of found instances.
    
    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        region_filter (list): Probe regions listed in the filter. 
            If None, probe all regions.
        tag_filter (dict): Filter out instances that don't have tags matching
            the filter. If None, filter not used.

    Yields:
        dict: Instances found in a single region matching the tag filter.
            "region": AWS region containing instance(s)
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

    instance_count = 0
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
                instance_count += 1

        yield region_instances

    if not instance_count:
        if region_filter and not tag_filter:
            quit_out.q(["Error: No instances found from specified region(s).", 
                "  Try searching all regions (region filter: [])."])
        if not region_filter and tag_filter:
            quit_out.q(["Error: No instances with specified tag(s) found.", 
                "  Try not using the tag filter (tag key filter: [])."])
        if region_filter and tag_filter:
            quit_out.q([("Error: No instances with specified tag(s) "
                "found from specified region(s)."), 
                "  Try removing the region filter and/or the tag key filter."])
        quit_out.q(["Error: No instances found."])


def get_regions(user_info, region_filter=None):
    """Returns list of EC2 regions, or region_filter if not empty and valid."""
    region_list = []
    for region in boto3.client("ec2", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"],
        region_name="us-east-1"
    ).describe_regions()["Regions"]:
        region_list.append(region["RegionName"])

    # Script can't handle an empty region list, so the filter must be valid.
    if region_filter:
        if set(region_filter).issubset(set(region_list)):
            return region_filter
        quit_out.q(["Error: Invalid region(s) specified."])
    return region_list
