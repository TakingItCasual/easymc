import boto3

from stuff import simulate_policy

def main(user_info, kwargs):
    """Downloads server's world folder as zip.
    
    Have the instance zip the world folder and send it to user via FTP.
    """

    pass


def add_documentation(argparse_obj, module_name):
    cmd_arg = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])


def blocked_actions(user_info):
    """Returns list of denied AWS actions used in the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances", 
        "ssm:RunCommand"
    ])
