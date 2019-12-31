#!/bin/bash

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a crob job

NHBAPPS="/var/www/nhb-apps"
LOGDIR="/var/log/www"
SPOOLDIR="/var/spool/records"
TMPDIR="/tmp/downloader"
RECORDS="/tmp/downloader/records.json"      # note: download_gsheet.py contains the same path

ID=$(id -u)
if [ $ID -ne 0 ]
then
    echo "Please run with sudo"
    exit 1
fi

STAMP=$(date +"%Y%m%d_%H%M%S")
LOG="$LOGDIR/${STAMP}_download_and_import_records.log"
echo "Logging to: $LOG"
echo "[INFO] Started" > "$LOG"

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
python3.6 ./download_gsheet.py &>> "$LOG"

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

        # import the records
        echo "[INFO] Importing records" >> "$LOG"
        (cd $NHBAPPS; python3.6 manage.py import_records "$SPOOLFILE") &>> "$LOG"
    else
        echo "[INFO] Records have not changed" >> "$LOG"
    fi

    # clean up
    echo "[INFO] Cleaning up" >> "$LOG"
    rm -rf "$TMPDIR" &>> "$LOG"
else
    echo "[ERROR] Download failed: cannot locate $RECORDS" >> "$LOG"
fi

echo "[INFO] Finished" >> "$LOG"

# end of file
