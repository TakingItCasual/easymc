import boto3
import paramiko

from verify import verify_instances
from stuff import simulate_policy
from stuff import quit_out
from commands.check_server import add_documentation_args

def main(user_info, args):
    """SSH into an EC2 instance using a .pem private key

    The private key is searched for from the script's config folder. Currently 
    SSH is only supported with a .pem private key, and using multiple keys is 
    not supported: all instances under an AWS account must share a private key.
    """
    
    instances = verify_instances.main(user_info, args)

    if len(instances) > 1:
        quit_out.q(["Error: Instance search returned multiple results.", 
            "  Narrow filter(s) so that only one instance is found."])

    #pkey = paramiko.RSAKey.from_private_key_file(pkey_file_path)
    #ssh_client = paramiko.SSHClient()
    #ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def add_documentation(argparse_obj, module_name):
    cmd_parser = argparse_obj.add_parser(module_name, 
        help=main.__doc__.splitlines()[0])
    add_documentation_args(cmd_parser)


def blocked_actions(user_info):
    """Returns list of denied AWS actions used in the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances"
    ])
