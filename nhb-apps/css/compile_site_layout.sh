#!/bin/bash

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# go to the directory of the script
# because all paths in this script are relative to that location
cd $(dirname $0)

OUT="$PWD/../compiled_static"
INFILE="$PWD/site_layout.css"
MINIFY_CSS="../minify_css.py"

# source file to modify when the version number changes
DTLFILE="$PWD/../../Plein/templates/plein/site_layout.dtl"

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

ruby -v > /dev/null
if [ $? -ne 0 ]
then
    echo "[ERROR] Ruby interpreter does not work"
    exit 1
fi

sass -v > /dev/null
if [ $? -ne 0 ]
then
    echo "[ERROR] Sass compiler does not work"
    exit 1
fi

if [ ! -e "$DTLFILE" ]
then
    echo "[ERROR] Failed to locate dtl file $DTLFILE"
    exit 1
fi

# get the sequence number
# <link rel="stylesheet" href="{% static 'site_layout_min-1.css' %}">
LINE=$(grep -m1 'site_layout_min' "$DTLFILE")
NR=$(echo "$LINE" | cut -d. -f1 | cut -d- -f2)
echo "[INFO] Found current sequence number: $NR"
NEWNR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEWNR"

# delete the old outfile
rm "$OUT"/site_layout_min*.css
OUTFILE="$OUT/site_layout_min-$NEWNR.css"

# run the compiler (minify)
python "$MINIFY_CSS" "$INFILE" "$OUTFILE"

# replace the sequence number in the referencing django template
cat "$DTLFILE" | sed "s/site_layout_min-.*\.css/site_layout_min-$NEWNR.css/" > "$DTLFILE.new"
mv "$DTLFILE.new" "$DTLFILE"

# end of file

