import pytest

from ec2mc import __main__

def test_vpc_setup():
    """test aws_setup delete command"""
    assert __main__.main([
        "aws_setup", "delete"
    ]) is not False
    assert __main__.main([
        "configure", "whitelist", "eu-central-1"
    ]) is not False
