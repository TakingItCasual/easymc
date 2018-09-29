from ec2mc import __main__

def test_vpc_setup():
    """test aws_setup upload and check command"""
    assert __main__.main([
        "configure", "whitelist", "eu-central-1", "eu-west-2"
    ]) is not False
    assert __main__.main([
        "aws_setup", "upload"
    ]) is not False
    assert __main__.main([
        "aws_setup", "check"
    ]) is not False
