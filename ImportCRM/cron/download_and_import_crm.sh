#!/bin/bash

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a cron job

LOGDIR="/var/log/www"
SPOOLDIR="/var/spool/crm"
CONFIGFILE="download_crm_config.txt"
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
cd "$SCRIPT_DIR"

# everything sent to stdout/stderr will be picked up by crontab and sent in an email
# avoid this by writing to a logfile

STAMP=$(date +"%Y%m%d_%H%M%S")
SHORTSTAMP=$(date +"%Y%m%d")       # elke dag een nieuwe logfile
LOG="$LOGDIR/${SHORTSTAMP}_download_and_import_crm.log"
#echo "Logging to: $LOG"
echo "[INFO] Started at $STAMP" >> "$LOG"

if [ ! -d "$SPOOLDIR" ]
then
    # cannot create, so report error
    echo "[ERROR] Missing $SPOOLDIR"
    exit 1
fi

# alles ouder dan 60 dagen mag wag
echo "[INFO] Removing old files" >> "$LOG"
find "$SPOOLDIR" -type f -mtime +60 -exec rm {} + &>> "$LOG"

URL=$(head -1 "$CONFIGFILE")
SECRET=$(tail -1 "$CONFIGFILE")

DOWNLOAD=0
echo "[INFO] retrieving headers" >> "$LOG"

# kijk of een download nodig is
PREV_LAST=$(grep "Last-Modified:" "$LOG" | tail -1)     # empty at start of new month

# download the headers only
curl -sS -H "secret: $SECRET" -I "$URL" &>> "$LOG"

# controleer dat bovenstaande HEAD goed werkte
NEW_HTTP=$(grep "HTTP/1.1 " "$LOG" | tail -1 | tr '\r' '\n')
if [ ! "$NEW_HTTP" == "HTTP/1.1 200 OK" ]
then
    echo "[ERROR] Failed to download: $NEW_HTTP" >> "$LOG"
else
    # haal de nieuwe Last-Modified header op
    NEW_LAST=$(grep "Last-Modified:" "$LOG" | tail -1)

    if [ "$PREV_LAST" != "$NEW_LAST" ]
    then
        echo "[INFO] Detected need for full download" >> "$LOG"
        DOWNLOAD=1
    else
        echo "[INFO] No need to download the crm data set" >> "$LOG"
    fi
fi

if [ $DOWNLOAD -eq 1 ]
then
    SPOOLFILE="$SPOOLDIR/crm_${STAMP}.json"
    echo "[INFO] Downloading complete crm data set to $SPOOLFILE" >> "$LOG"

    # download
    curl -sS -H "secret: $SECRET" "$URL" > "$SPOOLFILE" 2>>"$LOG"
    RES=$?
    if [ $RES -ne 0 ]
    then
        echo "[ERROR] Unexpected exit code $RES from curl" >> "$LOG"
    else
        echo "[INFO] Importing new data set" >> "$LOG"

        # move from ImportCRM/cron/ to top-dir
        cd ../..

        # -u = unbuffered --> needed to maintain the order of stdout and stderr lines
        python3 -u ./manage.py import_crm_json "$SPOOLFILE" &>> "$LOG"
    fi

    echo "[INFO] Import finished" >> "$LOG"
fi

echo "[INFO] Finished" >> "$LOG"

# end of file
