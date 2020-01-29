#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS="$*"
RED="\e[31m"
RESET="\e[0m"
REPORT_DIR="/tmp/covhtml"
OMIT="--omit=data3/wsgi.py,/usr/*/python3*/site-packages/*"

rm -rf "$REPORT_DIR"

coverage erase

coverage run --append --branch ./manage.py test --noinput $*  # note: double quotes not supported around $*
if [ $# -eq 0 ]
then
    # add coverage with debug enabled
    coverage run --append --branch ./manage.py test --debug-mode Plein.tests.PleinTest.test_plein_normaal
fi

echo
coverage report --skip-covered --fail-under=90 $OMIT
res=$?
#echo "res=$res"
echo

coverage html -d "$REPORT_DIR" --skip-covered $OMIT

if [ "$res" -gt 0 ] && [ -z "$ARGS" ]
then
    echo -e "$RED"
    echo "      ==========================="
    echo "      FAILED: NOT ENOUGH COVERAGE"
    echo "      ==========================="
    echo -e "$RESET"
else
    echo "HTML report is in $REPORT_DIR  (try firefox $REPORT_DIR/index.html)"
fi

echo
echo -n "Press ENTER to start firefox now, or Ctrl+C to abort"
timeout --foreground 10 read
if [ $? -ne 0 ]
then
    # automatically abort
    echo "^C"
    exit 1
fi

firefox $REPORT_DIR/index.html &

# end of file

