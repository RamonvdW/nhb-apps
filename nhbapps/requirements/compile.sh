#!/bin/bash

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# ga naar de directory waar het script staat
cd $(dirname $0)

for req in requirements requirements_test requirements_dev
do
    OUT="$req.txt"
    IN="$req.in"
    echo "[INFO] Creating $OUT"
    [ -f "$OUT" ] && rm "$OUT"
    pip-compile -q "$IN"
done

# end of file

