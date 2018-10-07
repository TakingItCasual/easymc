#!/bin/bash

# TODO: Learn for sure whether this leaves enough time to save the world
runuser -l ec2-user -c 'screen -XS minecraft quit'
sudo shutdown -h now
