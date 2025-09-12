#!/bin/bash

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a cron job

LOG_DIR="/var/log/www"
SPOOL_DIR="/var/spool/records"
TMP_DIR="/tmp/downloader_records"
JSON="$TMP_DIR/records.json"      # note: download_gsheet.py contains the same path
USER_WWW="$1"

if [ $# -ne 1 ]
then
    echo "Provide one argument: username (for example www-data)"
    exit 1
fi

ID=$(id -u)
ID_WWW=$(id -u "$USER_WWW")
if [ "$ID" -ne "$ID_WWW" ]
then
    echo "Please run with sudo -u $USER_WWW"
    exit 1
fi

# everything sent to stdout/stderr will be picked up by crontab and sent in an email
# avoid this by writing to a logfile

SHORT_STAMP=$(date +"%Y%m%d")       # elke dag een nieuwe logfile
LOG="$LOG_DIR/${SHORT_STAMP}_download_and_import_records.log"
#echo "Logging to: $LOG"

STAMP=$(date +"%Y%m%d_%H%M%S")
echo "" >> "$LOG"
echo "[INFO] Started at $STAMP" >> "$LOG"

if [ ! -d "$SPOOL_DIR" ]
then
    # cannot create, so report error
    echo "[ERROR] Missing $SPOOL_DIR" >> "$LOG"
    exit 1
fi

# prepare to download
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

# calculate the checksum for the latest downloaded file
LATEST_FILE=$(find "$SPOOL_DIR" -name 'records_*json' | sort | tail -1)
LATEST_HASH="none"
if [ -e "$LATEST_FILE" ]
then
    echo "[INFO] Latest records file is $LATEST_FILE" >> "$LOG"
    LATEST_HASH=$(sha1sum < "$LATEST_FILE")
    echo "[INFO] Hash van vorige download: $LATEST_HASH" >> "$LOG"
fi

# move from Records/cron/ to top-dir
cd ../..

# download het bestand en opslaan als JSON
./manage.py download_records "$JSON" &>> "$LOG"

# import or barf
if [ -e "$JSON" ]
then
    echo "[INFO] Download is gelukt" >> "$LOG"

    # calculate the hash so we can detect if it has not changed
    HASH=$(sha1sum < "$JSON")
    echo "[INFO] Hash van nieuwe download: $HASH" >> "$LOG"

    if [ "$HASH" != "$LATEST_HASH" ]
    then
        # file has changed, so store and import

        SPOOL_FILE="$SPOOL_DIR/records_$STAMP.json"
        echo "[INFO] Storing records file in $SPOOL_FILE" >> "$LOG"
        cp "$JSON" "$SPOOL_FILE"

        # import the records
        echo "[INFO] Importing records" >> "$LOG"
        ./manage.py import_records "$SPOOL_FILE" &>> "$LOG"

        echo "[INFO] Bepaal beste records" >> "$LOG"
        ./manage.py bepaal_beste_records &>> "$LOG"
    else
        echo "[INFO] Records zijn ongewijzigd" >> "$LOG"
    fi

    # clean up
    echo "[INFO] Cleaning up" >> "$LOG"
    rm -rf "$TMP_DIR" &>> "$LOG"
else
    echo "[ERROR] Download is niet gelukt (kan bestand $JSON niet vinden)" >> "$LOG"
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
echo "[INFO] Finished at $STAMP" >> "$LOG"

# end of file
