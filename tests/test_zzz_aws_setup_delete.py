import pytest

from ec2mc import __main__

def test_vpc_setup():
    """test aws_setup deletion command"""
    assert __main__.main([
        "aws_setup", "delete"
    ]) is not False
