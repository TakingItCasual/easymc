import boto3

import const
from stuff import simulate_policy

def main(user_info, args):
    """SSH into an EC2 instance using a .pem private key

    The private key is searched for from the script's config folder.
    """
    
    pass


def add_documentation(argparse_obj, module_name):
    cmd_arg = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])


def blocked_actions(user_info):
    """Returns list of denied AWS actions needed to run the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances"
    ])
