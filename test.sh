#!/bin/bash

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS="$*"
COV_AT_LEAST=96.70
RED="\e[31m"
RESET="\e[0m"
TEST_DIR="./SiteMain/tmp_test_data"
TEST_DIR_FOTOS_WEBWINKEL="$TEST_DIR/webwinkel"
REPORT_DIR="/tmp/covhtml"
LOG="/tmp/test_out.txt"
TMP_HTML="/tmp/tmp_html/"             # used by e2e_open_in_browser()
STATIC_DIR="$PWD/SiteMain/.static/"   # must be full path

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

COVRC="--rcfile=./SiteMain/utils/coverage.rc"
PYCOV="-m coverage run $COVRC --append --branch"       # --pylib
[ -n "$COV_INCLUDE_3RD_PARTY" ] && PYCOV+=" --include=*${COV_INCLUDE_3RD_PARTY}*"

export PYTHONDONTWRITEBYTECODE=1

OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate

# kill the http simulator if still running in the background
# -f check entire commandline program name is python and does not match
pgrep -f websim > /dev/null
RES=$?
if [ $RES -eq 0 ]
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

if [[ "$ARGS" =~ "-h" ]]
then
    echo "./test.sh [options] [testcase selector(s)]"
    echo ""
    echo "options:"
    echo "  --force     Force generate of coverage, even when tests fail"
    echo "  --fullcov   Do not focus the coverage report"
    echo "  --clean     Remove database (automatic for full run)"
    echo
    echo "Example selector: App_dir.tests_dir.test_filename.TestCaseClass.test_func"
    exit
fi

FORCE_REPORT=0
if [[ "$ARGS" =~ "--force" ]]
then
    echo "[INFO] Forcing coverage report"
    FORCE_REPORT=1
    # remove from ARGS used to decide focus
    # will still be given to ./manage.py where --force has no effect
    ARGS=${ARGS/--force/}
fi

FORCE_FULL_COV=0
if [[ "$ARGS" =~ "--fullcov" ]]
then
    echo "[INFO] Forcing full coverage report"
    FORCE_FULL_COV=1
    # remove from ARGS used to decide focus
    # will still be given to ./manage.py where --force has no effect
    ARGS=${ARGS/--fullcov/}
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

