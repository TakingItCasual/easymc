#!/bin/bash

cd /home/ec2-user/manage-scripts/

read MINUTES_NEEDED < minutes_needed.txt
read MINUTES_PASSED < minutes_passed.txt

CONNECTION_COUNT=$(/usr/sbin/ss -nt state established '( sport = :22 or sport = :25565 )' | wc -l)

if [ "$CONNECTION_COUNT" != "1" ]; then
    MINUTES_PASSED="0"
else
    MINUTES_PASSED=$(($MINUTES_PASSED+1))
fi
echo $MINUTES_PASSED > minutes_passed.txt

#echo $(date +"%D, %T: ")$CONNECTION_COUNT" "$MINUTES_PASSED >> minutes_passed.log

if [ "$MINUTES_PASSED" -ge "$MINUTES_NEEDED" ]; then
    . ./shutdown_script.sh
fi
