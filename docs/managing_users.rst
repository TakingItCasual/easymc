Managing Users
==============

.. role:: bash(code)
   :language: bash

The script, by default, provides three IAM groups to place IAM users in: :bash:`basic_users`, :bash:`admin_users`, and :bash:`setup_users`.
The groups have the following capabilities (each group inherits the permissions of the previous):

- :bash:`basic_users`: Can check and start instances.
- :bash:`admin_users`: Can stop instances (SSM capabilities are on the TODO).
- :bash:`setup_users`: Can manage (e.g. create/delete) instances, elastic IP addresses, IAM users, and the AWS account setup.

Note that the :bash:`setup_users` group has the needed permissions to grant access to *all* AWS services.
A malicious IAM user in the :bash:`setup_users` group could activate services that cost tens of thousands of dollars per day or more.
AWS provides support_, but disputing charges is not guaranteed to work.
It is **strongly** recommended to `set a budget`_ (see Costs_).

TL;DR: Don't put users in groups with permissions they don't need.

You can create an IAM user (e.g. named "Bob") under the :bash:`basic_users` IAM group with the script::

    ec2mc user create Bob basic_users

Bob's zipped config "Bob_config.zip" will be created under your config directory.
This file is what you send to Bob.
Instruct Bob on how to install this script, and to unzip the zip file into his home directory (e.g. "C:\\Users\\Bob\\").
Bob will then be able to get the IPs of instances you've created (:bash:`ec2mc servers check`), as well as start them (:bash:`ec2mc servers start`).

Alternatively, you can place Bob under the :bash:`admin_users` group to give him the ability to manage your existing server(s)::

    ec2mc user create Bob admin_users --ssh_key

The :bash:`--ssh_key` argument is used to package the RSA private key file(s) needed for SSH into the created zip.
(Removing the need to worry about SSH keys by using AWS's SSM is on the TODO.)

You can rotate an IAM user's access key (delete the old one and create a new one) with the script::

    ec2mc user rotate_key Bob

Bob's zipped config will be regenerated (you'll need to resend it).
This command provides the :bash:`--ssh_key` argument as well, so you'll need to remember to include it for users who've recieved the SSH key(s) before.

See the `user subcommands`_ for all of the provided commands for managing users.


.. _support: https://console.aws.amazon.com/support/home/?#

.. _set a budget: https://aws.amazon.com/aws-cost-management/aws-budgets/

.. _Costs: https://github.com/TakingItCasual/ec2mc/blob/master/docs/costs.rst

.. _user subcommands: https://github.com/TakingItCasual/ec2mc/blob/master/docs/commands.rst#user-subcommands
