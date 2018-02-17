from verify import verify_instances
from stuff import quit_out

def get_instances(user_info, args):
    """Wrapper for verify_instances.main(), which verifies the filter args.

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
            "tags": dict: Instance tags
    """

    #    for region in verify_instances.get_regions(user_info):
    #        help_message.append("    " + region)



    #    tag_key_list = set()
    #    for instance_tags in instances_tags(user_info, region_filter):
    #        for tag_key in instance_tags:
    #            tag_key_list.add(tag_key)
    #    help_message.extend("    "+tag_key for tag_key in tag_key_list)


        
    #        tag_value_list = set()
    #        for instance_tags in instances_tags(user_info, region_filter):
    #            if tag_key_filter in instance_tags:
    #                tag_value_list.add(instance_tags[tag_key_filter])

    #            help_message.extend(
    #                "    "+tag_value for tag_value in tag_value_list)

    region_filter = args["regions"]

    tag_filter = None
    if args["tagkey"] and args["tagvalues"]:
        tag_filter = {args["tagkey"]: args["tagvalues"]}

    regions = verify_instances.get_regions(user_info, region_filter)

    print("")
    print("Probing " + str(len(regions)) + " AWS region(s) for instances...")
    offset = max(len(region) for region in regions) + 1

    all_instances = []
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
