import os.path
#from codecs import open # For Python2.x

from setuptools import setup, find_packages

VERSION = "0.1.3"

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.rst'), encoding='utf-8') as f:
    LONG_DESC = f.read()

setup(
    name='ec2mc',
    version=VERSION,
    description='AWS EC2 instance manager for Minecraft servers',
    long_description=LONG_DESC,
    author='TakingItCasual',
    author_email='takingitcasual+gh@gmail.com',
    url='https://github.com/TakingItCasual/ec2mc',
    download_url='https://github.com/TakingItCasual/ec2mc/archive/v'+VERSION+'.tar.gz',
    platforms=['any'],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='mc minecraft server aws ec2 iam',
    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='~=3.6',
    entry_points={
        'console_scripts': [
            'ec2mc=ec2mc.__main__:main',
        ],
    },
    package_data={
        'ec2mc': [
            'verify/aws_setup_schema.json',
            'aws_setup_src/*.json',
            'aws_setup_src/iam_policies/*.json',
            'aws_setup_src/vpc_security_groups/*.json'
        ]
    },
    install_requires=[
        'boto3',
        'nbtlib',
        'deepdiff',
        'jsonschema'
    ]
)
