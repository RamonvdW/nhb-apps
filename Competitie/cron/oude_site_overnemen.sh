#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# script for execution by a crob job
# precondition: venv must be set

MAX_FOUTEN=5    # limiet, getest met een dry-run

ID=$(id -u)
ID_ROOT=$(id -u root)
ID_WWW=$(id -u apache)
if [ $ID -ne $ID_ROOT -a $ID -ne $ID_WWW ]
then
    echo "Please run with sudo"
    exit 1
fi

cd $(dirname $0)    # ga naar de directory van het script

STAMP=$(date +"%Y%m%d_%H%M%S")

SPOOLDIR="/var/spool/download-oude-site"
[ ! -d "$SPOOLDIR" ] && mkdir "$SPOOLDIR"

URL="http://uitslagen.handboogsport.nl/index.php"
DIR="$SPOOLDIR/${STAMP}_uitslagen"
mkdir "$DIR"

# everything sent to stdout/stderr will be picked up by crontab and sent in an email
# avoid this by writing to a logfile
LOGDIR="/var/log/www"
LOG="$LOGDIR/${STAMP}_oude_site_overnemen.log"

echo "[INFO] Started at $STAMP" > "$LOG"

download_rayon()
{
    COMPNR=$1
    RAYON=$2
    AFSTAND=$3
    BOOG=$4

    OUTFILE="$DIR/${AFSTAND}_${BOOG}_rayon$RAYON.html"

    # keuze: 2=vereniging, 3=regio, 4=rayon, 6=landelijk
    # teamcomp: 1=individueel
    DATA="go=go&nologin=&vereniging=&regio=&keuze=4&rayon=$RAYON&competitie=$COMPNR&teamcomp=1&x=70&y=12"

    echo "[INFO] Downloading to $OUTFILE" >> "$LOG"
    curl -X POST --data "$DATA" $URL --output "$OUTFILE" --silent --show-error &>> "$LOG"
}

download()
{
    COMPNR=$1
    AFSTAND=$2
    BOOG=$3

    # download de rayon lijsten want daar staat de klasse in
    download_rayon $COMPNR 1 $AFSTAND $BOOG
    download_rayon $COMPNR 2 $AFSTAND $BOOG
    download_rayon $COMPNR 3 $AFSTAND $BOOG
    download_rayon $COMPNR 4 $AFSTAND $BOOG
}

download_18()
{
    # 1: Indoorcompetitie Recurve 2020/2021
    # 2: Indoorcompetitie Compound 2020/2021
    # 5: Indoorcompetitie Barebow 2020/2021
    # 6: Indoorcompetitie Longbow 2020/2021
    # 7: Indoorcompetitie Instinctive Bow 2020/2021
    download 1 18 R
    download 2 18 C
    download 5 18 BB
    download 6 18 LB
    download 7 18 IB
}

download_25()
{
    # 3: 25 meter 1 pijl competitie recurve 2020/2021
    # 4: 25 meter 1 pijl competitie compound 2020/2021
    # 8: 25 meter 1 pijl Barebow 2020/2021
    # 9: 25 meter 1 pijl Longbow 2020/2021
    # 10: 25 meter 1 pijl Instinctive Bow 2020/2021
    download 3  25 R
    download 4  25 C
    download 8  25 BB
    download 9  25 LB
    download 10 25 IB
}

echo "[INFO] Downloading to $DIR" >> "$LOG"
download_18
download_25

echo "[INFO] Starting dry run" >> "$LOG"

# move from Competitie/cron/ to top-dir
cd ../..

# convert to json
echo "[INFO] Convert downloaded html to json" >> "$LOG"
./manage.py oude_site_maak_json "$DIR" &>> "$LOG"
NEW_JSON="$DIR/oude_site.json"

# kijk of deze anders is dan de vorige json
export LC_ALL=C
PREV_JSON=$(ls -1dt $SPOOLDIR/2020*/oude_site.json | head -1)
echo "[INFO] Previous JSON=$PREV_JSON" >> "$LOG"
cmp "$PREV_JSON" "$NEW_JSON" &>> "$LOG"
CMP_RES=$?
if [ $CMP_RES -eq 0 ]
then
    # identical file - no need to import
    echo "[INFO] Renaming identical oude_site.json to zelfde_site.json"
    mv "$NEW_JSON" "$DIR/zelfde_site.json" &>> "$LOG"
else
    # do import
    ./manage.py oude_site_overnemen --dryrun "$DIR" $MAX_FOUTEN &>> "$LOG"
    RES=$?
    if [ $RES -eq 0 ]
    then
        echo "[INFO] Positief resultaat van dry-run. Overnemen van de data begint nu." >> "$LOG"
        ./manage.py oude_site_overnemen "$DIR" $MAX_FOUTEN &>> "$LOG"
    else
        echo "[WARNING] Dry-run negatief resultaat - import wordt overgeslagen!" >> "$LOG"
    fi
fi

echo "[INFO] Finished" >> "$LOG"

# end of file
