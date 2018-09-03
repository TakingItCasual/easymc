from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.threader import Threader

def main(kwargs, *, single_instance=False):
    """wrapper for probe_regions which prints found instances to the CLI

    Requires ec2:DescribeRegions and ec2:DescribeInstances permissions.

    Halts if no instances found. This functionality is relied upon.

    Args:
        kwargs (dict):
            'region_filter' (list[str]): AWS region(s) to probe. If None,
                probe all regions (in whitelist, if defined).
            'tag_filters' (list[list[str]]): Instance tag key-value(s)
                filter(s). For inner lists with one item, filter by key.
            'name_filter' (list[str]): Instance tag value(s) filter for
                tag key "Name".
            'id_filter' (list[str]): Instance ID filter.
        single_instance (bool): Halt if multiple instances are found.

    Returns: See what probe_regions returns.
    """
    regions, tag_filter = parse_filters(kwargs)

    print("")
    print(f"Probing {len(regions)} AWS region(s) for instances...")

    all_instances = probe_regions(regions, tag_filter)

    if not all_instances:
        halt.err("No Namespace instances found.")

    for region in regions:
        instances = [instance for instance in all_instances
            if instance['region'] == region]
        if not instances:
            continue

        print(f"{region}: {len(instances)} instance(s) found:")
        for instance in instances:
            print(f"  {instance['name']} ({instance['id']})")
            for tag_key, tag_value in instance['tags'].items():
                print(f"    {tag_key}: {tag_value}")

    if single_instance is True:
        if len(all_instances) > 1:
            halt.err("Instance query returned multiple results.",
                "  Narrow filter(s) so that only one instance is found.")
        return all_instances[0]
    return all_instances


def probe_regions(regions, tag_filter=None):
    """probe AWS region(s) for instances, and return dict(s) of instance(s)

    Requires ec2:DescribeInstances permission.

    Uses multithreading to probe all regions simultaneously.

    Args:
        regions (list[str]): AWS region(s) to probe.
        tag_filter (list[dict]): Passed to probe_region

    Returns:
        list[dict]: Found instance(s).
            'region' (str): AWS region that an instance is in.
            For other key-value pairs, see what probe_region returns.
    """
    threader = Threader()
    for region in regions:
        threader.add_thread(probe_region, (region, tag_filter))
    regions_instances = threader.get_results(return_dict=True)

    all_instances = []
    for region, instances in regions_instances.items():
        for instance in instances:
            all_instances.append({
                'region': region,
                **instance
            })

    return all_instances


def probe_region(region, tag_filter=None):
    """probe a single AWS region for instances

    Requires ec2:DescribeInstances permission.

    Args:
        region (str): AWS region to probe.
        tag_filter (list[dict]): Filter out instances that don't have tags
            matching the filter. If None/empty, filter not used.

    Returns:
        list[dict]: Instance(s) found in region.
            'id' (str): ID of instance.
            'name' (str): Tag value for instance tag key "Name".
            'tags' (dict): Instance tag key-value pair(s).
    """
    if tag_filter is None:
        tag_filter = []

    reservations = aws.ec2_client(region).describe_instances(
        Filters=tag_filter)['Reservations']

    region_instances = []
    for reservation in reservations:
        for instance in reservation['Instances']:
            if instance['State']['Name'] in ("shutting-down", "terminated"):
                continue
            if not any(tag['Key'] == "Name" for tag in instance['Tags']):
                continue
            region_instances.append({
                'id': instance['InstanceId'],
                'tags': {tag['Key']: tag['Value'] for tag in instance['Tags']}
            })

    for instance in region_instances:
        instance['name'] = instance['tags']['Name']
        del instance['tags']['Name']

    return region_instances


def parse_filters(kwargs):
    """parses region and tag filters

    Args:
        kwargs (dict): See main's arguments.

    Returns:
        tuple:
            list[str]: Region(s) to probe.
            list[dict]: Filter to pass to EC2 client's describe_instances.
    """
    regions = aws.get_regions()
    if kwargs['region_filter'] is not None:
        region_filter = set(kwargs['region_filter'])
        # Validate region filter
        if not region_filter.issubset(set(regions)):
            halt.err("Following invalid region(s) specified:",
                *(region_filter - set(regions)))
        regions = list(region_filter)

    tag_filter = [{
        'Name': "tag:Namespace",
        'Values': [consts.NAMESPACE]
    }]
    if kwargs['tag_filters']:
        # Convert dict(s) list to what describe_instances' Filters expects.
        for filter_elements in kwargs['tag_filters']:
            # Filter instances based on tag key-value(s).
            if len(filter_elements) > 1:
                tag_filter.append({
                    'Name': f"tag:{filter_elements[0]}",
                    'Values': filter_elements[1:]
                })
            # If filter tag values not given, filter by just the tag key.
            elif filter_elements:
                tag_filter.append({
                    'Name': "tag-key",
                    'Values': [filter_elements[0]]
                })
    if kwargs['name_filter']:
        tag_filter.append({
            'Name': "tag:Name",
            'Values': kwargs['name_filter']
        })
    if kwargs['id_filter']:
        tag_filter.append({
            'Name': "instance-id",
            'Values': kwargs['id_filter']
        })

    return (regions, tag_filter)


def argparse_args(cmd_parser):
    """initialize argparse arguments that validate_instances:main expects"""
    cmd_parser.add_argument(
        "-r", dest="region_filter", nargs="+", metavar="",
        help=("AWS region(s) to probe for instances. If not set, all regions "
            "will be probed."))
    cmd_parser.add_argument(
        "-t", dest="tag_filters", nargs="+", action="append", metavar="",
        help=("Instance tag value filter. First value is the tag key, with "
            "proceeding value(s) as the tag value(s). If only 1 value given, "
            "the tag key itself will be filtered for instead."))
    cmd_parser.add_argument(
        "-n", dest="name_filter", nargs="+", metavar="",
        help="Instance tag value filter for the tag key \"Name\".")
    cmd_parser.add_argument(
        "--ids", dest="id_filter", nargs="+", metavar="",
        help="Instance ID filter.")
