#!/bin/bash

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for execution by a cron job
# precondition: venv must be set

USER_WWW="$1"

ID=$(id -u)
ID_ROOT=$(id -u root)
ID_WWW=$(id -u "$USER_WWW")
if [ "$ID" -ne "$ID_ROOT" ] && [ "$ID" -ne "$ID_WWW" ]
then
    echo "Please run with sudo"
    exit 1
fi

# ga naar de directory waar het script staat
SCRIPT_DIR=$(realpath "$0")             # volg links naar het echte script
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")     # directory van het script
cd "$SCRIPT_DIR" || exit 1

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
