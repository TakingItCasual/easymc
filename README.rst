AWS EC2 instance manager for Minecraft servers
==============================================

(Not yet uploaded to PyPi, pls ignore.)

Requires a Python version of 3.6. Can be installed with pip:

.. code-block:: bash

	$ python -m pip install easymc

A Python console script for managing Minecraft servers hosted on AWS EC2 instances. Currently the script can only start and check the status of instances, but it is coded with simple expansion as a goal. There was an attempt at validation and documentation.

Credentials for an IAM user with minimal permissions have been included to provide a basic understanding of what the script is doing. The instance turns itself off after 10 minutes, so feel free to start it.

Full commands to be used are the following:

.. code-block:: bash

	$ easymc check_server [eu-central-1] unique-desc [chisels-and-bits-1]
	$ easymc start_server [eu-central-1] unique-desc [chisels-and-bits-1]

If you want to see the validation at work, run the commands adding the arguments after main.py one at a time.

To see how the script updates the Minecraft client's server list, install Minecraft and set the client's servers.dat with "easymc configure". The script can't handle a non-existent/empty server list (yet?), so please add an entry to the Minecraft client's server list before using the script (gibberish is fine, as long as an entry exists).
