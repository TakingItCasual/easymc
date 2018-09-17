Getting Started
===============

.. role:: bash(code)
   :language: bash

Script Installation
-------------------

This script requires Python (version 3.6 or greater).
Python can be downloaded from http://www.python.org/.
If your OS is 64-bit, please find and download the latest 64-bit version of Python from the downloads page for your OS (32-bit Python can't use 64-bit exclusive executables).
In Python's installer, enable the "Add Python3.x to PATH" option so that Python can be used from a terminal.
The script can then be installed from a terminal with pip::

    python -m pip install ec2mc

(If the preceding command outputs a SyntaxError, you've installed an incorrect version of Python.)

To create the script's configuration folder (.ec2mc) under your home folder, run any script command.
For example::

    ec2mc servers check

You will get a "Configuration is not set" error, but the folder will be created (e.g. "C:\\Users\\Larry\\.ec2mc\\").

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

You must specify what `AWS Region`_\(s) the script will interact with (ideally, the one(s) closest to you).
For example, to restrict the script to interacting with just the London region::

    ec2mc configure whitelist eu-west-2

To verify the previous steps, attempt to use the following command again::

    ec2mc servers check

If the previous steps were done correctly, the script will output a "Access key validated as ..." notification.

Upload the default AWS account configuration included with the script with the following command::

    ec2mc aws_setup upload

(For an explanation of what is uploaded to AWS, and how it can be customized, see Customization_.)

Create an IAM user (e.g. named "Larry") under the setup_users IAM group with the script::

    ec2mc user create Larry setup_users --default

The :bash:`--default` argument sets the new user's access key as the script's default access key.
For more on IAM user management, see `Managing Users`_.

The temporary IAM user should then be deleted from your `IAM Management Console`_.

Server Creation
---------------

Please note that AWS refers to the servers they provide as "instances".
AWS EC2 On-Demand instances (the cloud servers) can be started and stopped at will, and you will only be charged for the time they're running (see Costs_).

Server IP Persistence
~~~~~~~~~~~~~~~~~~~~~

By default, the script creates an instance which gets a different IP each time it's started, as this is the cheaper option (see Costs_).
To create an instance with an elastic IP address (a persistent IP), append :bash:`--elastic_ip` to the instance creation command.

To handle non-persistent IPs, the script contains functionality to automatically update instance IPs in the the local Minecraft client's server list.
The server list will be updated whenever either of the two following script commands are run::

    ec2mc servers check
    ec2mc servers start

This functionality is still available for instances with persistent IP addresses.

You could modify your Minecraft client shortcut to automatically run the :bash:`start` command, to eliminate the need to manually start servers and update IPs in your server list.

Creating The Server
~~~~~~~~~~~~~~~~~~~

The script provides the template "mc_template" for creating a Minecraft 1.13.1 vanilla server.
Create an instance (e.g. named "test_server") using the following command::

    ec2mc server create mc_template test_server

Or if a persistent IP address is desired::

    ec2mc server create mc_template test_server --elastic_ip

The server will take a few minutes to initialize before it is ready for use/management.

All provided templates contain bash scripts (which are uploaded to the instances themselves) which will shut down the instances after 10 consecutive minutes of no online players (and no SSH connections).

(A template for a Forge server is also included: "cnb_template". See Customization_ for how to make your own template.)

Conclusion
----------

You should now have an EC2 instance hosting a Minecraft server up and running.
If you want to manage the server directly (e.g. to make yourself a server operator), you can SSH into it with the script (provided you have OpenSSH or PuTTY installed) using the following command::

    ec2mc server ssh

You can then access the server's console by typing :bash:`screen -r` (use :bash:`Ctrl-a`, :bash:`Ctrl-d` to exit the console, then type :bash:`exit` to close the SSH connection).

See `Managing Users`_ for how to give other people IAM user access keys so they can join and start the server themselves.


.. _IAM Management Console: https://console.aws.amazon.com/iam/home#/users

.. _Customization: https://github.com/TakingItCasual/ec2mc/blob/master/docs/customization.rst

.. _Managing Users: https://github.com/TakingItCasual/ec2mc/blob/master/docs/managing_users.rst

.. _Costs: https://github.com/TakingItCasual/ec2mc/blob/master/docs/costs.rst

.. _AWS Region: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions
