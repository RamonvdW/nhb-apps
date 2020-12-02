#!/bin/bash

# start the background process
./manage.py kampioenschap_mutaties 60 &

# start the webserver
./manage.py runserver

# kill the background process
pkill -f kampioenschap_mutaties

# end of file
