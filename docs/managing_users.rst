Managing Users
==============

.. role:: bash(code)
   :language: bash

The script, by default, provides three IAM groups to place IAM users in: :bash:`basic_users`, :bash:`admin_users`, and :bash:`setup_users`. The groups have the following capabilities (each group inherits the permissions of the previous):

- :bash:`basic_users`: Can check and start instances.
- :bash:`admin_users`: Can stop instances (SSM capabilities are on the TODO).
- :bash:`setup_users`: Can manage (e.g. create/delete) instances, elastic IP addresses, IAM users, and the AWS account setup.

Note that the :bash:`setup_users` group has the needed permissions to grant access to *all* AWS services.
A malicious IAM user in the :bash:`setup_users` group could activate services that cost tens of thousands of dollars per day or more.
AWS provides support_, but disputing charges is not guaranteed to work.
It is **strongly** recommended to `set a billing alarm`_.

TL;DR: Don't put users in groups with permissions they don't need.

You can create an IAM user (e.g. named "Bob") under the :bash:`basic_users` IAM group with the script::

    ec2mc user create Bob basic_users

Or under the :bash:`admin_users` group, if you want Bob to be able to manage your server(s)::

    ec2mc user create Bob admin_users --ssh_key

The :bash:`--ssh_key` argument is needed to package the RSA private key file(s) needed for SSH into the created zip.
SSM is an alternative to SSH that removes the need to worry about SSH keys, but this script does not (yet?) offer support for it.

Once the IAM user "Bob" is created, "Bob_config.zip" is created in the script's config directory.
This file is what you send to Bob.
Instruct Bob on how to install this script, and to unzip the file into his home directory (e.g. "C:\\Users\\Bob\\").

You can rotate an IAM user's access key (delete the old one and create a new one) with the script::

    ec2mc user rotate_key Bob

Their zipped config is regenerated (you'll need to resend it).
This can also be used to add the SSH key(s) to the zipped config if they were mistakenly left out before.

See the `user subcommands`_ for all of the provided commands for managing users.


.. _support: https://console.aws.amazon.com/support/home/?#

.. _set a billing alarm: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html

.. _user subcommands: https://github.com/TakingItCasual/ec2mc/blob/master/docs/commands.rst#user-subcommands