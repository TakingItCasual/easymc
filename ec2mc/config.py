"""ec2mc constants

Variables initialized as None are set *once* elsewhere.
"""

import os.path

# Path of the distribution's inner ec2mc directory
DIST_DIR = os.path.join(os.path.dirname(__file__), "")

# Directory for ec2mc to find/create its configuration file(s).
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".ec2mc", "")
# JSON file containing IAM credentials, servers.dat path, and region whitelist.
CONFIG_JSON = f"{CONFIG_DIR}config.json"
# JSON file containing instance title(s) for the MC client's server list.
SERVER_TITLES_JSON = f"{CONFIG_DIR}server_titles.json"
# PEM file containing RSA private key for SSHing into instances.
# Set in ec2mc.verify.verify_setup:main (Namespace used as file name)
RSA_PRIV_KEY_PEM = None

# Directory for ec2mc to find AWS setup files to upload to AWS.
AWS_SETUP_DIR = os.path.join((f"{CONFIG_DIR}aws_setup"), "")
# JSON file containing AWS setup instructions.
AWS_SETUP_JSON = f"{AWS_SETUP_DIR}aws_setup.json"

# Directory for ec2mc to find YAML instance templates
USER_DATA_DIR = os.path.join((f"{AWS_SETUP_DIR}user_data"), "")

# IAM user data needed for AWS programmatic access.
# Set in ec2mc.verify.verify_config:verify_user
IAM_ID = None
IAM_SECRET = None
IAM_ARN = None
IAM_NAME = None

# File path for Minecraft client's server list.
# (Optionally) set in ec2mc.verify.verify_config:main
SERVERS_DAT = None

"""This string is used for the following purposes:
- Path prefix for IAM groups, policies, and users ("/" on both sides).
- Name and Namespace tags of VPC created in each region.
- Name of SSH key pair created in each region.
- Namespace tag of created instances.
"""
# Set in ec2mc.verify.verify_setup:main
NAMESPACE = None

# Limit configuration RW access to owner of file(s).
CONFIG_PERMS = 0o600
# Private key files must be read-only, and only readable by user.
PK_PERMS = 0o400

# Creating an EC2 client requires a region, even for listing all regions.
DEFAULT_REGION = "us-east-1"
# Restrict AWS region(s) the script interacts with (if not None).
# (Optionally) set in ec2mc.verify.verify_config:main
REGION_WHITELIST = None
