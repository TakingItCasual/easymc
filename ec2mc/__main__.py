#!/usr/bin/env python3

import sys
import argparse

sys.dont_write_bytecode = True

from ec2mc.commands import *
from ec2mc.verify import verify_config
from ec2mc.stuff import send_bash
from ec2mc.stuff import quit_out

#import pprint
#pp = pprint.PrettyPrinter(indent=2)

def main(args=None):
    """The script's entry point.

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

        commands = [
            start_server.StartServer(), 
            check_server.CheckServer(), 
            #stop_server.StopServer(), 
            #get_backup.GetBackup(), 
            #update_mods.UpdateMods(), 
            #create_server.CreateServer(), 
            ssh_server.SSHServer()
        ]

        kwargs = argv_to_kwargs(args, commands)
        arg_cmd = kwargs["command"]

        if arg_cmd == "configure":
            verify_config.configure()
            quit_out.q()

        if not any(cmd.module_name() == arg_cmd for cmd in commands):
            print("Error: \"" + arg_cmd + "\" is an invalid argument.")

        user_info = verify_config.main()

        chosen_cmd = [cmd for cmd in commands 
            if cmd.module_name() == arg_cmd][0]
        quit_out.assert_empty(chosen_cmd.blocked_actions(user_info))

        chosen_cmd.main(user_info, kwargs)

        quit_out.q(["Script completed without errors."])
    except SystemExit:
        pass


def argv_to_kwargs(args, commands):
    """Initialize the script's argparse and its help.

    Returns:
        dict: Parsed arguments
            "command": First positional argument
            Other key-value pairs vary depending on the command. See the 
            command's add_documentation function to see its args.
    """

    parser = argparse.ArgumentParser(usage="ec2mc [-h] <command> [<args>]", 
        description=("AWS EC2 instance manager for Minecraft servers. "
            "Requires IAM credentials linked to an AWS account. Not all "
            "commands are necessarily available, as some require specific "
            "IAM permissions."))
    cmd_args = parser.add_subparsers(metavar="<command>"+" "*6, dest="command")

    cmd_args.add_parser("configure", help=verify_config.configure.__doc__)
    for command in commands:
        command.add_documentation(cmd_args)

    if not args:
        parser.print_help()
        quit_out.q()

    return vars(parser.parse_args(args))


if __name__ == "__main__":
    main()
