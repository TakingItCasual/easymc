import pytest

from ec2mc import __main__

def test_user_commands():
    """use aws_setup commands, and test all user commands."""
    assert __main__.main([
        "aws_setup", "upload"
    ]) is not False
    assert __main__.main([
        "user", "create", "ec2mc_test_user", "basic_users", "--default"
    ]) is not False
    assert __main__.main([
        "configure", "swap_user", "TakingItCasual"
    ]) is not False
    assert __main__.main([
        "user", "delete", "ec2mc_test_user"
    ]) is not False
    assert __main__.main([
        "aws_setup", "delete"
    ]) is not False
