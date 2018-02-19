def assert_empty(blocked_actions):
    """Used with simulate_policy, which returns list of denied AWS actions."""
    if blocked_actions:
        q(["Error: Missing following IAM permission(s):"] + blocked_actions)


def q(quit_message_list=None):
    """Quits the script when called by raising SystemExit."""
    if quit_message_list:
        print("")
        for quit_message in quit_message_list:
            print(quit_message)
    raise SystemExit(0) # Equivalent to sys.exit(0)
