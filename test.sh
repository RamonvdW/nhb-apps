#!/bin/bash

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS="$*"
RED="\e[31m"
RESET="\e[0m"
TEST_DIR="./nhbapps/data_test"
TEST_DIR_FOTOS_WEBWINKEL="$TEST_DIR/webwinkel"
REPORT_DIR="/tmp/covhtml"
LOG="/tmp/test_out.txt"

# -Wa = enable deprecation warnings
PY_OPTS="-Wa"

if [ -z "$VIRTUAL_ENV" ]
then
    echo "[ERROR] Virtual environment not activated"
    exit 1
fi

[ -e "$LOG" ] && rm "$LOG"
touch "$LOG"

# include a specific third party package
COV_INCLUDE_3RD_PARTY=""
#COV_INCLUDE_3RD_PARTY="mollie"

PYCOV=""
PYCOV="-m coverage run --append --branch"       # --pylib
[ ! -z "$COV_INCLUDE_3RD_PARTY" ] && PYCOV+=" --include=*${COV_INCLUDE_3RD_PARTY}*"

export PYTHONDONTWRITEBYTECODE=1

OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate

# kill the http simulator if still running in the background
# -f check entire commandline program name is python and does not match
pgrep -f websim > /dev/null
if [ $? -eq 0 ]
then
    echo "[WARNING] simulators found running - cleaning up now"
    pkill -f websim
fi

# create empty test data directories
rm -rf "$TEST_DIR" &> /dev/null
mkdir "$TEST_DIR"
mkdir "$TEST_DIR_FOTOS_WEBWINKEL"

echo
echo "****************************** START OF TEST RUN ******************************"
echo

STAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[INFO] Now is $STAMP"

FORCE_REPORT=0
if [[ "$ARGS" =~ "--force" ]]
then
    echo "[INFO] Forcing coverage report"
    FORCE_REPORT=1
    # remove from ARGS used to decide focus
    # will still be given to ./manage.py where --force has no effect
    ARGS=${ARGS/--force/}
fi

KEEP_DB=1
if [[ "$ARGS" =~ "--clean" ]]
then
    KEEP_DB=0
    # remove from ARGS used to decide focus
    # will still be given to ./manage.py where --force has no effect
    ARGS=${ARGS/--clean/}
    echo "ARGS without --clean: $ARGS"
fi

