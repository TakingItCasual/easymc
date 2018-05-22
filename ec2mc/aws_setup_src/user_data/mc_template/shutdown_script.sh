#!/bin/bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

kill -s 15 "$(cat MC_PID.txt)"
rm -rf ~/logs/*

sudo shutdown -h now
