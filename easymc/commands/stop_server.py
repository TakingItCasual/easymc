import boto3

from stuff import simulate_policy

def main(user_info, args):
    """Forces the server and instance to stop.
    
    Send a StopInstances command to instance(s). Server(s) will save data.
    """
    
    pass


def add_documentation(argparse_obj, module_name):
    cmd_arg = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])


def blocked_actions(user_info):
    """Returns list of denied AWS actions used in the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances", 
        "ec2:StopInstances"
    ])
