import boto3

from stuff import simulate_policy

def main(user_info, args):
    """Creates and initializes a new instance.

    Create new instance and initialize it using scripts from the setup folder.
    """

    pass


def add_documentation(argparse_obj, module_name):
    cmd_arg = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])
    

def blocked_actions(user_info):
    """Returns list of denied AWS actions used in the above main()."""
    blocked_actions = []
    blocked_actions.extend(simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances"
    ]))
    blocked_actions.extend(simulate_policy.blocked(user_info, actions=[
        "ec2:RunInstances"
    ], context={
        "ec2:InstanceType": ["t2.small"]
    }))
    return blocked_actions