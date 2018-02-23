AWS EC2 instance manager for Minecraft servers
==============================================

Requires a Python version of 3.6. Can be installed with pip:

.. code-block:: bash

	$ python -m pip install ec2mc

A Python console script for managing Minecraft servers hosted on AWS EC2 instances.
Currently the script can only start and check the status of instances, but it is coded with simple expansion as a goal.
There was an attempt at validation and documentation.

IAM user credentials must be set before the script can be used:

.. code-block:: bash

	$ ec2mc configure

Sample credentials (with minimal permissions) are the following:

.. code-block:: bash

	AWS access key ID: AKIAJSJIRSCFBLUWRG2Q
	AWS secret access key: N3zwOS1QanjGNgYO3uQ/ObN0Hjh0R3X27UW2abnq

"File path for Minecraft's servers.dat" can be left empty.
The previous IAM user credentials have been included to facilitate a basic understanding of what the script is doing.
The instance turns itself off after 10 minutes, so feel free to start it.

Full commands to be used are the following:

.. code-block:: bash

	$ ec2mc check_server -r eu-central-1 -t Name chisels-and-bits-1
	$ ec2mc start_server -r eu-central-1 -t Name chisels-and-bits-1

To see how the script updates the Minecraft client's server list, install Minecraft and add the MC client's servers.dat path to the config with "ec2mc configure".
The script can't handle a non-existent/empty server list (yet?), so please add an entry to the Minecraft client's server list before using the script (gibberish is fine, as long as an entry exists).
