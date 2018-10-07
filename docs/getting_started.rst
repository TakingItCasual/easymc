Getting Started
===============

.. role:: bash(code)
   :language: bash

Script Installation
-------------------

This script requires Python (version 3.6 or greater).
Python can be downloaded from https://www.python.org/.
If your OS is 64-bit, please download the latest 64-bit version of Python from the downloads page for your OS (e.g. `Windows x86-64 executable installer`_).
In Python's installer, enable the "Add Python3.x to PATH" option so that Python can be used from a terminal.
The script can then be installed from a terminal with pip::

    python -m pip install ec2mc

To create the script's configuration folder (.ec2mc) under your home folder, run any script command.
For example::

    ec2mc servers check

You will get a "Configuration is not set" error, but the folder will be created (e.g. "C:\\Users\\Larry\\.ec2mc\\").

Amazon Web Services Setup
-------------------------

A word of forewarning: You cannot remove your AWS payment method.
If you want to stop using AWS, you should close your account (see `Cleaning Up`_).
Please be aware of the various costs that using this script can incur (see Costs_).

To create the necessary AWS account, visit https://aws.amazon.com/.
(You'll need to provide information such as your address, phone number, and credit/debit card.)

This script requires an AWS IAM user access key to interact with your account.
To set up your AWS account with the configuration provided by the script, a temporary IAM user with administrator privileges is needed.
The script provides IAM group permissions to prevent accidentally creating large and expensive servers, so the temporary user should be deleted after creating an IAM user under the setup_users IAM group.

To create the temporary IAM user, go to your `IAM Management Console`_ and create a new user.
In step 1, name the IAM user, and enable "Programmatic access" for "Access type".
In step 2, switch to "Attach existing policies directly" and enable "AdministratorAccess".
Create the user.
Keep the page that loads open for the next step.

To have the script use the IAM user access key, you can download the accessKeys.csv file (by clicking "Download .csv") and move the file to the script's configuration folder.
Alternatively, you can copy the access key ID and secret access key, and paste them into the corresponding inputs for the access key configuration command.
For example::

    ec2mc configure access_key AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

The script will estimate the closest `AWS Region`_ to you and set it as your region whitelist.
However, as automated latency comparisons are not perfect, it is recommended to set the region whitelist manually to ensure low latency.
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

The :bash:`--default` argument sets Larry's access key as the script's default access key.

The temporary IAM user should then be deleted from your `IAM Management Console`_.

Server Creation
---------------

Please note that AWS refers to the servers they provide as "instances".
AWS EC2 On-Demand instances (the cloud servers) can be started and stopped at will, and you will only be billed for the time they're running (see Costs_).

Server IP Persistence
~~~~~~~~~~~~~~~~~~~~~

By default, the script creates an instance which receives a different IP each time it's started, as this is the cheaper option (see Costs_).
An instance can be created with an elastic IP address (a persistent IP) by appending :bash:`--elastic_ip` to the instance creation command.
An elastic IP address can still be attached afterwards with the `address subcommands`_.

To handle non-persistent IPs, the script contains functionality to automatically update instance IPs in the the local Minecraft client's server list.
The server list will be updated whenever either of the two following script commands are run::

    ec2mc servers check
    ec2mc servers start

This functionality is still available for instances with persistent IP addresses.

You could modify your Minecraft client shortcut to automatically run the :bash:`start` command, to eliminate the need to manually use the script from a terminal to start servers and update IPs in your server list.

Creating The Server
~~~~~~~~~~~~~~~~~~~

The script provides the template "mc_template" for creating a Minecraft 1.13.1 vanilla server.
Create an instance (e.g. named "test_server") using the following command::

    ec2mc server create test_server mc_template

Or if a persistent IP address is desired::

    ec2mc server create test_server mc_template --elastic_ip

The server will take some minutes to initialize before it is ready for use/management.

All provided templates contain bash scripts (which are uploaded to the instances themselves) which will shut down the instances after 10 consecutive minutes of no online players (and no SSH connections).

(A template for a Forge server is also included: "cnb_template". See Customization_ for how to modify the templates.)

Server Management
-----------------

You should now have an EC2 instance hosting a Minecraft server up and running.
See Commands_ for the various commands that the script provides for managing instances.

If you want to manage the server directly (e.g. to make yourself a server operator), you can SSH into the instance with the script (provided you have OpenSSH_ or PuTTY_ installed) using the following command::

    ec2mc server ssh

You can then access the server's console by typing :bash:`screen -r`.
To exit the server's console, use :bash:`Ctrl-a`, :bash:`Ctrl-d`.
You can then close the SSH connection by typing :bash:`exit`.

(Note that it is possible to SSH into the instance before it is done initializing, in which case the server won't be running and you'll get booted for the post-initialization reboot.)

Afterword
---------

See `Managing Users`_ for how to give friends/family IAM user access keys so they can join and start the server themselves.


.. _Windows x86-64 executable installer: https://www.python.org/downloads/windows/

.. _IAM Management Console: https://console.aws.amazon.com/iam/home#/users

.. _AWS Region: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions

.. _address subcommands: https://github.com/TakingItCasual/ec2mc/blob/master/docs/commands.rst#address-subcommands

.. _OpenSSH: https://www.mls-software.com/opensshd.html

.. _PuTTY: https://www.putty.org/

.. _Managing Users: https://github.com/TakingItCasual/ec2mc/blob/master/docs/managing_users.rst

.. _Customization: https://github.com/TakingItCasual/ec2mc/blob/master/docs/customization.rst

.. _Commands: https://github.com/TakingItCasual/ec2mc/blob/master/docs/commands.rst

.. _Costs: https://github.com/TakingItCasual/ec2mc/blob/master/docs/costs.rst

.. _Cleaning Up: https://github.com/TakingItCasual/ec2mc/blob/master/docs/cleaning_up.rst
