Getting Started
===============

|PyPI Version| |Python Version|

Script Installation
-------------------

This script requires Python (version 3.6 or greater).
Python can be downloaded from http://www.python.org/.
If your OS is 64-bit, please find and download the latest 64-bit version of Python from the downloads page for your OS (32-bit Python can't use 64-bit exclusive executables).
During Python's installation, enable the "Add Python3.x to PATH" option so that Python can be used from a terminal.
The script can then be installed from a terminal with pip::

    pip install ec2mc

To create the script's configuration folder (.ec2mc/) under your home folder, run any script command.
For example::

    ec2mc servers check

You will get a "Configuration is not set" error, but the folder will be created.

Amazon Web Services Setup
-------------------------

To create the necessary AWS account, visit https://aws.amazon.com/.
You'll need to attach a payment method, as the script uses services not covered by the free tier.

This script requires an AWS IAM user access key to interact with your account.
To set up your AWS account with the configuration provided by the script, a temporary IAM user is needed.
The script provides IAM group permissions to prevent accidentally creating large and expensive servers, so the temporary user should be deleted after creating an IAM user under the setup_users IAM group.

To create the temporary IAM user, go to your `IAM Management Console`_ and create a new user.
In step 1, name the IAM user, and enable "Programmatic access" for "Access type".
In step 2, switch to "Attach existing policies directly" and enable "AdministratorAccess".
Create the user.
Keep the page that loads open for the next step.

To have the script use the access key, you can download your IAM user's accessKeys.csv file (by clicking "Download .csv") and move the file to the script's configuration folder.
Alternatively, you can copy the IAM user's access key ID and secret access key, and paste them into the corresponding inputs for the access key configuration command.
For example::

    ec2mc configure access_key AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

To verify the previous steps, attempt to use the following command again::

    ec2mc servers check

If the previous steps were done correctly, the script will output a "Access key validated as ..." notification.

Upload the default AWS setup included with the script with the following command::

    ec2mc aws_setup upload

(For an explanation of what is uploaded to AWS, and how it can be customized, see Customization_.)

Create an IAM user under the setup_users IAM group (e.g. with the name "Bob") with the script::

    ec2mc user create Bob setup_users --default

The --default argument sets the new user's access key as the script's default access key.
For more on IAM user management, see `Managing Users`_.

The temporary IAM user should then be deleted from your `IAM Management Console`_.

Server Creation
---------------

Please note that AWS refers to the servers they provide as "instances".
AWS EC2 On-Demand instances (the cloud servers) can be turned on and off at will, and you will only be charged for the time they're turned on (see Costs_).

Server IP Persistence
~~~~~~~~~~~~~~~~~~~~~

By default, the script creates an instance which changes its IP address after every reboot, as this is the cheaper option (see Costs_).
To handle this, the script contains functionality to automatically update the local Minecraft client's server list with the current IP(s) of AWS instance(s).
The server list will be updated whenever either of the two following script commands are run::

    ec2mc servers check
    ec2mc servers start

This functionality is still available for instances with persistent IP addresses.

You could modify your Minecraft client shortcut to automatically run the `check` command, to eliminate the need to manually update an IP in the client's server list each time an instance is rebooted.
Or you could modify it to run the `start` command, to also eliminate the need to manually start the server.

Creating The Server
~~~~~~~~~~~~~~~~~~~

The script provides the template "mc_template" for creating a Minecraft 1.13.1 vanilla server.
You must specify an `AWS Region`_ to place the instance in (ideally, the one closest to you).
Create the instance (e.g. in the London region)::

    ec2mc server create eu-west-2 mc_template server_name_goes_here

Or if a persistent IP address is desired::

    ec2mc server create eu-west-2 mc_template server_name_goes_here --elastic_ip

All provided templates contain scripts (which will be uploaded to the instances themselves) which will shut down the instances after 10 consecutive minutes of no online players.

(A template for a Forge server is also included: "cnb_template". See Customization_ for how to make your own template.)

Conclusion
----------

You should now have an EC2 instance hosting a Minecraft server up and running.
If you want to manage the server directly, you can SSH into it with the script using the following command::

    ec2mc server ssh

(This command requires you to have either OpenSSH or PuTTY installed.)

See `Managing Users`_ for how to give your friends IAM user access keys so they can join and start the server themselves.


.. _IAM Management Console: https://console.aws.amazon.com/iam/home#/users

.. _Customization: https://github.com/TakingItCasual/ec2mc/blob/master/docs/customization.rst

.. _Managing Users: https://github.com/TakingItCasual/ec2mc/blob/master/docs/managing_users.rst

.. _Costs: https://github.com/TakingItCasual/ec2mc/blob/master/docs/costs.rst

.. _AWS Region: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions

.. |PyPI Version| image:: https://raw.githubusercontent.com/TakingItCasual/ec2mc/master/docs/images/pypi-v0.1.3-orange.svg?sanitize=true
   :target: https://pypi.org/project/ec2mc/

.. |Python Version| image:: https://raw.githubusercontent.com/TakingItCasual/ec2mc/master/docs/images/python-3.6-blue.svg?sanitize=true
   :target: https://pypi.org/project/ec2mc/
