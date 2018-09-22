#!/bin/bash

yum update -y

runuser -l ssm-user -c \
'screen -d -m -S minecraft /home/ssm-user/manage-scripts/start_server.sh'

cd /home/ssm-user/manage-scripts/
echo "10" > minutes_needed.txt
echo "0" > minutes_passed.txt

chmod -R 777 /home/ssm-user/minecraft/
