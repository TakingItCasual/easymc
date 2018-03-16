def assert_empty(blocked_actions):
    """used with simulate_policy, which returns a list of denied AWS actions"""
    if blocked_actions:
        err(["Missing following IAM permission(s):"] + blocked_actions)


def err(quit_message_list):
    """first prepend Error to the first quit message, then quit"""
    quit_message_list[0] = "Error: " + quit_message_list[0]
    q(quit_message_list)


def q(quit_message_list=None):
    """quits ec2mc when called by raising SystemExit"""
    if quit_message_list:
        print("")
        for quit_message in quit_message_list:
            print(quit_message)
    raise SystemExit(0) # Equivalent to sys.exit(0)
