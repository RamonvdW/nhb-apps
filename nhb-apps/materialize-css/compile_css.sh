#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# go to the directory of the script
# because all paths in this script are relative to that location
cd $(dirname $0)

OUT="$PWD/../global_static/materialize/"
OUTFILE="$OUT/materialize-new.css"
INFILE="$PWD/materialize-src/sass/materialize.scss"
MINIFY="--style compressed"

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

sass --no-cache --sourcemap=none $MINIFY $INFILE $OUTFILE

# end of file

