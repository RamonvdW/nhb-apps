#!/bin/bash

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

URL_SERVER="https://fonts.googleapis.com"

URL_OPEN_SANS_REGULAR="$URL_SERVER/css2?family=Open+Sans:wght@400&display=swap"
URL_OPEN_SANS_SEMIBOLD="$URL_SERVER/css2?family=Open+Sans:wght@600&display=swap"
URL_FIRA_SANS="$URL_SERVER/css2?family=Fira+Sans:wght@500&display=swap"

CURL_OPTIONS=(--silent --proto '=https')

FNAME_OPEN_SANS_REGULAR="OpenSans-Regular"
FNAME_OPEN_SANS_SEMIBOLD="OpenSans-SemiBold"
FNAME_FIRA_SANS="FiraSans-Medium"

EXT_OPEN_SANS=".ttf"
EXT_FIRA_SANS=".ttf"

STYLE_DIR=$(dirname "$0")
STATIC_DIR="$STYLE_DIR/../static/fonts"
WORK_DIR="/tmp/update_fonts.$$"

KEEP_DOWNLOAD_DIR=0

ADD_LICENSE_PY="$STYLE_DIR/add_license_url.py"


update_font()
{
    URL="$1"
    FNAME="$2"
    EXT="$3"
    LICENSE_URL="$4"

    echo "[INFO] Checking $FNAME"

    # get the CSS for the font
    DL_FILE1="$WORK_DIR/style_$FNAME"
    curl "${CURL_OPTIONS[@]}" -o "$DL_FILE1" "$URL"

    # check if it has changed
    STYLE_FILE="$STYLE_DIR/$FNAME/style.css2"
    diff "$DL_FILE1" "$STYLE_FILE"
    RES=$?
    if [ $RES -ne 0 ]
    then
        echo "[WARNING] Found difference in style files"
        echo "          Downloaded: $DL_FILE1"
        echo "          Style file: $STYLE_FILE"
        KEEP_DOWNLOAD_DIR=1
    fi

    # extract the url from the downloaded CSS file
    # src: url(https://fonts.gstatic.com/s/opensans/v34/memSYaGs126MiZpBA-UvWbX2vVnXBbObj2OVZyOOSr4dVJWUgsjZ0C4n.ttf) format('truetype');
    URL2=$(grep src "$DL_FILE1" | cut -d\( -f2 | cut -d\) -f1)
    # echo "[DEBUG] URL2=$URL2"

    # extract the font version number
    # URL2="https://fonts.gstatic.com/s/opensans/v34/memSYaGs126MiZpBA-UvWbX2vVnXBbObj2OVZyOOSr4dVJWUgsjZ0C4n.ttf"
    VERSION=$(echo "$URL2" | cut -d/ -f6)
    # echo "[DEBUG] VERSION=$VERSION"

    # check if the same as the current version
    NEW_NAME="${FNAME}-${VERSION}${EXT}"
    if [ -f "$STATIC_DIR/$NEW_NAME" ]
    then
        echo "[INFO] OK (no change)"
    else
        # download the new font file
        DL_FILE2="$WORK_DIR/$NEW_NAME"
        curl "${CURL_OPTIONS[@]}" -o "$DL_FILE2" "$URL2"

        # add a license url inside the font metadata, if needed
        if [ -n "$LICENSE_URL" ]
        then
            python -u "$ADD_LICENSE_PY" "$DL_FILE2" "$LICENSE_URL"
        fi

        OLD_NAME=$(ls -1 "$STATIC_DIR/$FNAME"-v*"$EXT")
        echo "[WARNING] Found updated version"
        echo "          NEW: $DL_FILE2"
        echo "          OLD: $OLD_NAME"

        KEEP_DOWNLOAD_DIR=1
    fi
}


mkdir "$WORK_DIR"

# Open Sans is the main font
update_font "$URL_OPEN_SANS_REGULAR"  "$FNAME_OPEN_SANS_REGULAR"  "$EXT_OPEN_SANS" "https://fonts.google.com/specimen/Open+Sans/license"
update_font "$URL_OPEN_SANS_SEMIBOLD" "$FNAME_OPEN_SANS_SEMIBOLD" "$EXT_OPEN_SANS" "https://fonts.google.com/specimen/Open+Sans/license"

# Fira Sans is for the headings
update_font "$URL_FIRA_SANS" "$FNAME_FIRA_SANS" "$EXT_FIRA_SANS" "https://fonts.google.com/specimen/Fira+Sans/license"

if [ $KEEP_DOWNLOAD_DIR -ne 0 ]
then
    echo "[INFO] Downloaded files are in $WORK_DIR"
else
    rm -rf "$WORK_DIR"
fi

# end of file
