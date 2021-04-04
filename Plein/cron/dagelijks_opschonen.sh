#!/bin/bash

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for execution by a cron job
# precondition: venv must be set

ID=$(id -u)
ID_ROOT=$(id -u root)
ID_WWW=$(id -u apache)
if [ $ID -ne $ID_ROOT -a $ID -ne $ID_WWW ]
then
    echo "Please run with sudo"
    exit 1
fi

cd $(dirname $0)    # ga naar de directory van het script
# move from Plein/cron/ to top-dir
cd ../..

STAMP=$(date +"%Y%m%d_%H%M%S")

# everything sent to stdout/stderr will be picked up by crontab and sent in an email
# avoid this by writing to a logfile
LOGDIR="/var/log/www"
LOG="$LOGDIR/${STAMP}_dagelijks_opschonen.log"

echo "[INFO] Started at $STAMP" >"$LOG"

echo "[INFO] Run: manage clearsessions" >>"$LOG"
./manage.py clearsessions &>>"$LOG"

echo "[INFO] Run: manage database_opschonen" >>"$LOG"
./manage.py database_opschonen &>>"$LOG"

echo "[INFO] Finished" >>"$LOG"

# end of file
