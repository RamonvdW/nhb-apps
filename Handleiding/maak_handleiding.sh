#!/bin/bash

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# ga naar de directory met dit script
cd $(dirname $0)

STATIC="./static/handleiding"
TEMPL="./templates/handleiding"
WIKI="/tmp/wiki"
WIKI_EXPORT="$WIKI/tmp/wiki_export.xml"

# maak the uitpak directory klaar
mkdir -p "$WIKI"
rm -rf "$WIKI"/*

# zoek de nieuwste export
LATEST=$(ls -1rt ../../testserver/*wiki_export.tgz | tail -1)
if [ -z "$LATEST" ]
then
    echo "[ERROR] Wiki export niet gevonden"
    exit 1
fi
echo "[INFO] Using wiki export $LATEST"

# pak de export uit
echo "[INFO] export wordt uitgepakt in $WIKI"
INFILE="$PWD/$LATEST"
(cd "$WIKI"; tar zxf $INFILE)

# kopieer de bestanden
echo "[INFO] static wordt opnieuw gevuld"
rm "$STATIC"/*
cp $(find "$WIKI" -type f -name \*jpg) "$STATIC"
cp $(find "$WIKI" -type f -name \*png) "$STATIC"
COUNT=$(ls -1 "$STATIC" | wc -l)
echo "[INFO]   $COUNT bestanden klaargezet in static"

echo "[INFO] template files worden opnieuw aangemaakt"
touch "$TEMPL/tmp.dtl"
rm "$TEMPL"/*dtl
echo "SITE_URL='hoi'" > ./copy_of_settings.py
echo "DEBUG=True" >> ./copy_of_settings.py
echo "ENABLE_DEBUG_TOOLBAR=False" >> ./copy_of_settings.py
cat ../nhb-apps/settings.py | grep -v "settings_local" >> ./copy_of_settings.py

python3 ./maak_handleiding.py "$WIKI_EXPORT" "$TEMPL" $*

rm ./copy_of_settings.py
COUNT=$(ls -1 "$TEMPL" | wc -l)
echo "[INFO]   $COUNT bestanden klaargezet in templates"

# end of file

