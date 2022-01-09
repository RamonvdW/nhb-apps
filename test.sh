#!/bin/bash

#  Copyright (c) 2019-2022 Ramon van der Winkel.
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
pgrep -f websim > /dev/null
if [ $? -eq 0 ]
then
    echo "[WARNING] simulators found running - cleaning up now"
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

echo "[INFO] Deleting test database"
sudo -u postgres dropdb --if-exists test_data3

# -u = unbuffered stdin/stdout --> also ensures the order of stdout/stderr lines
# -v = verbose
# note: double quotes not supported around $*
echo "[INFO] Starting main test run" >>"$LOG"
python3 -u $PYCOV ./manage.py test --keepdb --settings=nhbapps.settings_autotest -v 2 --noinput $* &>>"$LOG"
RES=$?
#echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"
[ $RES -eq 3 ] && ABORTED=1

echo >>"$LOG"
echo "[INFO] Finished main test run" >>"$LOG"

if [ $RES -eq 0 -a $# -eq 0 ]
then
    # add coverage with nodebug
    echo "[INFO] Performing run with nodebug"
    python3 -u $PYCOV ./manage.py test --keepdb --settings=nhbapps.settings_autotest_nodebug -v 2 Plein.tests.TestPlein.test_quick &>>"$LOG"
    RES=$?
    #echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
    [ $RES -eq 3 ] && ABORTED=1
fi

# stop showing the additions to the logfile, because the rest is less interesting
# use bash construct to prevent the Terminated message on the console
sleep 0.1
kill $PID_TAIL
wait $PID_TAIL 2>/dev/null

if [ $RES -eq 0 -a "$FOCUS" != "" ]
then
    echo "[INFO] Discovering all management commands in $FOCUS"
    for cmd in $(python3 ./manage.py --help);
    do
        if [ -f $FOCUS/management/commands/$cmd.py ]
        then
            echo -n '.'
            echo "[INFO] ./manage.py help $cmd" >>"$LOG"
            python3 -u $PYCOV ./manage.py help $cmd &>>"$LOG"
        fi
    done
    echo
fi

if [ $RES -eq 0 -a $# -eq 0 ]
then
    echo "[INFO] Running help for each management command"
    for cmd in $(for x in */management/commands; do ls -1 $x | grep -v '__pycache__' | rev | cut -d. -f2- | rev; done);
    do
        echo -n '.'
        echo "[INFO] ./manage.py help $cmd" >>"$LOG"
        python3 -u $PYCOV ./manage.py help $cmd &>>"$LOG"
    done
    echo
fi

# stop the websim tools
# use bash construct to prevent the Terminated message on the console
kill $PID_WEBSIM1
wait $PID_WEBSIM1 2>/dev/null
kill $PID_WEBSIM2
wait $PID_WEBSIM2 2>/dev/null

ASK_LAUNCH=0
COVERAGE_RED=0

if [ $ABORTED -eq 0 -o $FORCE_REPORT -eq 1 ]
then
    echo "[INFO] Generating reports" >>"$LOG"
    echo "[INFO] Generating reports"

    # delete old coverage report
    rm -rf "$REPORT_DIR" &>>"$LOG"

    if [ -z "$FOCUS" ]
    then
        python3 -m coverage report --precision=1 --skip-covered --fail-under=98 $OMIT
        res=$?

        python3 -m coverage html -d "$REPORT_DIR" --precision=1 --skip-covered $OMIT &>>"$LOG"

        if [ "$res" -gt 0 ] && [ -z "$ARGS" ]
        then
            COVERAGE_RED=1
        fi
    else
        python3 -m coverage report --precision=1 --include=$COV_INCLUDE
        python3 -m coverage html -d "$REPORT_DIR" --precision=1 --skip-covered --include=$COV_INCLUDE &>>"$LOG"
    fi

    rm "$COVERAGE_FILE"

    ASK_LAUNCH=1
fi

# set normal performance
sudo cpupower frequency-set --governor schedutil > /dev/null

if [ $COVERAGE_RED -ne 0 ]
then
    echo
    echo -e "$RED"
    echo "      ==========================="
    echo "      FAILED: NOT ENOUGH COVERAGE"
    echo "      ==========================="
    echo -e "$RESET"
    echo
fi

if [ $ASK_LAUNCH -ne 0 ]
then
    echo "HTML report is in $REPORT_DIR  (try firefox $REPORT_DIR/index.html)"
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

