#!/bin/bash

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

STATIC_DIR="nhbapps/.static/"
SETTINGS="nhbapps.settings_dev"
BG_DURATION=60   # minutes (60 is max voor de meeste commando's)
DEBUG=1

export PYTHONDONTWRITEBYTECODE=1

if [ "$1" = "--nodebug" ]
then
    DEBUG=0
    SETTINGS="nhbapps.settings"
fi

./manage.py check || exit 1

echo "[INFO] Refreshing static files"
rm -rf "$STATIC_DIR"*
./manage.py collectstatic -l

# start the background processes
echo "[INFO] Starting Mollie simulator"
pkill -f websim_betaal
python3 ./Betaal/test-tools/websim_betaal.py &

echo "[INFO] Starting betaal_mutaties (runtime: $BG_DURATION minutes)"
pkill -f betaal_mutaties
./manage.py betaal_mutaties --settings=$SETTINGS $BG_DURATION &

echo "[INFO] Starting bestel_mutaties (runtime: $BG_DURATION minutes)"
pkill -f bestel_mutaties
./manage.py bestel_mutaties --settings=$SETTINGS $BG_DURATION &

echo "[INFO] Starting regiocomp_mutaties (runtime: $BG_DURATION minutes)"
pkill -f regiocomp_mutaties
./manage.py regiocomp_mutaties --settings=$SETTINGS $BG_DURATION &

echo "[INFO] Starting regiocomp_tussenstand (runtime: $BG_DURATION minutes)"
pkill -f regiocomp_tussenstand
./manage.py regiocomp_tussenstand --settings=$SETTINGS $BG_DURATION &

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

echo "[INFO] Starting runserver with config $SETTINGS"
./manage.py runserver --settings=$SETTINGS --skip-checks $EXTRA_ARGS

# kill the background processes
echo "[INFO] Stopping background tasks"
pkill -f regiocomp_tussenstand
pkill -f regiocomp_mutaties
pkill -f bestel_mutaties
pkill -f betaal_mutaties
pkill -f websim_betaal

# end of file
