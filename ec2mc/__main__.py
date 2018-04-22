#!/usr/bin/env python3
"""AWS EC2 instance manager for Minecraft servers. Requires IAM user 
credentials associated with an AWS account. To use a specific command, 
the necessary permissions must be attached to the IAM group that the 
IAM user is a part of.
"""

import sys
import argparse

sys.dont_write_bytecode = True

from ec2mc.verify import verify_config
from ec2mc.verify import verify_aws_setup
from ec2mc.stuff import quit_out

from ec2mc.commands import configure
from ec2mc.commands import aws_setup
from ec2mc.commands import server
from ec2mc.commands import create_server

#import pprint
#pp = pprint.PrettyPrinter(indent=2)

def main(args=None):
    """ec2mc's entry point

    The config is verified, the CLI arguments are parsed, and if all goes
    well, ec2mc will interact with the specified AWS EC2 instance(s).

    Args:
        args (list): Args for argparse. If None, use CLI's args.
    """

    try:
        if args is None:
            args = sys.argv[1:]

        if sys.version_info < (3, 6):
            quit_out.err(["Python version 3.6 or greater required."])

        # Available commands from the ec2mc.commands directory
        commands = [
            configure.Configure(),
            aws_setup.AWSSetup(),
            server.Server(),
            create_server.CreateServer()
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
        # Verify that aws_setup is in the config
        verify_aws_setup.main()

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
        dict: Parsed argparse arguments.
            "command": First positional argument.
            Other key-value pairs vary depending on the command. See the 
                command's add_documentation method to see its args.
    """

    parser = argparse.ArgumentParser(description=__doc__)
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
