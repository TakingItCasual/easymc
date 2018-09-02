#!/bin/bash

cd /home/ec2-user/manage-scripts/

kill -s 15 "$(cat MC_PID.txt)"
rm -rf /home/ec2-user/minecraft/logs/*

sudo shutdown -h now
