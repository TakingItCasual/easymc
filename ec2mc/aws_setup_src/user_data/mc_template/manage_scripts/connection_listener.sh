#!/bin/bash

cd /home/ssm-user/manage-scripts/

read MINUTES_NEEDED < minutes_needed.txt
read MINUTES_PASSED < minutes_passed.txt

# Number of established network connections (+1) to server
# TODO: Figure out why SSM keeps established connections going
CONNECTION_COUNT=$(ss -nt state established '( sport = :22 or sport = :25565 or dport = :443 )' | wc -l)

# Increment minute counter if no connections, reset if any connections
if [ "$CONNECTION_COUNT" != "1" ]; then
    MINUTES_PASSED="0"
else
    MINUTES_PASSED=$(($MINUTES_PASSED+1))
fi
echo $MINUTES_PASSED > minutes_passed.txt

#echo $(date +"%D, %T: ")$CONNECTION_COUNT" "$MINUTES_PASSED >> minutes_passed.log

# If minute counter >= number in minutes_needed.txt, initiate shutdown
if [ "$MINUTES_PASSED" -ge "$MINUTES_NEEDED" ]; then
    . ./shutdown_script.sh
fi
