#!/bin/bash

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

FONTS_DIR="../../static/fonts"
GLYPH_NAMES="needed-glyphs_material-symbols.txt"        # created by find_icons.sh
DEST="material-symbols-subset-mh-v"
WOFF2_DEST="$FONTS_DIR/$DEST.woff2"
DTL_FONTS="../../templates/plein/site_layout_fonts.dtl"

# ga naar de directory van het script (Plein/fonts/reduce/)
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

WOFF2_SOURCE=$(find "$FONTS_DIR" -name MaterialSymbolsRounded-\*.woff2)
if [ ! -e "$WOFF2_SOURCE" ]
then
    echo "[ERROR] Cannot find woff2 file for MaterialSymbolsRounded"
    exit 1
fi

FULL=$(realpath "$WOFF2_SOURCE")
echo "[INFO] Source: $FULL"

# reduceer
rm -f "$WOFF2_DEST"
pyftsubset "$WOFF2_SOURCE" --output-file="$WOFF2_DEST" --glyphs-file="$GLYPH_NAMES" --unicodes=5f-7a,30-39 --no-layout-closure --name-IDs=*

if [ -e "$WOFF2_DEST" ]
then
    FULL=$(realpath "$WOFF2_DEST")
    echo "[INFO] Created $FULL"
else
    echo "[ERROR] Failed to create $WOFF2_DEST"
fi

# get the sequence number
LINE=$(grep "$DEST" "$DTL_FONTS")
# src: url({% static 'fonts/material-icons-subset-mh-v1.otf' %}) format('opentype');
NR=$(echo "$LINE" | cut -d. -f1 | sed 's/mh-v/@/' | cut -d@ -f2)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

# remove the old file
[ ! -z "$NR" ] && rm "$FONTS_DIR/$DEST$NR.woff2"

# rename the destination
WOFF2_DEST_NEW="$FONTS_DIR/$DEST$NEW_NR.woff2"
mv "$WOFF2_DEST" "$WOFF2_DEST_NEW"

# replace the sequence number in the referencing django template
sed -i "s#material-symbols-subset-mh-v.*\.woff2#material-symbols-subset-mh-v$NEW_NR.woff2#" "$DTL_FONTS"

# maak een dump van de nieuwe subset
TTX_DEST="$FONTS_DIR/$DEST"
rm -f "$TTX_DEST"*ttx     # avoids incremental filenames
ttx "$WOFF2_DEST_NEW"

# end of file