echo "[INFO] Provided  arguments: $ARGS"
# convert a path to a test file into a test case
ARGS=${ARGS//\//.}    # replace all (//) occurences of / with .
ARGS=${ARGS/.py/}   # string .py at the end
echo "[INFO] Converted arguments: $ARGS"

FOCUS=""
FOCUS_SPECIFIC_TEST=0
if [ -z "$ARGS" ]
then
    # no args = test all = remove database
    KEEP_DB=0
    COV_INCLUDE=""
else
    # convert Function.testfile.TestCase.test_functie into "Function"
    # also works for just "Function"
    FOCUS1=""
    for arg in $ARGS;
    do
        [[ "$arg" == *".tests."* ]] && FOCUS_SPECIFIC_TEST=1
        clean_focus=$(echo "$arg" | cut -d'.' -f1)
        FOCUS1="$clean_focus $FOCUS1"
    done

    # support Func1 Func2 by converting to Func1|Func2
    # after removing initial and trailing whitespace
    FOCUS=$(echo "$FOCUS1" | sed 's/^[[:blank:]]*//;s/[[:blank:]]*$//;s/  / /g;s/ /, /g')
    echo "[INFO] Focus set to $FOCUS"

    COV_INCLUDE=$(for opt in $FOCUS1; do echo -n "$opt/*,"; done)
    [ ! -z "$COV_INCLUDE_3RD_PARTY" ] && COV_INCLUDE+="*${COV_INCLUDE_3RD_PARTY}*"
fi

# echo "[DEBUG] FOCUS=$FOCUS, FOCUS_SPECIFIC_TEST=$FOCUS_SPECIFIC_TEST"
# echo "[DEBUG] COV_INCLUDE set to $COV_INCLUDE"

if [ $KEEP_DB -eq 0 ]
then
    echo "[INFO] Checking application is free of fatal errors"
    python3 $PY_OPTS ./manage.py check --tag admin --tag models || exit $?
fi

# set high performance
#sudo cpupower frequency-set --governor performance > /dev/null

ABORTED=0

export COVERAGE_FILE="/tmp/.coverage.$$"

python3 $PY_OPTS -m coverage erase

echo "[INFO] Capturing output in $LOG"
# --pid=$$ means: stop when parent stops
# -u = unbuffered stdin/stdout
tail -f "$LOG" --pid=$$ | python -u ./number_tests.py | grep --color -E "FAIL$|ERROR$|" &
PID_TAIL=$(jobs -p | tail -1)
# echo "PID_TAIL=$PID_TAIL"

if [ $KEEP_DB -ne 1 ]
then
    echo "[INFO] Deleting test database"
    sudo -u postgres dropdb --if-exists test_data3
    echo "[INFO] Creating clean database; running migrations and performing run with nodebug"

    # add coverage with nodebug
    python3 $PY_OPTS -u $PYCOV ./manage.py test --keepdb --noinput --settings=nhbapps.settings_autotest_nodebug -v 2 Plein.tests.tests.TestPlein.test_quick &>>"$LOG"
    RES=$?
    #echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
    [ $RES -eq 3 ] && ABORTED=1
fi

# start the mail transport service simulator
python3 $PY_OPTS ./Mailer/test_tools/websim_mailer.py &
PID_WEBSIM1=$!

# start the payment service simulator
python3 $PY_OPTS ./Betaal/test-tools/websim_betaal_test.py &
PID_WEBSIM2=$!

# check all websim programs have started properly
sleep 0.5               # give python some time to load everything
kill -0 $PID_WEBSIM1    # check the simulator is running
if [ $? -ne 0 ]
then
    echo "[ERROR] Mail transport service simulator failed to start"
    exit
fi

kill -0 $PID_WEBSIM2    # check the simulator is running
if [ $? -ne 0 ]
then
    echo "[ERROR] Betaal service simulator failed to start"
    exit
fi

# -u = unbuffered stdin/stdout --> also ensures the order of stdout/stderr lines
# -v = verbose
# note: double quotes not supported around $*
echo "[INFO] Starting main test run" >>"$LOG"
python3 $PY_OPTS -u $PYCOV ./manage.py test --keepdb --settings=nhbapps.settings_autotest -v 2 $ARGS &>>"$LOG"
RES=$?
#echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"
[ $RES -eq 3 ] && ABORTED=1

echo >>"$LOG"
echo "[INFO] Finished main test run" >>"$LOG"

# stop showing the additions to the logfile, because the rest is less interesting
# use bash construct to prevent the Terminated message on the console
sleep 0.1
kill $PID_TAIL
wait $PID_TAIL 2>/dev/null

# launch log in editor
[ $RES -eq 0 ] || geany --new-instance --no-msgwin "$LOG" &

if [ $RES -eq 0 ] && [ "$FOCUS" != "" ] && [ $FOCUS_SPECIFIC_TEST -eq 0 ]
then
    echo "[INFO] Discovering all management commands in $FOCUS"
    for cmd in $(python3 ./manage.py --help);
    do
        if [ -f "$FOCUS/management/commands/$cmd.py" ]
        then
            echo -n '.'
            echo "[INFO] ./manage.py help $cmd" >>"$LOG"
            python3 $PY_OPTS -u $PYCOV ./manage.py help $cmd &>>"$LOG"
        fi
    done
    echo
fi

if [ $RES -eq 0 ] && [ $# -eq 0 ]
then
    echo "[INFO] Running help for each management command"
    for cmd_file in $(ls */management/commands/*py | sed 's/\.py$//g');
    do
        cmd=$(basename $cmd_file)
        echo -n '.'
        echo "[INFO] ./manage.py help $cmd" >>"$LOG"
        python3 $PY_OPTS -u $PYCOV ./manage.py help $cmd &>>"$LOG"
    done
    echo
fi

# stop the websim tools
# use bash construct to prevent the Terminated message on the console
kill $PID_WEBSIM1
wait $PID_WEBSIM1 2>/dev/null
kill $PID_WEBSIM2
wait $PID_WEBSIM2 2>/dev/null

# cleanup test data directories
rm -rf "$TEST_DIR"

ASK_LAUNCH=0
COVERAGE_RED=0
PRECISION=2     # 2 decimalen achter de komma

if [ $ABORTED -eq 0 ] || [ $FORCE_REPORT -eq 1 ]
then
    echo "[INFO] Generating reports" | tee -a "$LOG"

    # delete old coverage report
    rm -rf "$REPORT_DIR" &>>"$LOG"

    if [ -z "$FOCUS" ]
    then
        python3 -m coverage report --precision=$PRECISION --skip-covered --fail-under=98 $OMIT 2>&1 | tee -a "$LOG"
        res=$?

        python3 -m coverage html -d "$REPORT_DIR" --precision=$PRECISION --skip-covered $OMIT &>>"$LOG"

        if [ "$res" -gt 0 ] && [ -z "$ARGS" ]
        then
            COVERAGE_RED=1
        fi
    else
        [ ! -z "$COV_INCLUDE" ] && COV_INCLUDE="--include=$COV_INCLUDE"
        python3 -m coverage report --precision=$PRECISION $COV_INCLUDE $OMIT
        python3 -m coverage html -d "$REPORT_DIR" --precision=$PRECISION --skip-covered $COV_INCLUDE $OMIT &>>"$LOG"
    fi

    rm "$COVERAGE_FILE"

    ASK_LAUNCH=1
fi

# set normal performance
#sudo cpupower frequency-set --governor schedutil > /dev/null

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

