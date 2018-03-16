AWS EC2 instance manager for Minecraft servers
==============================================

|PyPI Version| |Python Version|

Requires a Python version of 3.6.
Can be installed with pip:

.. code-block:: bash

	$ pip install ec2mc

A Python console script for managing Minecraft servers hosted on AWS EC2 instances (cloud computing).
The script is still in alpha, and currently only supports starting and checking instances that already exist.
Commands to start instances and initialize an AWS account are planned.

IAM user credentials must be set before the script can be used:

.. code-block:: bash

	$ ec2mc configure

Sample credentials (with minimal permissions) are the following:

.. code-block:: bash

	AWS access key ID: AKIAJSJIRSCFBLUWRG2Q
	AWS secret access key: N3zwOS1QanjGNgYO3uQ/ObN0Hjh0R3X27UW2abnq

"File path for Minecraft's servers.dat" can be left empty.
The preceding IAM user credentials have been included to facilitate a basic understanding of what the script does.
The instance will turn itself off after 10 minutes of inactivity using crontab.

Full commands to be used are the following ("-r" is the region filter, "-n" is a tag filter):

.. code-block:: bash

	$ ec2mc server check -r eu-central-1 -n chisels-and-bits-1
	$ ec2mc server start -r eu-central-1 -n chisels-and-bits-1

To see how the script updates the Minecraft client's server list, install Minecraft and add the MC client's servers.dat path to the config with "ec2mc configure".
The script can't handle a non-existent/empty server list (yet?), so please add an entry to the Minecraft client's server list before using the script (gibberish is fine, as long as an entry exists).

.. |PyPI Version| image:: https://raw.githubusercontent.com/TakingItCasual/ec2mc/master/docs/images/pypi-v0.1.3-orange.svg?sanitize=true
   :target: https://pypi.org/project/ec2mc/

.. |Python Version| image:: https://raw.githubusercontent.com/TakingItCasual/ec2mc/master/docs/images/python-3.6-blue.svg?sanitize=true
   :target: https://pypi.org/project/ec2mc/
