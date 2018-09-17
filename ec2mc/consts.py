"""ec2mc constants

Variables with "Set in..." comments are set once elsewhere.
"""

from pathlib import Path

# Path of script's distribution's inner ec2mc directory.
DIST_DIR = Path(__file__).parent

# Directory for ec2mc to find/create its configuration file(s).
CONFIG_DIR = Path().home()/".ec2mc"
# JSON file path for script user's configuration.
CONFIG_JSON = CONFIG_DIR/"config.json"
# PEM/PPK files containing RSA private key for SSHing into instances.
# Set in ec2mc.validate.validate_setup:main (Namespace used as file name)
RSA_KEY_PEM = None
RSA_KEY_PPK = None

# Directory for ec2mc to find AWS setup files to upload to AWS.
AWS_SETUP_DIR = CONFIG_DIR/"aws_setup"
# JSON file containing AWS setup instructions.
AWS_SETUP_JSON = AWS_SETUP_DIR/"aws_setup.json"

# Directory for ec2mc to find YAML instance templates
USER_DATA_DIR = AWS_SETUP_DIR/"user_data"
# Directory for ec2mc to find IP handlers for checked/started instances
IP_HANDLER_DIR = AWS_SETUP_DIR/"ip_handlers"

# Use IP handler script described by an instance's IpHandler tag.
# Set in ec2mc.validate.validate_config:main
USE_HANDLER = None

# IAM user data needed for AWS programmatic access.
# Set in ec2mc.validate.validate_config:validate_user
KEY_ID = None
KEY_SECRET = None
IAM_ARN = None
IAM_NAME = None

"""This string is used for the following purposes:
- Path prefix for IAM groups, policies, and users ("/" on both sides).
- Name and Namespace tags of:
  - VPC created in each region.
    - VPC's route table.
  - Internet gateway created in each region.
  - SSH key pair created in each region.
- Namespace tag of:
  - Created instances.
  - Allocated elastic IP addresses.
"""
# Set in ec2mc.validate.validate_setup:main
NAMESPACE = None

# Limit configuration RW access to owner of file(s).
CONFIG_PERMS = 0o600
# Private key files must be read-only, and only readable by user.
PK_PERMS = 0o400

# Tuple of regions found with ec2:GetRegions (filtered through whitelist)
# Set in ec2mc.validate.validate_config:validate_region_whitelist
REGIONS = None
