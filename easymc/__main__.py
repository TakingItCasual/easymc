#!/usr/bin/env python3

import sys
import argparse

sys.dont_write_bytecode = True

from commands import *
from verify import verify_config
from stuff import quit_out
from stuff import send_bash

# import pprint
# pp = pprint.PrettyPrinter(indent=2)

def main(args=None):
    """The script's top level function. 

    The config is verified, the script arguments are parsed, and if all goes
    well, the script will interact with the specified AWS EC2 instance(s).

    Args:
        args (list): The command line arguments passed to the script.
    """

    try:
        if args is None:
            args = sys.argv[1:]

        try:
            assert(sys.version_info >= (3,6))
        except AssertionError:
            quit_out.q(["Error: Python version 3.6 or greater required."])

        commands_list = [
            {"cmd": "start_server", "obj": start_server}, 
            {"cmd": "check_server", "obj": check_server}, 
            {"cmd": "stop_server", "obj": stop_server}, 
            {"cmd": "get_backup", "obj": get_backup}, 
            {"cmd": "update_mods", "obj": update_mods}, 
            {"cmd": "create_server", "obj": create_server}, 
            {"cmd": "ssh_server", "obj": ssh_server}
        ]

        args = argv_to_args(args, commands_list)
        arg_cmd = args["command"]

        if arg_cmd == "configure":
            verify_config.configure()
            quit_out.q()

        user_info = verify_config.main()

        # For testing SSM...
        #if False:
        #    from verify import verify_instances
        #    instance_id = verify_instances.main(user_info, args)[0]["id"]
        #    send_bash.main(user_info, instance_id, ["ifconfig"])
        #    quit_out.q()

        if not any(cmd["cmd"] == arg_cmd for cmd in commands_list):
            print("Error: \"" + arg_cmd + "\" is an invalid argument.")
            describe_arguments(user_info, commands_list)

        chosen_cmd = [cmd for cmd in commands_list if cmd["cmd"] == arg_cmd][0]
        quit_out.assert_empty(chosen_cmd["obj"].blocked_actions(user_info))

        chosen_cmd["obj"].main(user_info, args)

        quit_out.q(["Script completed successfully."])
    except SystemExit:
        pass


def argv_to_args(args, commands_list):
    """Seperating code relating to argparse to its own method.

    Returns:
        dict: Parsed arguments
            "command": First positional argument
            Other key-value pairs vary depending on the command. See the 
            command's add_documentation function to see its args.
    """

    parser = argparse.ArgumentParser(
        description=("AWS EC2 instance manager for Minecraft servers. "
            "Requires IAM credentials linked to an AWS account. Not all "
            "commands are necessarily usable, as some commands require "
            "specific IAM permissions. The SSH command requires a .pem "
            "private key file."))
    cmd_args = parser.add_subparsers(dest="command", metavar=" "*15)

    cmd_args.add_parser("configure", help=verify_config.configure.__doc__)
    for cmd in commands_list:
        cmd["obj"].add_documentation(cmd_args, cmd["cmd"])

    if not args:
        parser.print_help()
        quit_out.q()

    args = vars(parser.parse_args(args))
    if "tagkey" in args and args["tagkey"] and not args["tagvalues"]:
        parser.error("--tagkey requires --tagvalue")

    return args


if __name__ == "__main__":
    main()
