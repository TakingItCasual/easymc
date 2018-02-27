import os

# Location where the script finds/creates its configuration file(s).
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".ec2mc", "")
# Limit configuration RW access to owner of file(s).
CONFIG_PERMS = 0o600
# Private key files must be read-only, and only readable by the user.
PK_PERMS = 0o400
# Creating an EC2 client requires a region, even for listing all regions.
DEFAULT_REGION = "us-east-1"
# AWS Linux AMI (used to decide the instance OS on creation)
# TODO: Update to AWS Linux 2 LTS when it comes out
AWS_LINUX_AMI = "ami-5652ce39"
# EC2 security groups are searched for a GroupName with the following
SECURITY_GROUP_FILTER = "minecraft"
