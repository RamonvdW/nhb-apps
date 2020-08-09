#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# go to the directory of the script
# because all paths in this script are relative to that location
cd $(dirname $0)

OUT="$PWD/../compiled_static"
INFILE="$PWD/materialize-src/sass/materialize.scss"
MINIFY="--style compressed"

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
LINE=$(grep -m1 'materialize-new' "$DTLFILE")
# <link rel="stylesheet" href="{% static 'materialize/materialize-new-1.css' %}">
NR=$(echo "$LINE" | cut -d. -f1 | cut -d- -f3)
echo "[INFO] Found current sequence number: $NR"
NEWNR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEWNR"

# delete the old outfile
rm "$OUT"/materialize-new*.css
OUTFILE="$OUT/materialize-new-$NEWNR.css"

# run the compiler
sass --no-cache --sourcemap=none $MINIFY $INFILE $OUTFILE

if [ $? -ne 0 ]
then
    echo "[ERROR] Detected compilation error - keeping current file"
    exit 1
fi

cat "$DTLFILE" | sed "s/materialize-new-.*\.css/materialize-new-$NEWNR.css/" > "$DTLFILE.new"
mv "$DTLFILE.new" "$DTLFILE"

# end of file

