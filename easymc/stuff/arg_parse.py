from verify import verify_instances
from stuff import quit_out

def get_instances(user_info, args):
    """Wrapper for verify_instances.main(), which verifies the filter args.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        args (list):
            str->list: AWS region filter. If [], don't filter.
            str:       Instance tag key to filter. If [], don't filter.
            str->list: Instance tag values to filter (goes w/ tag key filter).

    Returns:
        list: dicts of instances: 
            "region": AWS region that an instance is in
            "id": ID of instance
            "tags": dict: Instance tags.
    """

    if not args:
        help_message = [
            ("Please append a comma-separated list of AWS region(s) to probe "
                "for instances."), 
            "  For example (no spaces): [eu-central-1,us-east-1]", 
            "  To probe all AWS regions: []", 
            "  Available regions:"
        ]
        for region in verify_instances.get_regions(user_info):
            help_message.append("    " + region)
        quit_out.q(help_message)

    region_filter = str_to_list(args[0])
    regions = verify_instances.get_regions(user_info, region_filter)

    tag_filter = None
    if not len(args) >= 2:
        help_message = [
            "Please append an instance tag key filter.", 
            "  To not set a tag key filter: []", 
            "  Available tag keys:"
        ]

        tag_key_list = set()
        for instance_tags in instances_tags(user_info, region_filter):
            for tag_key in instance_tags:
                tag_key_list.add(tag_key)
        help_message.extend("    "+tag_key for tag_key in tag_key_list)

        quit_out.q(help_message)

    # Tag key filter parsed to list to allow for [] in CLI to equate to None
    tag_key_filter = str_to_list(args[1])
    if tag_key_filter is not None:
        tag_key_filter = tag_key_filter[0]

        # If the user has not specified a tag value filter.
        if not len(args) >= 3:
            tag_value_list = set()
            for instance_tags in instances_tags(user_info, region_filter):
                if tag_key_filter in instance_tags:
                    tag_value_list.add(instance_tags[tag_key_filter])

            if tag_value_list:
                help_message = [
                    ("Please append a comma-separated list of instance tag "
                        "value filters."), 
                    "  For example (no spaces): [tag-value-1,tag-value-2]", 
                    "  Available tag values for " + tag_key_filter + ":"]
                help_message.extend(
                    "    "+tag_value for tag_value in tag_value_list)
            else:
                if not region_filter:
                    help_message = [("Error: Instance tag key \"" + 
                        tag_key_filter + "\" not found.")]
                else:
                    help_message = [("Error: Instance tag key \"" + 
                        tag_key_filter + "\" not found " +
                        "in specified region(s).")]
            quit_out.q(help_message)

        tag_values_filter = str_to_list(args[2])
        # If the tag value filter is empty
        if not tag_values_filter:
            help_message = [
                ("Error: Instance tag value filter cannot be empty when tag "
                    "key filter is set."), 
                "  To not set a tag filter, set tag key filter to: []"
            ]
            quit_out.q(help_message)

        tag_filter = {tag_key_filter: tag_values_filter}

    all_instances = []

    print("")
    print("Probing " + str(len(regions)) + " AWS region(s) for instances...")
    offset = max(len(region) for region in regions) + 1

    instance_gen = verify_instances.main(user_info, region_filter, tag_filter)
    for region_instances in instance_gen:
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

    return all_instances


def str_to_list(str_to_convert):
    """Takes a str and converts it to a list, splitting between commas."""
    converted_str = list(str_to_convert.strip('[]').split(','))
    if converted_str == [""]:
        converted_str = None
    return converted_str


def instances_tags(user_info, region_filter):
    """Probes instances for list of tag keys-value pairs."""
    instance_gen = verify_instances.main(user_info, region_filter)
    for region_instances in instance_gen:
        for instance in region_instances["instances"]:
            yield instance["tags"]
