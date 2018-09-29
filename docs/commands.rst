Commands
========

.. role:: bash(code)
   :language: bash

Python's argparse is used to manage the commands and their arguments, so you can append :bash:`-h` or :bash:`--help` to any command to display a summary of the command's arguments.

:bash:`configure` subcommands
-----------------------------

:bash:`configure access_key`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the script's default IAM user access key.
Takes two arguments: The access key's ID and secret.
The script can then use the specified access key to interact with AWS.
If an access key was already set, it will be overwritten.

:bash:`configure whitelist`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set what AWS region(s) the script will interact with (e.g. to create instances in).
Takes zero or more arguments.
Each argument should be from the :bash:`Code` column of the `AWS Regions`_ table.
If no arguments are given, the whitelist is cleared (the script will re-estimate the closest region to you when next used).

WARNING: You should decide upon the whitelist before uploading the AWS setup.
The AWS setup will need to be reuploaded if new regions are added to the whitelist.
Removing regions from the whitelist will only hide the AWS setup, instances, elastic IP addresses, etc. located in the removed regions.
Updates to your region whitelist are not propagated to users you've distributed IAM user access keys to.

:bash:`configure use_handler`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure the script to use the IP handler specified by an instance's IpHandler tag.
For example, the mc_handler.py handler updates the local Minecraft client server list with the IP of the instance.
If you want to disable the usage of handlers (e.g. if you don't have Minecraft installed), append the :bash:`--false` argument.

:bash:`aws_setup` subcommands
-----------------------------

:bash:`aws_setup check`
~~~~~~~~~~~~~~~~~~~~~~~

Report whether your AWS account has been configured, and whether the configuration needs to be updated.

:bash:`aws_setup upload`
~~~~~~~~~~~~~~~~~~~~~~~~

Configure your AWS account with the configuration described under the script's config directory's aws_setup directory (~/.ec2mc/aws_setup/).
If your AWS account is already configured and changes have been made to aws_setup, this command will update your AWS account's configuration.

:bash:`aws_setup delete`
~~~~~~~~~~~~~~~~~~~~~~~~

Delete your AWS account's configuration.
This command will not run if there are still any IAM users or EC2 instances left.

:bash:`server` subcommands
--------------------------

:bash:`server create`
~~~~~~~~~~~~~~~~~~~~~

Create a new EC2 instance.
Requires two arguments: A name for the instance, and what template to use.
The command must be confirmed with the :bash:`--confirm` argument (it is recommended to first run the command without confirmation to check if there are any issues).
If the AWS region whitelist has more than one entry, a region must be specified with the :bash:`-r` argument.
Additional tags can be attached to the instance with the :bash:`-t` argument.
The :bash:`--elastic_ip` argument will create a new elastic IP address and attach to the instance.
The :bash:`--use_ip` argument will attach an elastic IP address (that you already possess) to the instance (if the address is in use, the :bash:`--force` argument must be used).

:bash:`server delete`
~~~~~~~~~~~~~~~~~~~~~

Terminate an EC2 instance.
Requires two arguments: The ID and name of the instance.
If the AWS region whitelist has more than one entry, the instance's region must be specified with the :bash:`-r` argument.
By default, this command will release any elastic IP addresses associated with the instance.
To preserve the instance's address(es), use the :bash:`--save_ips` argument.
Note that this command does not require confirmation, unlike :bash:`server create`.
I consider needing to specify both the instance's ID and name as confirmation enough.

:bash:`server ssh`
~~~~~~~~~~~~~~~~~~

SSH into a running instance.
If you have more than one instance, you'll have to set a filter (this command has the same filtering options as :bash:`servers check`).
To use this command, you must have either OpenSSH_ or PuTTY_ installed (Windows 10 has OpenSSH natively, but it must be enabled).
If you use PuTTY, you'll need to convert your .pem RSA private key (in the script's config directory) to .ppk `using PuTTYgen`_.

:bash:`servers` subcommands
---------------------------

:bash:`servers check`
~~~~~~~~~~~~~~~~~~~~~

Check what instances belong to your AWS account, what region each belongs to, and what tags each has.
If an instance is running, its IP address is reported.
If you haven't disabled IP handlers, a running instance's IP is handled via the designated IP handler.
(The default mc_handler.py IP handler updates the local Minecraft client server list with the IP of the instance.)

