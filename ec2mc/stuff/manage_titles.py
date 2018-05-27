import os.path
import json
import nbtlib

from ec2mc import config
from ec2mc.stuff import os2

def update_title_dns(aws_region, instance_id, new_dns):
    """update MC client's server list with specified instance's DNS

    Args:
        aws_region (str): AWS region that the instance is in.
        instance_id (str): ID of instance.
        new_dns (str): Instance's new DNS to update client's server list with.
    """

    titles_dict = {"Instances": []}
    if os.path.isfile(config.SERVER_TITLES_JSON):
        titles_dict = os2.parse_json(config.SERVER_TITLES_JSON)

    try:
        title = next(x["title"] for x in titles_dict["Instances"]
            if x["region"] == aws_region and x["id"] == instance_id)
    except StopIteration:
        title = input("  Instance does not have a title, please assign one: ")
        titles_dict["Instances"].append({
            "region": aws_region,
            "id": instance_id,
            "title": title
        })
        os2.save_json(titles_dict, config.SERVER_TITLES_JSON)

    update_servers_dat(config.SERVERS_DAT, title, new_dns)


def update_servers_dat(servers_dat_path, server_title, new_dns):
    """update server_title in server list with new_dns

    Args:
        servers_dat_path (str): File path for MC client's servers.dat.
        server_title (str): Name of the server within client's server list.
        new_dns (str): Instance's new DNS to update client's server list with.
    """

    servers_dat_file = nbtlib.nbt.load(servers_dat_path, gzipped=False)

    for server_list_entry in servers_dat_file.root["servers"]:
        if server_title == server_list_entry["name"]:
            server_list_entry["ip"] = nbtlib.tag.String(new_dns)
            print("  Server titled \"" + server_title +
                "\" in server list updated w/ instance's DNS.")
            break
    # If server_title isn't in client's server list, add it.
    else:
        servers_dat_file.root["servers"].append(nbtlib.tag.Compound({
            "ip": nbtlib.tag.String(new_dns),
            "name": nbtlib.tag.String(server_title)
        }))
        print("  Server titled \"" + server_title +
            "\" added to server list w/ instance's DNS.")

    servers_dat_file.save(gzipped=False)
