#!/bin/bash

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

export PYTHONDONTWRITEBYTECODE=1

DEBUG=0
[ "$1" = "--debug" ] && DEBUG=1

# start the background processes
echo "[INFO] Starting regiocomp_mutaties (runtime: 60 minutes)"
./manage.py regiocomp_mutaties 60 &
sleep 1

echo "[INFO] Starting regiocomp_tussenstand (runtime: 60 minutes)"
./manage.py regiocomp_tussenstand 60 &
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

# kill the background processes
echo "[INFO] Stopping regiocomp_mutaties"
pkill -f regiocomp_mutaties

echo "[INFO] Stopping regiocomp_tussenstand"
pkill -f regiocomp_tussenstand

# end of file
