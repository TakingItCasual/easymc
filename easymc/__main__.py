#!/usr/bin/env python3

import sys

sys.dont_write_bytecode = True

from commands import *
from verify import verify_config
from stuff import quit_out

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

        if args:
            if args[0] == "configure":
                verify_config.configure()
                quit_out.q()

        user_info = {}
        commands_list = [
            {"cmd": "start_server", "obj": start_server}, 
            {"cmd": "check_server", "obj": check_server}, 
            {"cmd": "stop_server", "obj": stop_server}, 
            {"cmd": "get_backup", "obj": get_backup}, 
            {"cmd": "update_mods", "obj": update_mods}, 
            {"cmd": "create_server", "obj": create_server}
        ]

        user_info = verify_config.main()

        if not args:
            describe_arguments(user_info, commands_list)
        arg_cmd = str(args[0])

        if not any(cmd["cmd"] == arg_cmd for cmd in commands_list):
            print("Error: \"" + arg_cmd + "\" is an invalid argument.")
            describe_arguments(user_info, commands_list)

        arg_index = [cmd["cmd"] for cmd in commands_list].index(arg_cmd)
        quit_out.assert_empty(
            commands_list[arg_index]["obj"].blocked_actions(user_info))

        commands_list[arg_index]["obj"].main(user_info, args[1:])

        quit_out.q(["Script completed successfully."])
    except SystemExit:
        pass


def describe_arguments(user_info, commands_list):
    print("")
    print("Checking arguments' IAM permissions requirements...")

    allowed_args = []
    blocked_args = []
    for command in commands_list:
        if not command["obj"].blocked_actions(user_info):
            allowed_args.append(command)
        else:
            blocked_args.append(command)

    if allowed_args:
        print("")
        print("Available arguments:")

        offset_str = max(len(cmd["cmd"]) for cmd in allowed_args) + 2
        for cmd in allowed_args:
            print("  " + cmd["cmd"] + " "*(offset_str-len(cmd["cmd"])) + 
                cmd["obj"].main.__doc__.splitlines()[0])

    if blocked_args:
        print("")
        print("Blocked arguments (missing IAM permissions):")

        offset_str = max(len(cmd["cmd"]) for cmd in blocked_args) + 2
        for cmd in blocked_args:
            print("  " + cmd["cmd"] + " "*(offset_str-len(cmd["cmd"])) + 
                cmd["obj"].main.__doc__.splitlines()[0])
    
    if allowed_args:
        quit_out.q(["Please append an argument to the command."])
    quit_out.q(["Missing IAM permissions to execute any command."])


if __name__ == "__main__":
    main()
