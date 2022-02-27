#!/bin/bash

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# set high performance
sudo cpupower frequency-set --governor performance > /dev/null

export PYTHONDONTWRITEBYTECODE=1

DEBUG=1
[ "$1" = "--nodebug" ] && DEBUG=0

./manage.py check
[ $? -eq 0 ] || exit 1

echo "[INFO] Refreshing static files"
STATIC_DIR="nhbapps/.static"
rm -rf "$STATIC_DIR"/*
./manage.py collectstatic -l

# start the background processes
echo "[INFO] Starting regiocomp_mutaties (runtime: 60 minutes)"
pkill -f regiocomp_mutaties
./manage.py regiocomp_mutaties 60 &
# sleep 1

echo "[INFO] Starting regiocomp_tussenstand (runtime: 60 minutes)"
pkill -f regiocomp_tussenstand
./manage.py regiocomp_tussenstand 60 &
# sleep 1

# start the development webserver
if [ $DEBUG -eq 1 ]
then
    echo "[INFO] Starting runserver with dev config and DEBUG=True"
    ./manage.py runserver --settings=nhbapps.settings_dev
else
    # run with DEBUG=False stops serving static files..
    # using --insecure fixes that
    echo "[INFO] Starting runserver"
    ./manage.py runserver --settings=nhbapps.settings --insecure
fi

# kill the background processes
echo "[INFO] Stopping background tasks"
pkill -f regiocomp_mutaties
pkill -f regiocomp_tussenstand

# set normal performance
sudo cpupower frequency-set --governor schedutil > /dev/null

# end of file
