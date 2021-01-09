#!/bin/bash

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# go to the directory of the script
# because all paths in this script are relative to that location
cd $(dirname $0)

OUT="$PWD/../compiled_static"
INFILE=$(ls -1 "$PWD/materialize-src/"materialize-new-*.js | head -1)

# source file to modify when the version number changes
DTL_FILE="$PWD/../../Plein/templates/plein/site_layout.dtl"

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
LINE=$(grep 'materialize-new' "$DTL_FILE" | grep '_min.js')
# <script src="{% static 'materialize-new-1_min.js' %}"></script>
NR=$(echo "$LINE" | cut -d_ -f1 | cut -d- -f3)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

# delete the old outfile
rm "$OUT"/materialize-new*.js
OUTFILE="$OUT/materialize-new-${NEW_NR}_min.js"

# run the minify tool
python3 ./minify_js.py "$INFILE" "$OUTFILE"

if [ $? -ne 0 ]
then
    echo "[ERROR] Detected compilation error - keeping current file"
    exit 1
fi

cat "$DTL_FILE" | sed "s/materialize-new-.*\.js/materialize-new-${NEW_NR}_min.js/" > "$DTL_FILE.new"
mv "$DTL_FILE.new" "$DTL_FILE"

# end of file

