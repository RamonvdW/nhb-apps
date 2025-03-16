#!/bin/bash

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

STATIC_DIR="Site/.static/"
SETTINGS_DEV="Site.settings_dev"
SETTINGS_NORMAL="Site.settings"
BG_DURATION=60   # minutes (60 is max voor de meeste commando's)

export PYTHONDONTWRITEBYTECODE=1

# check the port is free
ss -l | grep -q 8000
RES=$?
if [ $RES -eq 0 ]
then
    echo "[ERROR] Port 8000 must be free"
    exit
fi

if [ "$1" = "--nodebug" ]
then
    DEBUG=0
    SETTINGS="$SETTINGS_NORMAL"
else
    DEBUG=1
    SETTINGS="$SETTINGS_DEV"
fi
echo "[INFO] Using config $SETTINGS"

echo "[INFO] Running system check"
CHECK=$(./manage.py check --settings="$SETTINGS")
RES=$?
if [ $RES -ne 0 ]
then
    echo "$CHECK"
    exit 1
fi

echo "[INFO] Refreshing static files"
rm -rf "$STATIC_DIR"*     # keeps top directory
COLLECT=$(./manage.py collectstatic --link)
RES=$?
if [ $RES -ne 0 ]
then
    echo "$COLLECT"
    exit 1
fi

# start the background processes
echo "[INFO] Starting Mollie simulator"
pkill -f websim_betaal
python3 ./Betaal/test-tools/websim_betaal.py &

echo "[INFO] Starting Google Maps simulator"
pkill -f websim_gmaps
python3 ./Locatie/test_tools/websim_gmaps.py &

echo "[INFO] Starting betaal_mutaties (runtime: $BG_DURATION minutes)"
pkill -f betaal_mutaties
./manage.py betaal_mutaties --settings="$SETTINGS" $BG_DURATION &

echo "[INFO] Starting bestel_mutaties (runtime: $BG_DURATION minutes)"
pkill -f bestel_mutaties
./manage.py bestel_mutaties --settings="$SETTINGS" $BG_DURATION &

echo "[INFO] Starting regiocomp_mutaties (runtime: $BG_DURATION minutes)"
pkill -f regiocomp_mutaties
./manage.py regiocomp_mutaties --settings="$SETTINGS" $BG_DURATION &

echo "[INFO] Starting regiocomp_tussenstand (runtime: $BG_DURATION minutes)"
pkill -f regiocomp_tussenstand
./manage.py regiocomp_tussenstand --settings="$SETTINGS" $BG_DURATION &

echo "[INFO] Starting scheids_mutaties (runtime: $BG_DURATION minutes)"
pkill -f scheids_mutaties
./manage.py scheids_mutaties --settings="$SETTINGS" $BG_DURATION &

# wacht tot alle achtergrondtaken gestart zijn
sleep 0.8

# start the development webserver
EXTRA_ARGS=''
if [ $DEBUG -ne 1 ]
then
    # run with DEBUG=False stops serving static files..
    # using --insecure fixes that
    EXTRA_ARGS="--insecure"
fi

echo "[INFO] Starting runserver"
./manage.py runserver --settings="$SETTINGS" --skip-checks $EXTRA_ARGS

# kill the background processes
echo "[INFO] Stopping background tasks"
pkill -f regiocomp_tussenstand
pkill -f regiocomp_mutaties
pkill -f bestel_mutaties
pkill -f betaal_mutaties
pkill -f scheids_mutaties
pkill -f websim_gmaps
pkill -f websim_betaal

# end of file
