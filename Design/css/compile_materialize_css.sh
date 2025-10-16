#!/bin/bash

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# go to the directory of the script
# because all paths in this script are relative to that location

# ga naar de directory waar het script staat
SCRIPT_DIR=$(realpath "$0")             # volg links naar het echte script
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")     # directory van het script
cd "$SCRIPT_DIR"

OUT="$PWD/../static/css"
INFILE="$PWD/materialize-src/sass/materialize.scss"
MINIFY="--style compressed"

# source file to modify when the version number changes
DTL_FILE1="$PWD/../templates/design/site_layout.dtl"
DTL_FILE2="$PWD/../templates/design/site_layout_minimaal.dtl"

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

for fname in "$DTL_FILE1" "$DTL_FILE2"
do
    if [ ! -e "$fname" ]
    then
        echo "[ERROR] Failed to locate dtl file $fname"
        exit 1
    fi
done

# get the sequence number
LINE=$(grep 'materialize-new-' "$DTL_FILE1" | grep '\.css')
# <link rel="stylesheet" href="{% static 'materialize/materialize-new-1.css' %}">
NR=$(echo "$LINE" | cut -d. -f1 | cut -d- -f3)
echo "[INFO] Found current sequence number: $NR"
NEW_NR=$(( NR + 1 ))
echo "[INFO] Decided sequence number: $NEW_NR"

# delete the old outfile
rm "$OUT"/materialize-new*.css
OUTFILE="$OUT/materialize-new-$NEW_NR.css"

# run the compiler
sass --no-cache --sourcemap=none $MINIFY "$INFILE" "$OUTFILE"
if [ $? -ne 0 ]
then
    echo "[ERROR] Detected compilation error - keeping current file"
    exit 1
fi

# replace the sequence number in the referencing django template
cat "$DTL_FILE1" | sed "s/materialize-new-.*\.css/materialize-new-$NEW_NR.css/" > "$DTL_FILE1.new"
cat "$DTL_FILE2" | sed "s/materialize-new-.*\.css/materialize-new-$NEW_NR.css/" > "$DTL_FILE2.new"
mv "$DTL_FILE1.new" "$DTL_FILE1"
mv "$DTL_FILE2.new" "$DTL_FILE2"

# end of file

