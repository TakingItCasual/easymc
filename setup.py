from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='easymc',
    version='0.1.0',
    description='AWS EC2 instance manager for Minecraft servers',
    long_description=long_description,
    author='TakingItCasual',
    author_email='takingitcasual+gh@gmail.com',
    url='https://github.com/TakingItCasual/easymc',
    download_url='https://github.com/TakingItCasual/easymc/archive/0.1.1.tar.gz',
    platforms=['any'],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='mc minecraft server aws ec2 iam',
    packages=find_packages(),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'easymc=__main__:main',
        ],
    },
    install_requires=[
        'boto3',
        'nbtlib'
    ]
)
