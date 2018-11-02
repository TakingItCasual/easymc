"""provides functions to kill the script by raising SystemExit"""

import sys
from typing import List

def assert_empty(blocked_actions: List[str]) -> None:
    """used with validate_perms, which returns list of denied AWS actions"""
    if blocked_actions:
        err("IAM user missing following permission(s):",
            *sorted(list(set(blocked_actions))))


def err(*halt_messages: str) -> None:
    """prepend "Error: " to first halt message, then halt"""
    halt_msg_list = list(halt_messages)
    halt_msg_list[0] = f"Error: {halt_messages[0]}"
    stop(*halt_msg_list)


def stop(*halt_messages: str) -> None:
    """halts the script by raising SystemExit"""
    if halt_messages:
        print("")
        print("\n".join(halt_messages), file=sys.stderr, flush=True)
    sys.exit(1)
