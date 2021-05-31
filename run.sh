#!/bin/bash

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

export PYTHONDONTWRITEBYTECODE=1

DEBUG=0
[ "$1" = "--debug" ] && DEBUG=1

# start the background process
echo "[INFO] Starting kampioenschap_mutaties (runtime: 60 minutes)"
./manage.py kampioenschap_mutaties 60 &
sleep 1

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

# kill the background process
echo "[INFO] Stopping kampioenschap_mutaties"
pkill -f kampioenschap_mutaties

# end of file
