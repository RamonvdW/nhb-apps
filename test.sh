#!/bin/bash

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS="$*"
RED="\e[31m"
RESET="\e[0m"
REPORT_DIR="/tmp/covhtml"
OMIT="--omit=data3/wsgi.py,manage.py,/usr/*/python3*/site-packages/*"

# start the http simulator in the background
pgrep -f websim
if [ $? -eq 0 ]
then
    echo "[ERROR] websim is already running - please stop it"
    exit 1
fi

echo
echo "****************************** START OF TEST RUN ******************************"
echo

python3.6 ./websim.py &

rm -rf "$REPORT_DIR"

coverage erase

coverage run --append --branch ./manage.py test --noinput $*  # note: double quotes not supported around $*
if [ $# -eq 0 ]
then
    # add coverage with debug enabled
    echo "[INFO] Performing quick debug run"
    coverage run --append --branch ./manage.py test --debug-mode Plein.tests.TestPlein.test_plein_normaal &>/dev/null
fi

# stop the http simulator
# do this by killing the most recent background task
# and use bash construct to prevent the Terminated message on the console
kill $!
wait $! 2>/dev/null

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

