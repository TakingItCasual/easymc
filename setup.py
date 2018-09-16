from pathlib import Path
from setuptools import setup
from setuptools import find_packages

from ec2mc import __version__

REPO_URL = "https://github.com/TakingItCasual/ec2mc"

README_PATH = Path(__file__).parent/"README.rst"
LONG_DESC = README_PATH.read_text(encoding="utf-8")

# The OS restrictions are due to the cryptography package.
setup(
    name="ec2mc",
    version=__version__,
    description="AWS EC2 instance manager for Minecraft servers",
    long_description=LONG_DESC,
    author="TakingItCasual",
    author_email="takingitcasual+gh@gmail.com",
    url=REPO_URL,
    download_url=f"{REPO_URL}/archive/v{__version__}.tar.gz",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6"
    ],
    keywords="mc minecraft ssh server aws ec2 iam cloud-config",
    packages=find_packages(exclude=["docs", "tests"]),
    python_requires="~=3.6",
    entry_points={'console_scripts': ["ec2mc=ec2mc.__main__:main"]},
    include_package_data=True,
    install_requires=[
        "boto3 ~= 1.9",
        "nbtlib ~= 1.2",
        "deepdiff ~= 3.3",
        "cryptography ~= 2.3",
        "ruamel.yaml >= 0.15, < 0.16",
        "jsonschema ~= 2.6"
    ]
)
