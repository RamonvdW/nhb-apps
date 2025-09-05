#!/bin/bash

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

FONTS_DIR="../../static/fonts"

DEST="firasans-medium-subset-mh-v"
WOFF_DEST="$FONTS_DIR/$DEST.woff"
# TTX_DEST="$FONTS_DIR/$DEST.ttx"
DTL_FONTS="../../templates/plein/site_layout_fonts.dtl"

# ga naar de directory van het script (Plein/fonts/reduce/)
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

TTF_SOURCE=$(find "$FONTS_DIR" -name FiraSans-Medium\*.ttf)
if [ ! -e "$TTF_SOURCE" ]
then
    echo "[ERROR] Cannot find ttf file for FiraSans-Medium"
    exit 1
fi

FULL=$(realpath "$TTF_SOURCE")
echo "[INFO] Source: $FULL"

# reduceer
rm -f "$WOFF_DEST"
pyftsubset "$TTF_SOURCE" --flavor=woff --output-file="$WOFF_DEST" --unicodes=20-7e --no-layout-closure

# get the sequence number
LINE=$(grep "$DEST" "$DTL_FONTS")
# src: url({% static 'fonts/firasans-medium-subset-mh-v1.ttf' %}) format('truetype');
NR=$(echo "$LINE" | cut -d. -f1 | sed 's/mh-v/@/' | cut -d@ -f2)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

# remove the old file
rm "$FONTS_DIR/$DEST$NR.*"

# move to the destination
WOFF_DEST_NEW="$FONTS_DIR/$DEST$NEW_NR.woff"
mv "$WOFF_DEST" "$WOFF_DEST_NEW"

# replace the sequence number in the referencing django template
sed -i "s/firasans-medium-subset-mh-v.*\.woff/firasans-medium-subset-mh-v$NEW_NR.woff/" "$DTL_FONTS"

# maak een dump van de nieuwe subset
# rm -f "$TTX_DEST"     # avoids incremental filenames
# ttx "$WOFF_DEST_NEW"

# end of file

