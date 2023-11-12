#!/bin/bash

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# ga naar de directory waar het script staat
SCRIPT_DIR=$(realpath "$0")             # volg links naar het echte script
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")     # directory van het script
cd "$SCRIPT_DIR"

for req in requirements requirements_dev
do
    OUT="$req.txt"
    IN="$req.in"
    echo "[INFO] Creating $OUT"
    [ -f "$OUT" ] && rm "$OUT"
    pip-compile --resolver=backtracking --strip-extras -q "$IN"
done

# end of file

