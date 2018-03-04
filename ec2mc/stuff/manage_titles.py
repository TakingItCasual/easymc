import os
import json
import nbtlib

from ec2mc import config

def update_dns(aws_region, instance_id, new_dns):
    """update the MC client's server list with specified instance's DNS

    Args:
        aws_region (str): AWS region that the instance is in.
        instance_id (str): ID of instance.
        servers_dat_path (str): File path for MC client's servers.dat.
        new_dns (str): Instance's new DNS to update client's server list with.
    """

    titles_dict = verify_titles_json()
    title = [x["title"] for x in titles_dict["instances"] 
        if x["region"] == aws_region and x["id"] == instance_id]

    # It should only be possible for the length of title to be 0 or 1.
    if title:
        title = title[0]
    else:
        title = input("  Instance does not have a title, please assign one: ")
        titles_dict["instances"].append({
            "region": aws_region,
            "id": instance_id,
            "title": title
        })
        save_titles_json(titles_dict)

    update_servers_dat(config.SERVERS_DAT, title, new_dns)


def verify_titles_json():
    """verify that server_titles.json adheres to basic_struct"""
    titles_file = config.CONFIG_DIR + "server_titles.json"
    basic_struct = {"instances": []}

    if os.path.isfile(titles_file):
        with open(titles_file, "r", encoding="utf-8") as server_titles_json:
            try:
                server_titles = json.load(server_titles_json)
                if "instances" in server_titles:
                    if isinstance(server_titles["instances"], list):
                        return server_titles
            except json.decoder.JSONDecodeError:
                pass

    save_titles_json(basic_struct)
    return basic_struct


def save_titles_json(input_dict):
    titles_file = config.CONFIG_DIR + "server_titles.json"
    with open(titles_file, "w", encoding="utf-8") as out_file:
        json.dump(input_dict, out_file, ensure_ascii=False)    


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
    else:
        # If server_title isn't in client's server list, add it.
        servers_dat_file.root["servers"].append(nbtlib.tag.Compound({
            "ip": nbtlib.tag.String(new_dns),
            "name": nbtlib.tag.String(server_title)
        }))
        print("  Server titled \"" + server_title + 
            "\" added to server list w/ instance's DNS.")

    servers_dat_file.save(gzipped=False)
