#!/bin/bash

screen -d -m -S minecraft /home/ec2-user/manage-scripts/start_server.sh

cd /home/ec2-user/manage-scripts/
echo "10" > minutes_needed.txt
echo "0" > minutes_passed.txt
