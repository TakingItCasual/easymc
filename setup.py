import os.path
import sys
from setuptools import setup
from setuptools import find_packages

from ec2mc import __version__
from ec2mc import __min_python__

CURRENT_PYTHON = sys.version_info[:2]
if CURRENT_PYTHON < __min_python__:
    sys.stderr.write("""
==========================
Unsupported Python version
==========================

This version of ec2mc requires Python {}.{}. You're using Python {}.{}.
Install the required Python version and ensure it is in your PATH.
""".format(*(__min_python__ + CURRENT_PYTHON)))
    sys.exit(1)

REPO_URL = "https://github.com/TakingItCasual/ec2mc"

README_PATH = os.path.join(os.path.dirname(__file__), "README.rst")
with open(README_PATH, encoding="utf-8") as f:
    LONG_DESC = f.read()

setup(
    name="ec2mc",
    version=__version__,
    description="AWS EC2 instance manager for Minecraft servers",
    long_description=LONG_DESC,
    author="TakingItCasual",
    author_email="takingitcasual+gh@gmail.com",
    url=REPO_URL,
    download_url="{}/archive/v{}.tar.gz".format(REPO_URL, __version__),
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: {}".format(__min_python__[0]),
        "Programming Language :: Python :: {}.{}".format(*__min_python__)
    ],
    keywords="mc minecraft ssh server aws ec2 iam cloud-config",
    packages=find_packages(exclude=["docs", "tests"]),
    python_requires="~={}.{}".format(*__min_python__),
    entry_points={'console_scripts': ["ec2mc=ec2mc.__main__:main"]},
    include_package_data=True,
    install_requires=[
        "boto3 ~= 1.9",
        "nbtlib ~= 1.2",
        "deepdiff ~= 3.3",
        "cryptography ~= 2.3",
        "ruamel.yaml ~= 0.15.0",
        "jsonschema ~= 2.6"
    ]
)
