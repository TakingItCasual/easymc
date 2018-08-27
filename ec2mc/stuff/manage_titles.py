import os
import nbtlib

from ec2mc import consts
from ec2mc.utils import os2

def update_title_dns(aws_region, instance_id, new_dns):
    """update MC client's server list with specified instance's DNS

    Args:
        aws_region (str): AWS region that the instance is in.
        instance_id (str): ID of instance.
        new_dns (str): Instance's new DNS to update client's server list with.
    """
    servers_dat_path = find_minecraft_servers_dat()
    if servers_dat_path is None:
        return

    titles_dict = {'Instances': []}
    if os.path.isfile(consts.SERVER_TITLES_JSON):
        titles_dict = os2.parse_json(consts.SERVER_TITLES_JSON)

    try:
        title = next(x['title'] for x in titles_dict['Instances']
            if x['region'] == aws_region and x['id'] == instance_id)
    except StopIteration:
        title = input("  Instance does not have a title, please assign one: ")
        titles_dict['Instances'].append({
            'region': aws_region,
            'id': instance_id,
            'title': title
        })
        os2.save_json(titles_dict, consts.SERVER_TITLES_JSON)

    update_servers_dat(servers_dat_path, title, new_dns)


# TODO: Make compatible with all possible forms of the servers.dat file
def update_servers_dat(servers_dat_path, server_title, new_dns):
    """update IP of server_title in server list with new_dns

    Args:
        servers_dat_path (str): File path for MC client's servers.dat.
        server_title (str): Name of the server within client's server list.
        new_dns (str): Instance's new DNS to update client's server list with.
    """
    servers_dat_nbt = nbtlib.nbt.load(servers_dat_path, gzipped=False)

    for server_list_entry in servers_dat_nbt.root['servers']:
        if server_title == server_list_entry['name']:
            server_list_entry['ip'] = nbtlib.tag.String(new_dns)
            print(f"  Server titled \"{server_title}\" "
                "in server list updated w/ instance's DNS.")
            break
    # If server_title isn't in client's server list, add it.
    else:
        servers_dat_nbt.root['servers'].append(nbtlib.tag.Compound({
            'ip': nbtlib.tag.String(new_dns),
            'name': nbtlib.tag.String(server_title)
        }))
        print(f"  Server titled \"{server_title}\" "
            "added to server list w/ instance's DNS.")

    servers_dat_nbt.save(gzipped=False)


def find_minecraft_servers_dat():
    """retrieve servers.dat path from config, or search home directory"""
    config_dict = os2.parse_json(consts.CONFIG_JSON)
    if 'servers_dat' in config_dict:
        if config_dict['servers_dat'] is None:
            return None
        elif os.path.isfile(config_dict['servers_dat']):
            return config_dict['servers_dat']

    config_dict['servers_dat'] = None
    for root, _, files in os.walk(os.path.expanduser("~")):
        if "servers.dat" in files and root.endswith("minecraft"):
            config_dict['servers_dat'] = os.path.join(root, "servers.dat")
    os2.save_json(config_dict, consts.CONFIG_JSON)
    return config_dict['servers_dat']
