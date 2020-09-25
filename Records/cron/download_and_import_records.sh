#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a crob job

LOGDIR="/var/log/www"
SPOOLDIR="/var/spool/records"
TMPDIR="/tmp/downloader"
RECORDS="/tmp/downloader/records.json"      # note: download_gsheet.py contains the same path

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

SHORTSTAMP=$(date +"%Y%m%d")       # elke dag een nieuwe logfile
LOG="$LOGDIR/${SHORTSTAMP}_download_and_import_records.log"
#echo "Logging to: $LOG"

STAMP=$(date +"%Y%m%d_%H%M%S")
echo "" >> "$LOG"
echo "[INFO] Started at $STAMP" >> "$LOG"

# prepare to download
rm -rf "$TMPDIR"
mkdir -p "$TMPDIR"
cp "./downloader_service-account.json" "$TMPDIR/service-account.json"

# calculate the checksum for the latest downloaded file
LATESTFILE=$(ls -1t "$SPOOLDIR"/records_*.json | head -1)
LATESTHASH="none"
if [ -e "$LATESTFILE" ]
then
    LATESTHASH=$(sha1sum < "$LATESTFILE")
    echo "[INFO] Hash of previously downloaded records: $LATESTHASH" >> "$LOG"
fi

# download the records
echo "[INFO] Starting download" >> "$LOG"
python ./download_gsheet.py &>> "$LOG"

# import or barf
if [ -e "$RECORDS" ]
then
    echo "[INFO] Download successful" >> "$LOG"

    # calculate the hash so we can detect if it has not changed
    HASH=$(sha1sum < "$RECORDS")
    echo "[INFO] Hash of newly downloaded records: $HASH" >> "$LOG"

    if [ "$HASH" != "$LATESTHASH" ]
    then
        # file has changed, so store and import!

        SPOOLFILE="$SPOOLDIR/records_$STAMP.json"
        echo "[INFO] Storing records file in $SPOOLFILE" >> "$LOG"
        cp "$RECORDS" "$SPOOLFILE"

        # move from Records/cron/ to top-dir
        #echo "[DEBUG] pwd=$PWD"
        cd ../..
        #echo "[DEBUG] pwd=$PWD"

        # import the records
        echo "[INFO] Importing records" >> "$LOG"
        ./manage.py import_records "$SPOOLFILE" &>> "$LOG"

        echo "[INFO] Decide best records" >> "$LOG"
        ./manage.py bepaal_beste_records &>> "$LOG"
    else
        echo "[INFO] Records have not changed" >> "$LOG"
    fi

    # clean up
    echo "[INFO] Cleaning up" >> "$LOG"
    rm -rf "$TMPDIR" &>> "$LOG"
else
    echo "[ERROR] Download failed: cannot locate $RECORDS" >> "$LOG"
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
echo "[INFO] Finished at $STAMP" >> "$LOG"

# end of file
