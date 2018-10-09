Costs
=====

.. role:: bash(code)
   :language: bash

For your first year using AWS, you won't be billed for the usage of some basic AWS services due to `AWS's Free Tier`_.
How this applies to you will be explained below.
There are four AWS services that you will be billed for using (three related to the instances themselves).
Note that a Value Added Tax (VAT) is added on top of your other costs.

Note that if you plan to use a server for more than a few hours a day, it's cheaper to just use `Minecraft Realms`_, or any of the numerous hosting services that will host old/modded versions of Minecraft for you.

If costs run higher than expected, AWS provides support_, but disputing charges is not guaranteed to work.
It is **strongly** recommended to `set a budget`_ to alert you when your costs go over a set limit (the spending itself cannot be limited).

On-Demand Instance Running Costs
--------------------------------

You are only billed for each hour that an on-demand instance runs.
However, you are billed seperately for an instance's storage and networking (see below).

The two provided instance templates (:bash:`mc_template` and :bash:`cnb_template`) are configured to create an on-demand instance of the type :bash:`t2.small`.
This instance type can cost between $0.02 and $0.03 an hour, depending on which AWS region the instance is located in.

If you think in terms of how many hours a day the server will be running over the course of a month, it's between $0.6 and $0.9 for each hour.
If the server runs 24/7, this works out to around $15-$22 a month.

For details on instance type capabilities and costs, and how prices vary between regions, see the following URL:

https://aws.amazon.com/ec2/pricing/on-demand/

Instance Storage Costs
----------------------

Billing is based on how much storage space is allocated, rather than how much storage space is actually used.
Allocating 50GB while only using 10GB will still result in you being billed for 50GB.

The two provided instance templates (:bash:`mc_template` and :bash:`cnb_template`) are configured to allocate 8GB for an instance.
This amount of storage can cost between $0.8 and $1 a month, depending on which AWS region the instance is located in.

Due to `AWS's Free Tier`_, you can allocate 30GB (enough for 3 instances) for free during your first year.

For details on how storage prices vary between regions, see the following URL ("gp2" is the relevant volume type):

https://aws.amazon.com/ebs/pricing/

Instance Networking Costs
-------------------------

Billing is based on the amount of data transferred out from instances.
Data transferred into instances (e.g. an instance downloading files, or receiving player commands) is free.

It can cost between $0.09 to $0.12 per GB transferred out, depending on which AWS region the instance is located in.

Mincraft server bandwidth `is estimated`_ to be around 0.1GB per hour per player.
For each hour your server is running a day, that's 3GB ($0.3-$0.4) per month per player.

Due to `AWS's Free Tier`_, you can transfer out 15GB a month for free during your first year.
This should be sufficient for 1 player playing 5 hours a day, 5 players playing 1 hour a day, etc.

For details on how prices vary between regions, see the following URL:

https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer

Elastic IP address costs
------------------------

(WIP)

Elastic IP addresses, by themselves, cost $0.005 an hour in all AWS regions.

If a single address is associated with a running instance, it's free, otherwise it costs the usual amount.

Summary
-------

(WIP)


.. _AWS's Free Tier: https://aws.amazon.com/free/#AWS_Free_Tier_(12_Month_Introductory_Period):

.. _Minecraft Realms: https://minecraft.net/en-us/realms/

.. _support: https://console.aws.amazon.com/support/home/?#

.. _set a budget: https://aws.amazon.com/aws-cost-management/aws-budgets/

.. _is estimated: https://gaming.stackexchange.com/a/22160
