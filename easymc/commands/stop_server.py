import boto3

from stuff import simulate_policy

def main(config_data, *args):
    """Forces the server and instance to stop.
    
    Send a StopInstances command to instance(s). Server(s) will save data.
    """
    
    pass


def blocked_actions(user_info):
    """Returns list of denied AWS actions needed to run the above main()."""
    return simulate_policy.blocked(user_info, actions=[
        "ec2:DescribeInstances", 
        "ec2:StopInstances"
    ])
