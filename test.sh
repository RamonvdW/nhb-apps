#!/bin/bash

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS="$*"
RED="\e[31m"
RESET="\e[0m"
REPORT_DIR="/tmp/covhtml"
LOG="/tmp/test_out.txt"
LOG1="/tmp/tmp_out1.txt"
[ -e "$LOG" ] && rm "$LOG" && touch "$LOG"
[ -e "$LOG1" ] && rm "$LOG1"

PYCOV=""
PYCOV="-m coverage run --append --branch"

export PYTHONDONTWRITEBYTECODE=1

OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate
# show all saml2 and djangosaml2idp source files
#OMIT="--omit=data3/wsgi.py,manage.py,/usr/local/lib64/*,/usr/lib/*,/usr/local/lib/python3.6/site-packages/c*,/usr/local/lib/python3.6/site-packages/da*,/usr/local/lib/python3.6/site-packages/de*,/usr/local/lib/python3.6/site-packages/i*,/usr/local/lib/python3.6/site-packages/p*,/usr/local/lib/python3.6/site-packages/q*,/usr/local/lib/python3.6/site-packages/r*,/usr/local/lib/python3.6/site-packages/si*,/usr/local/lib/python3.6/site-packages/u*,/usr/local/lib/python3.6/site-packages/django/*"

# set high performance
sudo cpupower frequency-set --governor performance > /dev/null

# kill the http simulator if still running in the background
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

FORCE_REPORT=0
if [[ "$ARGS" =~ "--force" ]]
then
    FORCE_REPORT=1
    # remove from ARGS used to decide focus
    # will still be given to ./manage.py where --force has no effect
    ARGS=$(echo "$ARGS" | sed 's/--force//')
fi

FOCUS=""
if [ ! -z "$ARGS" ]
then
    # convert Function.testfile.TestCase.test_functie into "Function"
    # also works for just "Function"
    FOCUS1=""
    for arg in $ARGS;
    do
        clean_focus=$(echo "$arg" | cut -d'.' -f1)
        FOCUS1="$clean_focus $FOCUS1"
    done

    # support Func1 Func2 by converting to Func1|Func2
    # after removing initial and trailing whitespace
    FOCUS=$(echo "$FOCUS1" | sed 's/^[[:blank:]]*//;s/[[:blank:]]*$//;s/  / /g;s/ /, /g')
    echo "[INFO] Focus set to $FOCUS"

    COV_INCLUDE=$(for opt in $FOCUS1; do echo -n "$opt/*,"; done)
    #echo "[DEBUG] COV_INCLUDE set to $COV_INCLUDE"
fi

ABORTED=0

# start the simulator for the mailer
python3 ./Mailer/test_tools/websim_mailer.py &
PID_WEBSIM1=$!
sleep 0.5               # give python some time to load everything
kill -0 $PID_WEBSIM1    # check the simulator is running
RES=$?
#echo "RES=$RES"
if [ $RES -ne 0 ]
then
    echo "[ERROR] Mail server simulator failed to start"
    exit
fi

# start the simulator for the bondspas downloader
python3 ./Bondspas/test-tools/websim_bondspas.py &
PID_WEBSIM2=$!
sleep 0.5               # give python some time to load everything
kill -0 $PID_WEBSIM2    # check the simulator is running
RES=$?
#echo "RES=$RES"
if [ $RES -ne 0 ]
then
    echo "[ERROR] Bondspas server simulator failed to start"
    exit
fi

export COVERAGE_FILE="/tmp/.coverage.$$"

python3 -m coverage erase

echo "[INFO] Capturing output in $LOG"
COLOR_DEFAULT=$(tput sgr0)
COLOR_RED=$(tput setaf 1)
tail -f "$LOG" | grep --color -E "FAIL$|ERROR$|" &
PID_TAIL=$!

# -u = unbuffered stdin/stdout
# -v = verbose
# note: double quotes not supported around $*
python3 -u $PYCOV ./manage.py test --settings=nhbapps.settings_autotest -v 2 --noinput $* >>"$LOG" 2>&1
RES=$?
#echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"
[ $RES -eq 3 ] && ABORTED=1

echo >> "$LOG"

# use bash construct to prevent the Terminated message on the console
kill $PID_TAIL
wait $PID_TAIL 2>/dev/null

if [ $RES -eq 0 -a $# -eq 0 ]
then
    # add coverage with nodebug
    echo "[INFO] Performing run with nodebug"
    python3 -u $PYCOV ./manage.py test --settings=nhbapps.settings_autotest_nodebug -v 2 Plein.tests.TestPlein.test_quick >>"$LOG" 2>&1
    RES=$?
    #echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
    [ $RES -eq 3 ] && ABORTED=1
fi

if [ $RES -eq 0 -a "$FOCUS" != "" ]
then
    echo "[INFO] Discovering all management commands in $FOCUS"
    for cmd in $(python3 ./manage.py --help);
    do
        [ -f $FOCUS/management/commands/$cmd.py ] && python3 -u $PYCOV ./manage.py $cmd help >>"$LOG" 2>&1
    done
fi

if [ $RES -eq 0 -a $# -eq 0 ]
then
    echo "[INFO] Discovering all management commands"
    for cmd in $(python3 ./manage.py --help);
    do
        [ -f */management/commands/$cmd.py ] && python3 -u $PYCOV ./manage.py $cmd help >>"$LOG" 2>&1
    done
fi

# stop the websim tools
# use bash construct to prevent the Terminated message on the console
kill $PID_WEBSIM1
wait $PID_WEBSIM1 2>/dev/null
kill $PID_WEBSIM2
wait $PID_WEBSIM2 2>/dev/null

if [ $ABORTED -eq 0 -o $FORCE_REPORT -eq 1 ]
then
    echo "[INFO] Generating reports"

    # delete old coverage report
    rm -rf "$REPORT_DIR"

    echo
    if [ -z "$FOCUS" ]
    then
        python3 -m coverage report --precision=1 --skip-covered --fail-under=98 $OMIT | tee -a "$LOG"
        res=$?

        echo
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
    else
        python3 -m coverage report --precision=1 --include=$COV_INCLUDE | tee -a "$LOG"
        python3 -m coverage html -d "$REPORT_DIR" --precision=1 --skip-covered --include=$COV_INCLUDE
        echo "HTML report is in $REPORT_DIR  (try firefox $REPORT_DIR/index.html)"
    fi

    rm "$COVERAGE_FILE"

    # set normal performance
    sudo cpupower frequency-set --governor schedutil > /dev/null

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

# set normal performance
sudo cpupower frequency-set --governor schedutil > /dev/null

# end of file

