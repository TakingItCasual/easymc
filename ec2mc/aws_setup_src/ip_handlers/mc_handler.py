import os
from pathlib import Path
from nbtlib.nbt import load
from nbtlib.tag import List
from nbtlib.tag import Compound
from nbtlib.tag import String

from ec2mc import consts

def main(instance_name, new_ip):
    """update MC client's server list with specified instance's IP

    Args:
        instance_name (str): Tag value for instance tag key "Name".
        new_ip (str): Instance's new IP to update client's server list with.
    """
    servers_dat_path = _find_minecraft_servers_dat()
    if servers_dat_path is not None:
        _update_servers_dat(servers_dat_path, instance_name, new_ip)


def _update_servers_dat(servers_dat_path, server_name, new_ip):
    """update IP of server_name in server list with new_ip

    Args:
        servers_dat_path (str): File path for MC client's servers.dat.
        server_name (str): Name of the server within client's server list.
        new_ip (str): Instance's new IP to update client's server list with.
    """
    servers_dat_nbt = load(servers_dat_path, gzipped=False)

    for server_list_entry in servers_dat_nbt.root['servers']:
        if server_name == server_list_entry['name']:
            server_list_entry['ip'] = String(new_ip)
            print(f"  IP for \"{server_name}\" entry in server list updated.")
            break
    # If server_name isn't in client's server list, add it.
    else:
        # List type must be "Compound" (defaults to "End" for empty List).
        if not servers_dat_nbt.root['servers']:
            servers_dat_nbt.root['servers'] = List[Compound]()
        servers_dat_nbt.root['servers'].append(Compound({
            'ip': String(new_ip),
            'name': String(server_name)
        }))
        print(f"  \"{server_name}\" entry with instance's IP "
            "added to server list.")

    servers_dat_nbt.save(gzipped=False)


def _find_minecraft_servers_dat():
    """retrieve servers.dat path from config, or search home directory"""
    # Path to text file containing path to Minecraft client's servers.dat file.
    mc_servers_dat_txt = consts.CONFIG_DIR / "mc_servers_dat_path.txt"
    if mc_servers_dat_txt.is_file():
        file_contents = mc_servers_dat_txt.read_text(encoding="utf-8").rstrip()
        if Path(file_contents).is_file():
            return Path(file_contents).resolve()
        print(f"  Config's {mc_servers_dat_txt.name} contains invalid path.")
        print("    Delete file for script to locate servers.dat again.")
    else:
        for root, _, files in os.walk(Path().home()):
            if "servers.dat" in files and root.endswith("minecraft"):
                file_path = Path(root) / "servers.dat"
                mc_servers_dat_txt.write_text(str(file_path), encoding="utf-8")
                return file_path
        print("  Path for MC client's servers.dat not found from home dir.")
    return None
