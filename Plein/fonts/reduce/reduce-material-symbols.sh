#!/bin/bash

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

FONTS_DIR="../../static/fonts"
GLYPH_NAMES="needed-glyphs_material-symbols.txt"        # created by find_icons.sh
SUBSET_NAME="material-symbols-subset-mh-v"
DEST="$FONTS_DIR/${SUBSET_NAME}NEW.woff2"
DTL_FONTS="../../templates/plein/site_layout_fonts.dtl"

# ga naar de directory van het script (Plein/fonts/reduce/)
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

FONTS_SOURCE=$(find "$FONTS_DIR" -name Material-Symbols-v\*.ttf)
if [ ! -e "$FONTS_SOURCE" ]
then
    echo "[ERROR] Cannot find Material-Symbols font file in $FONTS_DIR"
    exit 1
fi

SOURCE_FULL=$(realpath "$FONTS_SOURCE")
echo "[INFO] Source: $SOURCE_FULL"

# reduceer
rm -f "$DEST"
pyftsubset "$FONTS_SOURCE" --output-file="$DEST" --flavor=woff2 --glyphs-file="$GLYPH_NAMES" --unicodes=5f-7a,30-39 --no-layout-closure --name-IDs=*

if [ -e "$DEST" ]
then
    DEST_FULL=$(realpath "$DEST")
    echo "[INFO] Created $DEST_FULL"
else
    echo "[ERROR] Failed to create $DEST"
fi

# get the sequence number
LINE=$(grep "$SUBSET_NAME" "$DTL_FONTS")
# src: url({% static 'fonts/material-icons-subset-mh-v1.otf' %}) format('opentype');
NR=$(echo "$LINE" | cut -d. -f1 | sed 's/mh-v/@/' | cut -d@ -f2)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

DEST_NEW="$FONTS_DIR/$SUBSET_NAME${NEW_NR}.woff2"

# remove the old file
[ -f "$DEST_NEW" ] && rm "$DEST_NEW"

# rename the destination
mv "$DEST" "$DEST_NEW"

# replace the sequence number in the referencing django template
sed -i "s#material-symbols-subset-mh-v$NR.woff2#material-symbols-subset-mh-v$NEW_NR.woff2#" "$DTL_FONTS"

# maak een dump van de nieuwe subset
# TTX_DEST="$FONTS_DIR/$SUBSET_NAME"
# rm -f "$TTX_DEST"*ttx     # avoids incremental filenames
# ttx "$DEST_NEW"

# end of file
