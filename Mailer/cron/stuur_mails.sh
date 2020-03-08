#!/bin/bash

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for regular execution by a crob job, typically at 15 minute intervals
# the invoked command will run for the given amount of minutes and then quits

NHBAPPS="/var/www/nhb-apps"
LOGDIR="/var/log/www"
RUN_DURATION=$1
DEPLOY_FLAG="/tmp/running_deploy"

ID=$(id -u)
ID_ROOT=$(id -u root)
ID_WWW=$(id -u apache)
if [ $ID -ne $ID_ROOT -a $ID -ne $ID_WWW ]
then
    echo "Please run with sudo"
    exit 1
fi

# everything sent to stdout/stderr will be picked up by crontab and sent in an email
# avoid this by writing to a logfile

STAMP=$(date +"%Y%m%d_%H%M%S")
SHORTSTAMP=$(date +"%Y%m%d")       # elke dag een nieuwe logfile
LOG="$LOGDIR/${SHORTSTAMP}_stuur_mails.log"
#echo "Logging to: $LOG"
echo "[INFO] Started at $STAMP" >> "$LOG"

if [ -e "$DEPLOY_FLAG" ]
then
    echo "[WARNING] Skipping because of $DEPLOY_FLAG" >> "$LOG"
else
    echo "[INFO] Run duration is $RUN_DURATION" >> "$LOG"
    (cd $NHBAPPS; python3.6 manage.py stuur_mails $RUN_DURATION) &>> "$LOG"
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
echo "[INFO] Finished at $STAMP" >> "$LOG"

# end of file
