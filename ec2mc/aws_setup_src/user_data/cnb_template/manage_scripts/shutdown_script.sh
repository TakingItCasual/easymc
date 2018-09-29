#!/bin/bash

runuser -l ec2-user -c 'screen -XS minecraft quit'
sudo shutdown -h now
