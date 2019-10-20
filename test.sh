#!/bin/bash

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

RED="\e[31m"
RESET="\e[0m"

OMIT="--omit=data3/wsgi.py,/usr/lib/python3.6/site-packages/*"
ARGS="$*"

coverage erase
coverage run ./manage.py test --noinput $*  # note: double quotes not supported around $*
coverage report --skip-covered --fail-under=80 $OMIT
res=$?
coverage html -d covhtml --skip-covered $OMIT

#echo "res=$res"
if [ "$res" -gt 0 ] && [ -z "$ARGS" ]
then
    echo -e "$RED"
    echo "      ==========================="
    echo "      FAILED: NOT ENOUGH COVERAGE"
    echo "      ==========================="
    echo -e "$RESET"
    firefox covhtml/index.html&
fi

# end of file

