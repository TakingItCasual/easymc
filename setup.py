import os.path
#from codecs import open # For Python2.x

from setuptools import setup, find_packages

VERSION = "0.1.3"
REPO_URL = 'https://github.com/TakingItCasual/ec2mc'

README_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "README.rst")
with open(README_PATH, encoding='utf-8') as f:
    LONG_DESC = f.read()

# The OS restrictions are due to the cryptography package.
setup(
    name='ec2mc',
    version=VERSION,
    description='AWS EC2 instance manager for Minecraft servers',
    long_description=LONG_DESC,
    author='TakingItCasual',
    author_email='takingitcasual+gh@gmail.com',
    url=REPO_URL,
    download_url=f'{REPO_URL}/archive/v{VERSION}.tar.gz',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='mc minecraft ssh server aws ec2 iam',
    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='~=3.6',
    entry_points={'console_scripts': ['ec2mc=ec2mc.__main__:main']},
    package_data={
        'ec2mc.validate.jsonschemas': ['*.json'],
        'ec2mc.aws_setup_src': ['*.json'],
        'ec2mc.aws_setup_src.ip_handlers': ['*.py'],
        'ec2mc.aws_setup_src.iam_policies': ['*.json'],
        'ec2mc.aws_setup_src.vpc_security_groups': ['*.json'],
        'ec2mc.aws_setup_src.user_data': ['*.yaml'],
        'ec2mc.aws_setup_src.user_data.mc_template.manage_scripts': ['*']
    },
    install_requires=[
        'boto3',
        'nbtlib',
        'deepdiff',
        'cryptography',
        'ruamel.yaml',
        'jsonschema'
    ]
)
