Costs
=====

.. role:: bash(code)
   :language: bash

For your first year using AWS, you won't be billed for the usage of some basic AWS services due to `AWS's Free Tier`_.
How this applies to you will be explained below.
There are four AWS services that you will be billed for using (three related to the instances themselves).
Note that a Value Added Tax (VAT) is added on top of your other costs.

Note that if you plan to use a server for more than a few hours a day, it's cheaper to just use `Minecraft Realms`_, or any of the numerous hosting services that will host old/modded versions of Minecraft for you.

If costs run higher than expected, AWS provides support_ where you can attempt to dispute them.
It is **strongly** recommended to `set a budget`_ to alert you when your costs go over a set limit (the spending itself cannot be limited).

Instance Running Costs
--------------------------------

You are only billed for each hour that an on-demand instance runs.
However, you are billed seperately for an instance's storage and networking (see below).

The two provided instance templates (:bash:`mc_template` and :bash:`cnb_template`) are configured to create an on-demand instance of the type :bash:`t2.small`.
This instance type can cost between $0.02 and $0.03 an hour, depending on which AWS region the instance is located in.

If you think in terms of how many hours a day the server will be running over the course of a month, it's between $0.60 and $0.90 for each hour.
If the server runs 24/7, this works out to $14.40-$21.60 a month.

For details on instance type capabilities and costs, and how prices vary between regions, see the following URL:

https://aws.amazon.com/ec2/pricing/on-demand/

Instance Storage Costs
----------------------

Billing is based on how much storage space is allocated, rather than how much storage space is actually used.
Allocating 50GB while only using 10GB will still result in you being billed for 50GB.

General purpose SSD (gp2) volumes (the storage) can cost between $0.10 and $0.12 per GB per month, depending on which AWS region the volume is located in.
The two provided instance templates are configured to allocate 8GB for an instance.
This amount of storage costs $0.80-$0.96 a month.

Due to `AWS's Free Tier`_, you can allocate 30GB (enough for 3 instances) for free during your first year.

For details on how storage prices vary between regions, see the following URL ("gp2" is the relevant volume type):

https://aws.amazon.com/ebs/pricing/

Instance Networking Costs
-------------------------

Billing is based on the amount of data transferred out from instances.
Data transferred into instances (e.g. an instance downloading files, or receiving player commands) is free.

It can cost between $0.09 to $0.12 per GB transferred out, depending on which AWS region the instance is located in.

Mincraft server bandwidth `is estimated`_ to be around 0.1GB per hour per player.
For each hour your server is running a day, that's 3GB ($0.27-$0.36) per month per player.

Due to `AWS's Free Tier`_, you can transfer out 15GB a month for free during your first year.
This should be sufficient for 1 player playing 5 hours a day, 5 players playing 1 hour a day, etc.
Essentially, it's a discount of $4.05-$5.40 a month.

For details on how prices vary between regions, see the following URL:

https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer

Elastic IP Address Costs
------------------------

Elastic IP addresses are free when attached to a running instance.
Otherwise, you are billed $0.005 an hour for each address (in all AWS regions).
This means you will be billed for your addresses whenever your servers aren't running.

`More specifically`_, you are not billed for an address if all of the following conditions are met:

- The elastic IP address is associated with an EC2 instance.
- The instance associated with the elastic IP address is running.
- The instance has only one elastic IP address attached to it.

If an address is left unused, the cost works out to $0.15 for each hour a day, or $3.6 for a whole month.

Summary
-------

Your monthly bill is based on how many hours a day (on average) your instances are running, whether you're covered by `AWS's Free Tier`_, whether instances have elastic IP addresses (EIP), and how many players are on your servers (on average) when they're running.

The following table shows the expected monthly bill for a :bash:`t2.small` instance.
To get the total expected cost of a server, multiply "Cost per player" by the number of expected players, and add it to the relevant cost on the left. 
When your free tier benefits expire, you will no longer recieve the $4.05-$5.40 networking discount, and you'll be billed an additional $0.80-$0.96 for the 8GB of storage.

====== ============= ============= ===============
Uptime Instance running costs      Networking
------ --------------------------- ---------------
hr/day No EIP        Has EIP       Cost per player
====== ============= ============= ===============
1      $0.60-$0.90   $4.05-$4.35   $0.27-$0.36
2      $1.20-$1.80   $4.50-$5.10   $0.54-$0.72
3      $1.60-$2.70   $4.95-$5.85   $0.81-$1.08
4      $2.40-$3.60   $5.40-$6.60   $1.08-$1.44
6      $3.60-$5.40   $6.30-$8.10   $1.62-$2.16
9      $5.40-$8.10   $7.65-$10.35  $2.43-$3.24
12     $7.20-$10.80  $9.00-$12.60  $3.24-$4.32
18     $10.80-$16.20 $11.70-$17.10 $4.86-$6.48
24     $14.40-$21.60 $14.40-$21.60 $6.48-$8.64
====== ============= ============= ===============


.. _AWS's Free Tier: https://aws.amazon.com/free/#AWS_Free_Tier_(12_Month_Introductory_Period):

.. _Minecraft Realms: https://minecraft.net/en-us/realms/

.. _support: https://console.aws.amazon.com/support/home/?#

.. _set a budget: https://aws.amazon.com/aws-cost-management/aws-budgets/

.. _is estimated: https://gaming.stackexchange.com/a/22160

.. _More specifically: https://aws.amazon.com/premiumsupport/knowledge-center/elastic-ip-charges/#Resolution
