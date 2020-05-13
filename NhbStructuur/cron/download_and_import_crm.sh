#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a crob job

NHBAPPS="/var/www/nhb-apps"
LOGDIR="/var/log/www"
SPOOLDIR="/var/spool/crm"
CONFIGFILE="download_crm_config.txt"

# TODO: cleanup of spool directory

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
SHORTSTAMP=$(date +"%Y%m")       # elke maand een nieuwe logfile
LOG="$LOGDIR/${SHORTSTAMP}_download_and_import_crm.log"
#echo "Logging to: $LOG"
echo "[INFO] Started at $STAMP" >> "$LOG"

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

    # TODO: error handling

    echo "[INFO] Importing new data set" >> "$LOG"

    (cd $NHBAPPS; python3.6 manage.py import_nhb_crm "$SPOOLFILE") &>> "$LOG"

    echo "[INFO] Import finished" >> "$LOG"
fi

echo "[INFO] Finished" >> "$LOG"

# end of file
