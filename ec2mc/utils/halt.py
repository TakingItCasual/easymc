"""provides functions to kill the script by raising SystemExit"""

def assert_empty(blocked_actions):
    """used with verify_perms, which returns list of denied AWS actions"""
    if blocked_actions:
        err("IAM user missing following permission(s):", *blocked_actions)


def err(*halt_messages):
    """prepend "Error: " to first halt message, then halt"""
    halt_messages = list(halt_messages)
    halt_messages[0] = "Error: " + halt_messages[0]
    q(*halt_messages)


def q(*halt_messages):
    """halts the script by raising SystemExit"""
    if halt_messages:
        print("")
        for halt_message in halt_messages:
            print(halt_message)
    raise SystemExit(0) # Equivalent to sys.exit(0)
