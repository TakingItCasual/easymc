#!/bin/bash

# TODO: Learn for sure whether this leaves enough time to save the world
runuser -l ssm-user -c 'screen -XS minecraft quit'
#rm -rf /home/ssm-user/minecraft/logs/*

sudo shutdown -h now
