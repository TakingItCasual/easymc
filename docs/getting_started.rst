Getting Started
===============

|PyPI Version| |Python Version|

Script Installation
-------------------

This script requires Python (version 3.6 or greater).
Python can be downloaded from http://www.python.org/ (during installation, enable "Add Python3.x to PATH").
The script can then be installed with pip::

    pip install ec2mc

To create the script's configuration folder (.ec2mc/) under your home folder, run any script command.
For example::

    ec2mc servers check

You will get a "configuration is not set" error, but the folder will be created.

Amazon Web Services Setup
-------------------------

To create the necessary AWS account, visit https://aws.amazon.com/.

This script requires AWS IAM user credentials to interact with your account.
To set up your AWS account, a temporary IAM user is needed.
To create the IAM user, visit your `IAM Management Console`_ and create a new user.

In step 1, give the IAM user a name, and enable "Programmatic access" for "Access type".
In step 2, switch to "Attach existing policies directly" and enable "AdministratorAccess".
Create the user.
Keep the page that loads open for the next step.

To set the credentials for the script, you can download your IAM user's credentials.csv file (by clicking "Download .csv") and move the file to the script's configuration folder. Alternatively, you can copy the IAM user's access key ID and secret access key, and paste them into the corresponding inputs given by the following command::

    ec2mc configure

To verify the previous steps, attempt to use the following command again::

    ec2mc servers check

If the previous steps were successfully completed, the script will output a "credentials verified" notification.

Upload the default setup included with the script with the following command::

    ec2mc aws_setup upload

To make changes to the setup to be uploaded to AWS, see Customization_.

The administrator access given to the temporary IAM user is potentially dangerous, so create a (WIP...)

Server Creation
---------------

(WIP)


.. _IAM Management Console: https://console.aws.amazon.com/iam/home#/users

.. _Customization: https://github.com/TakingItCasual/ec2mc/blob/master/docs/customization.rst

.. |PyPI Version| image:: https://raw.githubusercontent.com/TakingItCasual/ec2mc/master/docs/images/pypi-v0.1.3-orange.svg?sanitize=true
   :target: https://pypi.org/project/ec2mc/

.. |Python Version| image:: https://raw.githubusercontent.com/TakingItCasual/ec2mc/master/docs/images/python-3.6-blue.svg?sanitize=true
   :target: https://pypi.org/project/ec2mc/
