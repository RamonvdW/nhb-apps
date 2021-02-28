#!/bin/bash

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS="$*"
RED="\e[31m"
RESET="\e[0m"
REPORT_DIR="/tmp/covhtml"
LOG="/tmp/test_out.txt"
[ -e "$LOG" ] && rm "$LOG"

export PYTHONDONTWRITEBYTECODE=1

OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate
# show all saml2 and djangosaml2idp source files
#OMIT="--omit=data3/wsgi.py,manage.py,/usr/local/lib64/*,/usr/lib/*,/usr/local/lib/python3.6/site-packages/c*,/usr/local/lib/python3.6/site-packages/da*,/usr/local/lib/python3.6/site-packages/de*,/usr/local/lib/python3.6/site-packages/i*,/usr/local/lib/python3.6/site-packages/p*,/usr/local/lib/python3.6/site-packages/q*,/usr/local/lib/python3.6/site-packages/r*,/usr/local/lib/python3.6/site-packages/si*,/usr/local/lib/python3.6/site-packages/u*,/usr/local/lib/python3.6/site-packages/django/*"

# start the http simulator in the background
pgrep -f websim
if [ $? -eq 0 ]
then
    echo "[WARNING] websim was already running - killing it now with 'pkill -f websim'"
    pkill -f websim
fi

echo
echo "****************************** START OF TEST RUN ******************************"
echo

echo "[INFO] Checking application is free of fatal errors"
python3 ./manage.py check || exit $?

FOCUS=""
if [ ! -z "$ARGS" ]
then
    # convert Function.testfile.TestCase.test_functie into "Function"
    # also works for just "Function"
    FOCUS=$(echo "$ARGS" | cut -d'.' -f1)
    # support Func1 Func2 by converting to Func1|Func2
    FOCUS=$(echo "$FOCUS" | sed 's/ /|/g')
    echo "[INFO] Focus set to: $FOCUS"
fi

ABORTED=0

# start the simulator (for the mailer)
python3 ./Mailer/test_tools/websim.py &

export COVERAGE_FILE="/tmp/.coverage.$$"

python3 -m coverage erase

# note: double quotes not supported around $*
echo "[INFO] Capturing output in $LOG"
python3 -m coverage run --append --branch ./manage.py test --settings=nhbapps.settings_dev --noinput $* 2>&1 | tee "$LOG"
RES=$?
[ $RES -eq 3 ] && ABORTED=1
#echo "[DEBUG] Coverage run result: $RES"
if [ $RES -eq 0 -a $# -eq 0 ]
then
    # add coverage with debug and wiki enabled
    echo "[INFO] Performing run with debug + wiki run"
    python3 -m coverage run --append --branch \
        ./manage.py test --settings=nhbapps.settings_dev_wiki_debug Plein.tests.TestPlein.test_quick Functie.test_saml2idp &>/dev/null
    RES=$?
    [ $RES -eq 3 ] && ABORTED=1
    #echo "[DEBUG] Debug coverage run result: $RES"
fi

# stop the http simulator
# do this by killing the most recent background task
# and use bash construct to prevent the Terminated message on the console
kill $!
wait $! 2>/dev/null

if [ $ABORTED -eq 0 ]
then
    echo "[INFO] Generating reports"

    # delete old coverage report
    rm -rf "$REPORT_DIR"

    echo
    if [ -z "$FOCUS" ]
    then
        python3 -m coverage report --precision=1 --skip-covered --fail-under=98 $OMIT | tee -a "$LOG"
        res=$?
    else
        python3 -m coverage report --precision=1 $OMIT | grep -E "$FOCUS|----|Cover" | tee -a "$LOG"
        res=0
    fi
    #echo "res=$res"
    echo

	# TODO: dark themed coverage report
    python3 -m coverage html -d "$REPORT_DIR" --precision=1 --skip-covered $OMIT

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

    rm "$COVERAGE_FILE"

    echo
    echo -n "Press ENTER to start firefox now, or Ctrl+C to abort"
    read -t 5
    if [ $? -ne 0 ]
    then
        # automatically abort
        echo "^C"
        exit 1
    fi

    echo
    echo "Launching firefox"
    firefox $REPORT_DIR/index.html &

    echo "Done"
fi

# end of file

