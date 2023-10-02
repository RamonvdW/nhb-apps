#!/bin/bash

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# ga naar de directory van het script in ~/Plein/fonts/reduce
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

# ga naar de top directory van het project
cd ../../..

OUT_TMP="/tmp/find_icons.txt"
OUT="$SCRIPT_DIR/needed-glyphs_material-icons-round.txt"
HANDLED='@@@'   # dummy, to allow concatenation

echo "[INFO] Searching for icons in templates and sources"
grep material-icons-round */templates/*/*dtl | grep -v secondary-content | sed -s 's/material-icons-round/@/' | cut -d@ -f2- | cut -d\> -f2- | sed -s 's#</i>#@#' | cut -d@ -f1 > "$OUT_TMP"

# handle include 'plein/card_..' icon="xxx"
grep icon= */templates/*/*dtl | sed 's/icon=/@/' | cut -d@ -f2 | cut -d\" -f2 >> "$OUT_TMP"
HANDLED+="|{{ icon }}"       # in Plein/templates/plain/card_*dtl

# handle {{ korting.icon_name }}
grep icon_name */view*py | cut -d= -f2 | cut -d\' -f2 >> "$OUT_TMP"
HANDLED+="|{{ korting.icon_name }}"

# handle kaartje.icon
grep kaartje.icon */view*py | cut -d= -f2- | cut -d\' -f2 >> "$OUT_TMP"
HANDLED+="|kaartje.icon"

# handle kaartje.icoon
grep 'icoon=' */view*py | cut -d= -f2- | cut -d\" -f2 >> "$OUT_TMP"
HANDLED+="|kaartje.icoon|ander.icoon"


echo "[INFO] Checking for missed situations"
grep -vE "$HANDLED" "$OUT_TMP" | sort -u > "$OUT"
rm "$OUT_TMP"
grep -E '{{|}' "$OUT"       # typical in template files

COUNT=$(wc -l < "$OUT")
echo "[INFO] Found $COUNT icons, see $OUT"

# end of file