Four different instance filtering methods are provided:

- The :bash:`-n` argument will filter instances by the specified name(s).
- The :bash:`-r` argument will filter instances by the specified AWS region(s).
- The :bash:`-t` argument will filter instances by the specified tag value(s) (first parameter is the tag key).
- The :bash:`-i` argument will filter instances by the specified ID(s).

:bash:`servers start`
~~~~~~~~~~~~~~~~~~~~~

Start currently stopped instances.
Once running, an instace's IP address is reported.
If an instance doesn't have an elastic IP address, it will start with a different IP address from the last time it was running.
If you haven't disabled IP handlers, the instance's IP is handled via the designated IP handler.
This command has the same filtering options as :bash:`servers check`.

:bash:`servers stop`
~~~~~~~~~~~~~~~~~~~~

Stop instances.
If an instance doesn't have an elastic IP address, when it is started again it will have a different IP address.
This command has the same filtering options as :bash:`servers check`.

:bash:`address` subcommands
---------------------------

:bash:`address list`
~~~~~~~~~~~~~~~~~~~~

List possessed elastic IP addresses, what region each belongs to, and what instance each is associated with (if any).

:bash:`address request`
~~~~~~~~~~~~~~~~~~~~~~~

Allocate an elastic IP address from AWS.
If an IP is not specified, a random address is allocated.
If an IP is specified (e.g. to recover a mistakenly released address), the IP is requested, which may or may not succeed.
If the AWS region whitelist has more than one entry, a region must be specified with the :bash:`-r` argument.

:bash:`address associate`
~~~~~~~~~~~~~~~~~~~~~~~~~

Associate an elastic IP address with an instance.
Requires 2 arguments: The IP of the address, and the name of the instance.
If the address is in use, the :bash:`--force` argument must be used.

:bash:`address disassociate`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Disassociate an elastic IP address from its instance.
Takes one argument: The IP of the address.

:bash:`address release`
~~~~~~~~~~~~~~~~~~~~~~~

Release an elastic IP address (give the address back to AWS).
Requires one argument: The ip of the address.
If the address is in use, the :bash:`--force` argument must be used.

:bash:`user` subcommands
------------------------

:bash:`user list`
~~~~~~~~~~~~~~~~~

List the IAM groups and what IAM users belong to each.

:bash:`user be`
~~~~~~~~~~~~~~~

Set another IAM user's access key as the script's default access key.
Takes one argument: The name of the desired IAM user.
As it is not possible to request existing access keys from AWS, this works by the script storing access keys generated from the :bash:`user create` and :bash:`user rotate_key` commands in your config.
The stored access keys are gone over in an attempt to find one belonging to the desired IAM user.

:bash:`user create`
~~~~~~~~~~~~~~~~~~~

Create a new IAM user.
Requires two arguments: A name for the user, and the IAM group to add the user to.
If you want to set the new user's access key as the script's default, use the :bash:`--default` argument.
Otherwise, the script will create a .zip file of the new user's config directory.
If you want to add the RSA private key needed for SSH to the .zip, use the :bash:`--ssh_key` argument.

:bash:`user set_group`
~~~~~~~~~~~~~~~~~~~~~~

Set what IAM group an IAM user belongs to.
Requires two arguments: The name of the user, and the name of the group to add the user to.
The user is removed from any groups it belonged to before.

:bash:`user rotate_key`
~~~~~~~~~~~~~~~~~~~~~~~

Delete an IAM user's existing access key(s) and create a new access key for the user.
Requires one argument: The name of the user.
If rotating an access key for a user other than yourself, the user's zipped config directory is (re)generated.
If you want to add the RSA private key needed for SSH to the .zip, use the :bash:`--ssh_key` argument.

:bash:`user delete`
~~~~~~~~~~~~~~~~~~~

Delete an IAM user.
Requires one argument: The name of the user.


.. _AWS Regions: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions

.. _OpenSSH: http://www.mls-software.com/opensshd.html

.. _PuTTY: https://www.putty.org/

.. _using PuTTYgen: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html#putty-private-key
