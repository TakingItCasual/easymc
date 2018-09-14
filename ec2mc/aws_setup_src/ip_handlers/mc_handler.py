import os
from pathlib import Path
import nbtlib

from ec2mc import consts
from ec2mc.utils import os2

# JSON file containing instance title(s) for the MC client's server list.
SERVER_TITLES_JSON = consts.CONFIG_DIR/"server_titles.json"

def main(aws_region, instance_name, instance_id, new_ip):
    """update MC client's server list with specified instance's IP

    Args:
        aws_region (str): AWS region that the instance is in.
        instance_name (str): Tag value for instance tag key "Name".
        instance_id (str): ID of instance.
        new_ip (str): Instance's new IP to update client's server list with.
    """
    titles_dict = {'Instances': []}
    if SERVER_TITLES_JSON.is_file():
        titles_dict = os2.parse_json(SERVER_TITLES_JSON)

    servers_dat_path = find_minecraft_servers_dat(titles_dict)
    if servers_dat_path is None:
        print("  Path for MC client's servers.dat not found from home dir.")
        return

    try:
        server_name = next(x['title'] for x in titles_dict['Instances']
            if x['region'] == aws_region and x['id'] == instance_id)
    except StopIteration:
        server_name = instance_name
        titles_dict['Instances'].append({
            'region': aws_region,
            'id': instance_id,
            'title': server_name
        })
        os2.save_json(titles_dict, SERVER_TITLES_JSON)

    update_servers_dat(servers_dat_path, server_name, new_ip)


# TODO: Make compatible with all possible forms of the servers.dat file
def update_servers_dat(servers_dat_path, server_name, new_ip):
    """update IP of server_name in server list with new_ip

    Args:
        servers_dat_path (str): File path for MC client's servers.dat.
        server_name (str): Name of the server within client's server list.
        new_ip (str): Instance's new IP to update client's server list with.
    """
    servers_dat_nbt = nbtlib.nbt.load(servers_dat_path, gzipped=False)

    for server_list_entry in servers_dat_nbt.root['servers']:
        if server_name == server_list_entry['name']:
            server_list_entry['ip'] = nbtlib.tag.String(new_ip)
            print(f"  IP for \"{server_name}\" entry in server list updated.")
            break
    # If server_name isn't in client's server list, add it.
    else:
        servers_dat_nbt.root['servers'].append(nbtlib.tag.Compound({
            'ip': nbtlib.tag.String(new_ip),
            'name': nbtlib.tag.String(server_name)
        }))
        print(f"  \"{server_name}\" entry with instance's IP "
            "added to server list.")

    servers_dat_nbt.save(gzipped=False)


def find_minecraft_servers_dat(titles_dict):
    """retrieve servers.dat path from config, or search home directory"""
    if 'servers_dat' in titles_dict:
        if Path(titles_dict['servers_dat']).is_file():
            return titles_dict['servers_dat']

    titles_dict['servers_dat'] = None
    for root, _, files in os.walk(Path().home()):
        if "servers.dat" in files and root.endswith("minecraft"):
            titles_dict['servers_dat'] = str(Path(root)/"servers.dat")
            os2.save_json(titles_dict, SERVER_TITLES_JSON)
            break
    return titles_dict['servers_dat']
