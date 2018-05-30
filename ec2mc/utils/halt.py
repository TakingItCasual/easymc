"""provides functions to kill the script by raising SystemExit"""

def assert_empty(blocked_actions):
    """used with verify_perms, which returns list of denied AWS actions"""
    if blocked_actions:
        err(["Missing following IAM permission(s):"] + blocked_actions)


def err(halt_message_list):
    """prepend "Error: " to first halt message, then halt"""
    halt_message_list[0] = "Error: " + halt_message_list[0]
    q(halt_message_list)


def q(halt_message_list=None):
    """halts the script by raising SystemExit"""
    if halt_message_list:
        print("")
        for halt_message in halt_message_list:
            print(halt_message)
    raise SystemExit(0) # Equivalent to sys.exit(0)
