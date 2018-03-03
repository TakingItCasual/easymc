"""ec2mc constants

Variables initialized as None are set *once* elsewhere.
"""

import os

# Location where ec2mc finds/creates its configuration file(s).
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".ec2mc", "")
# Location where ec2mc finds the AWS setup files to upload to AWS.
AWS_SETUP_DIR = os.path.join((CONFIG_DIR + "aws_setup"), "")

# IAM user data needed for AWS programmatic access.
# Set in ec2mc.verify.verify_config:verify_user
IAM_ID = None
IAM_SECRET = None
IAM_ARN = None
IAM_NAME = None

# File path for the Minecraft client's server list.
# (Optionally) set in ec2mc.verify.verify_config:main
SERVERS_DAT = None

# Limit configuration RW access to owner of file(s).
CONFIG_PERMS = 0o600
# Private key files must be read-only, and only readable by the user.
PK_PERMS = 0o400

# Creating an EC2 client requires a region, even for listing all regions.
DEFAULT_REGION = "us-east-1"

# AWS Linux AMI (used to decide the instance OS on creation).
# TODO: Update to AWS Linux 2 LTS when it comes out
EC2_OS_AMI = "ami-5652ce39"
# Used during instance creation for setting instance's storage space.
# I don't know if there's any connection to the AMI so I'll just leave it here.
DEVICE_NAME = "/dev/xvda"
# EC2 security groups are searched for a GroupName with the following.
SECURITY_GROUP_FILTER = "minecraft"
