#!/bin/bash

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a crob job

NHBAPPS="/var/www/nhb-apps"
LOGDIR="/var/log/www"
TMPDIR="/tmp/downloader"

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

RECORDS="$TMPDIR/records.json"      # note: download_gsheet.py contains the same path

# prepare to download
rm -rf "$TMPDIR"
mkdir -p "$TMPDIR"
cp "./downloader_service-account.json" "$TMPDIR/service-account.json"

# download the records
echo "[INFO] Starting download"
python3.6 ./download_gsheet.py &>> "$LOG"

# import or barf
if [ -e "$RECORDS" ]
then
    echo "[INFO] Download successful" >> "$LOG"

    # import the records
    echo "[INFO] Importing records" >> "$LOG"
    (cd $NHBAPPS; python3.6 manage.py import_records /tmp/downloader/records.json &>> "$LOG")

    # clean up
    echo "[INFO] Cleaning up"
    rm -rf "$TMPDIR" &>> "$LOG"
else
    echo "[ERROR] Download failed: cannot locate $RECORDS" >> "$LOG"
fi

echo "[INFO] Finished" >> "$LOG"

# end of file
