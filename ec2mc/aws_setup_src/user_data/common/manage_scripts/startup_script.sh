#!/bin/bash

yum update -y

runuser -l ec2-user -c \
'screen -d -m -S minecraft /home/ec2-user/manage-scripts/start_server.sh'

cd /home/ec2-user/manage-scripts/
echo "10" > minutes_needed.txt
echo "0" > minutes_passed.txt

chown -R ec2-user:ec2-user /home/ec2-user/minecraft/
