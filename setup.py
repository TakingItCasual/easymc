from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ec2mc',
    version='0.1.3',
    description='AWS EC2 instance manager for Minecraft servers',
    long_description=long_description,
    author='TakingItCasual',
    author_email='takingitcasual+gh@gmail.com',
    url='https://github.com/TakingItCasual/ec2mc',
    download_url='https://github.com/TakingItCasual/ec2mc/archive/v0.1.3.tar.gz',
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
    packages=find_packages(exclude=['docs']),
    python_requires='~=3.6',
    entry_points={
        'console_scripts': [
            'ec2mc=ec2mc.__main__:main',
        ],
    },
    package_data={
        'ec2mc': [
            'aws_setup_src/*.json',
            'aws_setup_src/iam_policies/*.json'
        ]
    },
    install_requires=[
        'boto3',
        'nbtlib',
        'deepdiff'
    ]
)
