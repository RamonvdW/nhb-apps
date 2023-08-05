#!/bin/bash

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# go to the directory of the script
# because all paths in this script are relative to that location
SCRIPT_DIR=$(realpath "$0")             # volg links naar het echte script
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")     # directory van het script
cd "$SCRIPT_DIR"

OUT="$PWD/../static/js"
INFILE="$PWD/site_layout.js"

# source file to modify when the version number changes
DTL_FILE="$PWD/../templates/plein/site_layout.dtl"

if [ ! -e "$INFILE" ]
then
    echo "[ERROR] Failed to locate input $INFILE"
    exit 1
fi

if [ ! -d "$OUT" ]
then
    echo "[ERROR] Failed to locate output directory $OUT"
    exit 1
fi

if [ ! -e "$DTL_FILE" ]
then
    echo "[ERROR] Failed to locate dtl file $DTL_FILE"
    exit 1
fi

# get the sequence number
LINE=$(grep 'site_layout' "$DTL_FILE" | grep '\.js')
# <script src="{% static 'site_layout-1_min.js' %}"></script>
NR=$(echo "$LINE" | cut -d_ -f2 | cut -d- -f2)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

# delete the old outfile
rm "$OUT"/site_layout-*.js
OUTFILE="$OUT/site_layout-${NEW_NR}_min.js"

# run the minify tool
python3 ./minify_js.py "$INFILE" "$OUTFILE"
RES=$?
if [ $RES -ne 0 ]
then
    echo "[ERROR] Detected compilation error - keeping current file"
    exit 1
fi

cat "$DTL_FILE" | sed "s/site_layout-.*\.js/site_layout-${NEW_NR}_min.js/" > "$DTL_FILE.new"
mv "$DTL_FILE.new" "$DTL_FILE"

# end of file

