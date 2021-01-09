#!/bin/bash

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# start the background process
echo "[INFO] Starting kampioenschap_mutaties (runtime: 60 minutes)"
./manage.py kampioenschap_mutaties 60 &
sleep 1

# start the webserver
echo "[INFO] Starting runserver"
./manage.py runserver --settings=nhbapps.settings_dev

# kill the background process
echo "[INFO] Stopping kampioenschap_mutaties"
pkill -f kampioenschap_mutaties

# end of file
