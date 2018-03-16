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
    """ec2mc's entry point

    The config is verified, the CLI arguments are parsed, and if all goes
    well, ec2mc will interact with the specified AWS EC2 instance(s).

    Args:
        args (list): The command line arguments passed to ec2mc
    """

    try:
        if args is None:
            args = sys.argv[1:]

        try:
            assert(sys.version_info >= (3,6))
        except AssertionError:
            quit_out.err(["Python version 3.6 or greater required."])

        # Available commands from the ec2mc.commands directory
        commands = [
            configure.Configure(),
            #aws_setup.AWSSetup(),
            server.Server(),
            #create_server.CreateServer(),
            #get_backup.GetBackup(),
            #update_mods.UpdateMods()
        ]

        # Use argparse to turn sys.argv into a dict of arguments
        kwargs = argv_to_kwargs(args, commands)
        arg_cmd = kwargs["command"]

        # If the "configure" command was used, skip configuration verification
        if arg_cmd == "configure":
            config_cmd = next(cmd for cmd in commands
                if cmd.module_name() == arg_cmd)
            config_cmd.main()
            quit_out.q()

        # Load and verify the config (primarily for the IAM credentials)
        verify_config.main()

        # Get the command class object from the commands list
        chosen_cmd = next(cmd for cmd in commands
            if cmd.module_name() == arg_cmd)

        # Verify that the IAM user has needed permissions to use the command
        quit_out.assert_empty(chosen_cmd.blocked_actions(kwargs))

        # Use the command
        chosen_cmd.main(kwargs)

        quit_out.q(["ec2mc completed without errors."])
    except SystemExit:
        pass


def argv_to_kwargs(args, commands):
    """ínitialize ec2mc's argparse and its help

    Returns:
        dict: Parsed arguments
            "command": First positional argument
            Other key-value pairs vary depending on the command. See the 
            command's add_documentation method to see its args.
    """

    parser = argparse.ArgumentParser(
        description=("AWS EC2 instance manager for Minecraft servers. "
            "Requires IAM credentials associated with an AWS account. "
            "Depending on your access level some commands may not be "
            "available due to missing IAM permissions."))
    cmd_args = parser.add_subparsers(metavar="{command}"+" "*6, dest="command")
    cmd_args.required = True

    for command in commands:
        command.add_documentation(cmd_args)

    if not args:
        parser.print_help()
        quit_out.q()

    return vars(parser.parse_args(args))


if __name__ == "__main__":
    main()
