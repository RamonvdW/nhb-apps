#!/bin/bash

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

FONTS_DIR="../../static/fonts"
GLYPH_NAMES="needed-glyphs_material-icons-round.txt"
DEST="material-icons-subset-mh-v"
OTF_DEST="$FONTS_DIR/$DEST.otf"
TTX_DEST="$FONTS_DIR/$DEST.ttx"
DTL_FONTS="../../templates/plein/site_layout_fonts.dtl"

# ga naar de directory van het script (Plein/fonts/reduce/)
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

OTF_SOURCE=$(find "$FONTS_DIR" -name Material-Icons-Round-\*.otf)
if [ ! -e "$OTF_SOURCE" ]
then
    echo "[ERROR] Cannot find otf file for Material-Icons-Round"
    exit 1
fi

FULL=$(realpath "$OTF_SOURCE")
echo "[INFO] Source: $FULL"

# reduceer
rm -f "$OTF_DEST"
pyftsubset "$OTF_SOURCE" --output-file="$OTF_DEST" --glyphs-file="$GLYPH_NAMES" --unicodes=5f-7a,30-39 --no-layout-closure --name-IDs=*

if [ -e "$OTF_DEST" ]
then
    FULL=$(realpath "$OTF_DEST")
    echo "[INFO] Created $FULL"
else
    echo "[ERROR] Failed to create $OTF_DEST"
fi

# get the sequence number
LINE=$(grep "$DEST" "$DTL_FONTS")
# src: url({% static 'fonts/material-icons-subset-mh-v1.otf' %}) format('opentype');
NR=$(echo "$LINE" | cut -d. -f1 | sed 's/mh-v/@/' | cut -d@ -f2)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

# remove the old file
rm "$FONTS_DIR/$DEST$NR.otf"

# rename the destination
OTF_DEST_NEW="$FONTS_DIR/$DEST$NEW_NR.otf"
mv "$OTF_DEST" "$OTF_DEST_NEW"

# replace the sequence number in the referencing django template
sed -i "s/material-icons-subset-mh-v.*\.otf/material-icons-subset-mh-v$NEW_NR.otf/" "$DTL_FONTS"

# maak een dump van de nieuwe subset
rm -f "$TTX_DEST"     # avoids incremental filenames
# ttx "$OTF_DEST_NEW"

# end of file
