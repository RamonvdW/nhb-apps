#!/bin/bash

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# set high performance
sudo cpupower frequency-set --governor performance > /dev/null

export PYTHONDONTWRITEBYTECODE=1

DEBUG=1
SETTINGS="nhbapps.settings_dev"
if [ "$1" = "--nodebug" ]
then
    DEBUG=0
    SETTINGS="nhbapps.settings"
fi

./manage.py check
[ $? -eq 0 ] || exit 1

echo "[INFO] Refreshing static files"
STATIC_DIR="nhbapps/.static"
rm -rf "$STATIC_DIR"/*
./manage.py collectstatic -l

# start the background processes
echo "[INFO] Starting Mollie simulator"
pkill -f websim_betaal
python3 ./Betaal/test-tools/websim_betaal.py &

echo "[INFO] Starting betaal_mutaties (runtime: 60 minutes)"
pkill -f betaal_mutaties
./manage.py betaal_mutaties --settings=$SETTINGS 60 &

echo "[INFO] Starting bestel_mutaties (runtime: 60 minutes)"
pkill -f bestel_mutaties
./manage.py bestel_mutaties --settings=$SETTINGS 60 &

echo "[INFO] Starting regiocomp_mutaties (runtime: 60 minutes)"
pkill -f regiocomp_mutaties
./manage.py regiocomp_mutaties --settings=$SETTINGS 60 &

echo "[INFO] Starting regiocomp_tussenstand (runtime: 60 minutes)"
pkill -f regiocomp_tussenstand
./manage.py regiocomp_tussenstand --settings=$SETTINGS 60 &

# start the development webserver
if [ $DEBUG -eq 1 ]
then
    echo "[INFO] Starting runserver with dev config and DEBUG=True"
    ./manage.py runserver --settings=$SETTINGS
else
    # run with DEBUG=False stops serving static files..
    # using --insecure fixes that
    echo "[INFO] Starting runserver"
    ./manage.py runserver --settings=$SETTINGS --insecure
fi

# set normal performance
sudo cpupower frequency-set --governor schedutil > /dev/null

# kill the background processes
echo "[INFO] Stopping background tasks"
pkill -f regiocomp_tussenstand
pkill -f regiocomp_mutaties
pkill -f bestel_mutaties
pkill -f betaal_mutaties
pkill -f websim_betaal

# end of file
