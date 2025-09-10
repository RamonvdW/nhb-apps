#!/bin/bash

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for daily (or faster) execution by a cron job

LOG_DIR="/var/log/www"
SPOOL_DIR="/var/spool/crm"
CONFIG_FILE="download_crm_config.txt"
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
cd "$SCRIPT_DIR" || exit 2

# everything sent to stdout/stderr will be picked up by crontab and sent in an email
# avoid this by writing to a logfile

STAMP=$(date +"%Y%m%d_%H%M%S")
SHORT_STAMP=$(date +"%Y%m%d")       # elke dag een nieuwe logfile
LOG="$LOG_DIR/${SHORT_STAMP}_download_and_import_crm.log"
#echo "Logging to: $LOG"
echo "[INFO] Started at $STAMP" >> "$LOG"

if [ ! -d "$SPOOL_DIR" ]
then
    # cannot create, so report error
    echo "[ERROR] Missing $SPOOL_DIR" >> "$LOG"
    exit 1
fi

# alles ouder dan 60 dagen mag wag
echo "[INFO] Removing old files" >> "$LOG"
find "$SPOOL_DIR" -type f -mtime +60 -exec rm {} + &>> "$LOG"

URL=$(head -1 "$CONFIG_FILE")
SECRET=$(tail -1 "$CONFIG_FILE")

DOWNLOAD=0
echo "[INFO] retrieving headers" >> "$LOG"

# kijk of een download nodig is
PREV_LAST=$(grep --binary-files=text --ignore-case "Last-Modified:" "$LOG" | tail -1)     # empty at start of new day

# download the headers only
# -6 = connect using IPv6 only
# -s = silent
# -S = show errors
# -I = headers only
#                                                 remove DOS newlines
curl -6 -sS -H "secret: $SECRET" -I "$URL" 2>&1 | sed 's#\r##g' >> "$LOG"

# controleer dat bovenstaande HEAD goed werkte
NEW_HTTP=$(grep --binary-files=text -E "HTTP/1.1 |HTTP/2 " "$LOG" | tail -1 | tr '\r' '\n')
if [[ "$NEW_HTTP" != *" 200 OK"* ]]
then
    echo "[ERROR] Failed to download: missing 'HTTP/* 200 OK' in $NEW_HTTP" >> "$LOG"
else
    # haal de nieuwe Last-Modified header op
    NEW_LAST=$(grep --binary-files=text --ignore-case "Last-Modified:" "$LOG" | tail -1)

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
    TMP_FILE="/tmp/crm_${STAMP}.json"

    echo "[INFO] Downloading complete crm data set to $TMP_FILE" >> "$LOG"

    # download
    # -6 = use IPv6
    # -s = silent
    # -S = show errors
    curl -6 -sS -H "secret: $SECRET" "$URL" > "$TMP_FILE" 2>>"$LOG"
    RES=$?
    if [ $RES -ne 0 ]
    then
        echo "[ERROR] Unexpected exit code $RES from curl" >> "$LOG"
        rm -f "$TMP_FILE"
    else
        # move from ImportCRM/cron/ to top-dir
        cd ../..

        # find the previous download
        unset -v OLD_CRM
        for file in "$SPOOL_DIR/crm_"*;
        do
            [[ $file -nt $OLD_CRM ]] && OLD_CRM=$file
        done

        echo "[DEBUG] Previous data set: $OLD_CRM" >> "$LOG"

        # if present, compare the number of changes
        if [ -e "$OLD_CRM" ]
        then
            echo "[INFO] Checking differences with previous import"
            # -u = unbuffered --> needed to maintain the order of stdout and stderr lines
            python3 -u ./manage.py diff_crm_jsons "$OLD_CRM" "$TMP_FILE" &>> "$LOG"
            DIFF_RES=$?
        else
            echo "[WARNING] No previous data set to diff against" >> "$LOG"
            DIFF_RES=0
        fi

        if [ $DIFF_RES -eq 0 ]
        then
            echo "[INFO] Accepted newly downloaded data set"  >> "$LOG"
            SPOOL_FILE="$SPOOL_DIR/crm_${STAMP}.json"
            cat "$TMP_FILE" > "$SPOOL_FILE" 2>> "$LOG"
            rm "$TMP_FILE" 2>> "$LOG"

            echo "[INFO] Importing new data set" >> "$LOG"

            # -u = unbuffered --> needed to maintain the order of stdout and stderr lines
            python3 -u ./manage.py import_crm_json "$SPOOL_FILE" &>> "$LOG"
        else
            echo "[ERROR] Too many differences; blocking automatic import" >> "$LOG"
            # e-mail aan ontwikkelaar wordt gestuurd door diff_crm_jsons.py
        fi
    fi

    echo "[INFO] Import finished" >> "$LOG"
fi

echo "[INFO] Finished" >> "$LOG"

# end of file
