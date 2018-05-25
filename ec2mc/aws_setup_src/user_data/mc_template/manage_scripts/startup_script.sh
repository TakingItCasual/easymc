#!/bin/bash

cd $HOME/manage-scripts

screen -d -m -S minecraft $HOME/manage-scripts/start_server.sh

echo "10" > minutes_needed.txt
echo "0" > minutes_passed.txt
