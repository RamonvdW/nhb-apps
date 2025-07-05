#!/bin/bash

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# ga naar de directory waar het script staat
SCRIPT_DIR=$(realpath "$0")             # volg links naar het echte script
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")     # directory van het script
cd "$SCRIPT_DIR" || exit 1

for req in requirements requirements_dev
do
    OUT="$req.txt"
    IN="$req.in"
    echo "[INFO] Creating $OUT"
    [ -f "$OUT" ] && rm "$OUT"
    pip-compile --resolver=backtracking --strip-extras -q "$IN"
    sed -i -- "s#$SCRIPT_DIR/##g" "$OUT"
done

echo
echo "Press ENTER to start pip-sync (or ^C to abort)"
read -r

echo "[INFO] Running pip-sync requirements_dev.txt"
pip-sync requirements_dev.txt

echo
echo "[INFO] Getting licenses"
cd ../..
Site/utils/get_licenses.sh

# end of file