# convert a path to a module or test.py file into a test case
ARGS=${ARGS//\//.}                              # replace all (//) occurrences of / with .
[ "${ARGS: -1}" == "." ] && ARGS=${ARGS:0:-1}   # strip last . (case: Plein/)
ARGS=${ARGS/.py/}                               # strip .py at the end
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
    [ -n "$COV_INCLUDE_3RD_PARTY" ] && COV_INCLUDE+="*${COV_INCLUDE_3RD_PARTY}*"
fi

# echo "[DEBUG] FOCUS=$FOCUS, FOCUS_SPECIFIC_TEST=$FOCUS_SPECIFIC_TEST"
# echo "[DEBUG] COV_INCLUDE set to $COV_INCLUDE"

if [ $KEEP_DB -eq 0 ]
then
    echo "[INFO] Checking application is free of fatal errors"
    python3 $PY_OPTS ./manage.py check --tag admin --tag models || exit $?
fi

echo "[INFO] Refreshing static files"
rm -rf "$STATIC_DIR"*     # keeps top directory
COLLECT=$(./manage.py collectstatic --link)
RES=$?
if [ $RES -ne 0 ]
then
    echo "$COLLECT"
    exit 1
fi

# create a link from /tmp/static to the actual static dir
# used to load static content from html written by e2e_open_in_browser()
rm -rf "$TMP_HTML"
mkdir -p "$TMP_HTML"
ln -s "$STATIC_DIR" "$TMP_HTML/static"

export COVERAGE_FILE="/tmp/.coverage.$$"
python3 $PY_OPTS -m coverage erase

echo "[INFO] Capturing output in $LOG"
# --pid=$$ means: stop when parent stops
# -u = unbuffered stdin/stdout
tail -f "$LOG" --pid=$$ | python -u ./SiteMain/utils/number_tests.py | grep --color -E "FAIL$|ERROR$|" &
PID_TAIL=$(jobs -p | tail -1)
# echo "PID_TAIL=$PID_TAIL"

ABORTED=0

if [ $KEEP_DB -ne 1 ]
then
    echo "[INFO] Deleting test database"
    old_pwd="$PWD"
    cd /tmp
    sudo -u postgres dropdb --if-exists test_data3 || exit 1
    sudo -u postgres createdb -E UTF8 test_data3 || exit 1
    sudo -u postgres psql -d test_data3 -q -c 'GRANT CREATE ON SCHEMA public TO django' || exit 1
    echo "[INFO] Creating clean database; running migrations and performing run with nodebug"
    cd "$old_pwd"

    # add coverage with no-debug
    python3 $PY_OPTS -u $PYCOV ./manage.py test --keepdb --noinput --settings=SiteMain.settings_autotest_nodebug -v 2 Plein.tests.tests.TestPlein.test_quick &>>"$LOG"
    RES=$?
    #echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
    [ $RES -eq 3 ] && ABORTED=1
fi

echo "[INFO] Starting websim tasks"

# start the mail transport service simulator
python3 $PY_OPTS ./Mailer/test_tools/websim_mailer.py &
PID_WEBSIM1=$!

# start the payment service simulator
python3 $PY_OPTS ./Betaal/test-tools/websim_betaal_test.py &
PID_WEBSIM2=$!

# start the payment service simulator
python3 $PY_OPTS ./Locatie/test_tools/websim_gmaps.py &
PID_WEBSIM3=$!

# check all websim programs have started properly
sleep 0.5               # give python some time to load everything
kill -0 $PID_WEBSIM1    # check the simulator is running
RES=$?
if [ $RES -ne 0 ]
then
    echo "[ERROR] Mail transport service simulator failed to start"
    exit
fi

kill -0 $PID_WEBSIM2    # check the simulator is running
RES=$?
if [ $RES -ne 0 ]
then
    echo "[ERROR] Betaal service simulator failed to start"
    exit
fi

kill -0 $PID_WEBSIM3    # check the simulator is running
RES=$?
if [ $RES -ne 0 ]
then
    echo "[ERROR] Google Maps simulator failed to start"
    exit
fi

# set high performance
OLD_PERF=$(powerprofilesctl get)
powerprofilesctl set performance

# -u = unbuffered stdin/stdout --> also ensures the order of stdout/stderr lines
# -v = verbose
# note: double quotes not supported around $*
echo "[INFO] Starting main test run" >>"$LOG"
python3 $PY_OPTS -u $PYCOV ./manage.py test --keepdb --settings=SiteMain.settings_autotest -v 2 $ARGS &>>"$LOG"
RES=$?
#echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"
[ $RES -eq 3 ] && ABORTED=1

echo >>"$LOG"
echo "[INFO] Finished main test run" >>"$LOG"


# launch a browser with all the stored web pages
find "$TMP_HTML" -type f | grep -q html
RES=$?
# echo "[DEBUG] RES=$RES"
if [ $RES -eq 0 ]
then
    # echo "[DEBUG] Found HTML files in $TMP_HTML"
    HTML_FILES=$(ls -1tr "$TMP_HTML"/*html)   # sorted by creation time
    firefox $HTML_FILES &
fi


# stop showing the additions to the logfile, because the rest is less interesting
# use bash construct to prevent the Terminated message on the console
sleep 0.1
kill "$PID_TAIL"
wait "$PID_TAIL" 2>/dev/null

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
            python3 $PY_OPTS -u $PYCOV ./manage.py help "$cmd" &>>"$LOG"
        fi
    done
    echo
fi

if [ $RES -eq 0 ] && [ $# -eq 0 ]
then
    echo "[INFO] Running help for each management command" >>"$LOG"
    echo "[INFO] Running help for each management command"
    for cmd_file in $(find -- */management/commands -name \*py | sed 's/\.py$//g');
    do
        cmd=$(basename "$cmd_file")
        echo -n '.'
        echo "[INFO] ./manage.py help $cmd" >>"$LOG"
        python3 $PY_OPTS -u $PYCOV ./manage.py help "$cmd" &>>/dev/null    # ignore output
    done
    echo
fi

# stop the websim tools
# use bash construct to prevent the Terminated message on the console
echo "[INFO] Terminating websim tasks"
kill $PID_WEBSIM1
wait $PID_WEBSIM1 2>/dev/null
kill $PID_WEBSIM2
wait $PID_WEBSIM2 2>/dev/null
kill $PID_WEBSIM3
wait $PID_WEBSIM3 2>/dev/null

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

    if [ -z "$FOCUS" ] || [ $FORCE_FULL_COV -ne 0 ]
    then
        python3 -m coverage report $COVRC --precision=$PRECISION --skip-covered --fail-under=$COV_AT_LEAST $OMIT 2>&1 | tee -a "$LOG"
        res=${PIPESTATUS[0]}
        if [ $res -gt 0 ] && [ -z "$ARGS" ]
        then
            COVERAGE_RED=1
        fi

        python3 -m coverage html $COVRC -d "$REPORT_DIR" --precision=$PRECISION --skip-covered $OMIT &>>"$LOG"
    else
        [ -n "$COV_INCLUDE" ] && COV_INCLUDE="--include=$COV_INCLUDE"
        python3 -m coverage report $COVRC --precision=$PRECISION $COV_INCLUDE $OMIT
        python3 -m coverage html $COVRC -d "$REPORT_DIR" --precision=$PRECISION --skip-covered $COV_INCLUDE $OMIT &>>"$LOG"
    fi

    rm "$COVERAGE_FILE"

    ASK_LAUNCH=1
fi

# restore performance mode
powerprofilesctl set $OLD_PERF

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
    read -r -t 5
    RES=$?
    if [ $RES -ne 0 ]
    then
        # automatically abort
        echo "^C"
        exit 1
    fi

    echo
    echo "Launching firefox"
    firefox $REPORT_DIR/index.html &>/dev/null &

    echo "Done"
fi

# end of file
