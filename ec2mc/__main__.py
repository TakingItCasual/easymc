#!/usr/bin/env python3
"""AWS EC2 instance manager for Minecraft servers. Requires IAM user 
access key associated with an AWS account. To use a specific command, 
the necessary permissions must be attached to the IAM group that the 
IAM user is a part of.
"""

import sys
import argparse

from ec2mc.validate import validate_config
from ec2mc.validate import validate_setup
from ec2mc.utils import halt

from ec2mc.commands import configure
from ec2mc.commands import aws_setup
from ec2mc.commands import server
from ec2mc.commands import servers
from ec2mc.commands import user

#import pprint
#pp = pprint.PrettyPrinter(indent=2)

def main(args=None):
    """ec2mc script's entry point

    Args:
        args (list): Args for argparse. If None, use CLI's args.
    """
    try:
        if sys.version_info < (3, 6):
            halt.err("Python version 3.6 or greater required.")

        if args is None:
            args = sys.argv[1:]

        # Available commands from the ec2mc.commands directory
        commands = [
            configure.Configure(),
            aws_setup.AWSSetup(),
            server.Server(),
            servers.Servers(),
            user.User()
        ]

        # Use argparse to turn args into dict of arguments
        kwargs = argv_to_kwargs(args, commands)
        # Get the command class object from the commands list
        chosen_cmd = next(cmd for cmd in commands
            if cmd.module_name() == kwargs['command'])

        # If basic configuration being done, skip config validation
        if not (chosen_cmd.module_name() == "configure" and
                kwargs["swap_user"] is None):
            # Validate config's config.json and server_titles.json
            validate_config.main()
            # Validate config's aws_setup.json and YAML instance templates
            validate_setup.main()

        # Validate IAM user has needed permissions to use the command
        halt.assert_empty(chosen_cmd.blocked_actions(kwargs))
        # Use the command
        chosen_cmd.main(kwargs)
    except SystemExit:
        pass


def argv_to_kwargs(args, commands):
    """ínitialize ec2mc's argparse and its help

    Returns:
        dict: Parsed argparse arguments.
            'command': First positional argument.
            Other key-value pairs vary depending on the command. See the 
                command's add_documentation method to see its args.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    cmd_args = parser.add_subparsers(metavar="{command}"+" "*2, dest="command")
    cmd_args.required = True

    for command in commands:
        command.add_documentation(cmd_args)

    if not args:
        parser.print_help()
        halt.q()

    return vars(parser.parse_args(args))


if __name__ == "__main__":
    main()
