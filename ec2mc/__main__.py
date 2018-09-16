#!/usr/bin/env python3
"""AWS EC2 instance manager for Minecraft servers. Requires IAM user
access key associated with an AWS account. To use a specific command,
the necessary permissions must be attached to the IAM group that the
IAM user is a part of.
"""

import sys

from ec2mc import __version__
from ec2mc.utils.base_classes import ProperIndentParser
from ec2mc.validate import validate_config
from ec2mc.validate import validate_setup
from ec2mc.utils import halt

from ec2mc.commands import configure_cmd
from ec2mc.commands import aws_setup_cmd
from ec2mc.commands import server_cmds
from ec2mc.commands import servers_cmds
from ec2mc.commands import address_cmds
from ec2mc.commands import user_cmds

#import pprint
#pp = pprint.PrettyPrinter(indent=2)

def main(args=None):
    """ec2mc script's entry point

    Args:
        args (list): Args for argparse. If None, set to sys.argv[1:].
    """
    if args is None:
        args = sys.argv[1:]
    try:
        # Available commands from the ec2mc.commands directory
        commands = [
            configure_cmd.Configure(),
            aws_setup_cmd.AWSSetup(),
            server_cmds.Server(),
            servers_cmds.Servers(),
            address_cmds.Address(),
            user_cmds.User()
        ]

        # Use argparse to turn args into dict of arguments
        kwargs = argv_to_kwargs(args, commands)
        # Get the command class object from the commands list
        chosen_cmd = next(cmd for cmd in commands
            if cmd.cmd_name() == kwargs['command'])

        # If basic configuration being done, skip config validation
        if not (chosen_cmd.cmd_name() == "configure" and
                kwargs['action'] != "swap_key"):
            # Validate config's config.json
            validate_config.main()
            # Validate config's aws_setup.json and YAML instance templates
            validate_setup.main()

        # Validate IAM user has needed permissions to use the command
        halt.assert_empty(chosen_cmd.blocked_actions(kwargs))
        # Use the command
        chosen_cmd.main(kwargs)
    except SystemExit:
        return False
    return True


def argv_to_kwargs(args, commands):
    """ínitialize ec2mc's argparse and its help

    Returns:
        dict: Parsed argparse arguments.
            'command': First positional argument.
            Other key-value pairs vary depending on the command. See command's
                add_documentation method to see its args.
    """
    parser = ProperIndentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    cmd_parser = parser.add_subparsers(metavar="<command>", dest="command")
    cmd_parser.required = True

    for command in commands:
        command.add_documentation(cmd_parser)

    if not args:
        args = ["-h"]

    return vars(parser.parse_args(args))


if __name__ == "__main__":
    main()
