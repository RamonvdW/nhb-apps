#!/bin/bash

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

URL_SERVER="https://fonts.googleapis.com"

#URL_MATERIAL_SYMBOLS="$URL_SERVER/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0"         # only filled
#URL_MATERIAL_SYMBOLS="$URL_SERVER/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0..1,0"      # gives 2 fonts, not variable font
URL_MATERIAL_SYMBOLS="https://raw.githubusercontent.com/google/material-design-icons/refs/heads/master/variablefont/MaterialSymbolsRounded%5BFILL%2CGRAD%2Copsz%2Cwght%5D.ttf"
URL_OPEN_SANS="$URL_SERVER/css2?family=Open+Sans&display=swap"
URL_FIRA_SANS="$URL_SERVER/css2?family=Fira+Sans:wght@500&display=swap"

CURL_OPTIONS=(--silent --proto '=https')

FNAME_MATERIAL_SYMBOLS="Material-Symbols"
FNAME_OPEN_SANS="OpenSans-Regular"
FNAME_FIRA_SANS="FiraSans-Medium"

EXT_MATERIAL_SYMBOLS=".ttf"
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


# download a font from GitHub, without style information
gh_update_font()
{
    URL="$1"
    FNAME="$2"
    EXT="$3"
    LICENSE_URL="$4"

    echo "[INFO] Checking $FNAME"

    # download the raw file from
    DL_FILE1="$WORK_DIR/$FNAME"
    curl "${CURL_OPTIONS[@]}" -o "$DL_FILE1" "$URL"

    OLD_FILE=$(find "$STATIC_DIR" -name "$FNAME-v"\*)

    cmp --silent "$OLD_FILE" "$DL_FILE1"
    cmp_res=$?
    if [ $cmp_res -eq 0 ]
    then
        echo "[INFO] OK (no change)"
    elif [ $cmp_res -eq 1 ]
    then
        echo "[WARNING] Found updated version"
        echo "          NEW: $DL_FILE1"
        echo "          OLD: $OLD_FILE"
    else
        echo "[ERROR] cmp_res=$cmp_res"
    fi
}


mkdir "$WORK_DIR"

# Material Symbols are for the icons on the site
gh_update_font "$URL_MATERIAL_SYMBOLS" "$FNAME_MATERIAL_SYMBOLS" "$EXT_MATERIAL_SYMBOLS" "https://www.apache.org/licenses/LICENSE-2.0.html"

# Open Sans is the main font
update_font "$URL_OPEN_SANS" "$FNAME_OPEN_SANS" "$EXT_OPEN_SANS" "https://fonts.google.com/specimen/Open+Sans/license"

# Fira Sans is for the headings
update_font "$URL_FIRA_SANS" "$FNAME_FIRA_SANS" "$EXT_FIRA_SANS" "https://fonts.google.com/specimen/Fira+Sans/license"

if [ $KEEP_DOWNLOAD_DIR -ne 0 ]
then
    echo "[INFO] Downloaded files are in $WORK_DIR"
else
    rm -rf "$WORK_DIR"
fi

# end of file
