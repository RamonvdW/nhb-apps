#!/bin/bash

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS=("$@")
#for idx in "${!ARGS[@]}"; do echo "ARGS[$idx]=${ARGS[$idx]}"; done

TEST_DIR="./Site/tmp_test_data"
TEST_DIR_FOTOS_WEBWINKEL="$TEST_DIR/webwinkel"
LOG="/tmp/browser_test_out.txt"
STATIC_DIR="$PWD/Site/.static/"   # must be full path
SETTINGS_AUTOTEST_NODEBUG="Site.settings_autotest_nodebug"
COVERAGE_RC="./Site/utils/coverage.rc"
COVERAGE_FILE="/tmp/.coverage.$$"
DATABASE="test_data3"

# -Wa = enable deprecation warnings
PY_OPTS=(-Wa)

if [ -z "$VIRTUAL_ENV" ]
then
    echo "[ERROR] Virtual environment not activated"
    exit 1
fi

[ -e "$LOG" ] && rm "$LOG"
touch "$LOG"

export PYTHONDONTWRITEBYTECODE=1

# create empty test data directories
rm -rf "$TEST_DIR" &> /dev/null
mkdir "$TEST_DIR"
mkdir "$TEST_DIR_FOTOS_WEBWINKEL"

STAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[INFO] Now is $STAMP"

KEEP_DB=1
FOCUS=""

export COVERAGE_FILE        # where to write coverage data to
python3 "${PY_OPTS[@]}" -m coverage erase

for arg in "${ARGS[@]}"
do
    # echo "[DEBUG] arg=$arg"

    if [[ "$arg" == "-h" || "$arg" == "--help" ]]
    then
        echo "./browser_tests.sh [options]"
        echo ""
        echo "options:"
        echo "  --clean     Remove database (automatic for full run)"
        exit 1

    elif [[ "$arg" == "--clean" ]]
    then
        KEEP_DB=0

    else
        FOCUS="$arg"
    fi
done

echo "[INFO] Checking application is free of fatal errors"
python3 "${PY_OPTS[@]}" ./manage.py check --tag admin --tag models || exit $?

ABORTED=0
if [ $KEEP_DB -ne 1 ]
then
    echo "[INFO] Deleting test database"
    old_pwd="$PWD"
    cd /tmp
    sudo -u postgres dropdb --if-exists $DATABASE || exit 1

    echo "[INFO] Creating clean database"
    sudo -u postgres createdb -E UTF8 $DATABASE || exit 1
    sudo -u postgres psql -d $DATABASE -q -c 'GRANT CREATE ON SCHEMA public TO django' || exit 1
    cd "$old_pwd"

    echo "[INFO] Running migrations"
    # cannot run migrations stand-alone because it will not use the test database
    time python3 -u ./manage.py test --keepdb --noinput --settings=$SETTINGS_AUTOTEST_NODEBUG -v 2 Plein.tests.test_basics.TestPleinBasics.test_quick
    RES=$?
    [ $RES -eq 0 ] || exit 1
    # echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
fi

echo "[INFO] Refreshing static files"       # (webwinkel foto's, minified js, app static contents, etc.)
[ -d "$STATIC_DIR" ] && rm -rf "$STATIC_DIR"*     # keeps top directory
COLLECT=$(./manage.py collectstatic --settings=$SETTINGS_AUTOTEST_NODEBUG --link)
RES=$?
if [ $RES -ne 0 ]
then
    echo "$COLLECT"
    exit 1
fi

# set high performance
powerprofilesctl set performance

echo "[INFO] Capturing output in $LOG"
# --pid=$$ means: stop when parent stops
# -u = unbuffered stdin/stdout
tail -f "$LOG" --pid=$$ | grep --color -E "FAIL$|ERROR$|" &
PID_TAIL=$(jobs -p | tail -1)
# echo "PID_TAIL=$PID_TAIL"

# -u = unbuffered stdin/stdout --> also ensures the order of stdout/stderr lines
# -v = verbose
# note: double quotes not supported around $*
if [ $ABORTED -eq 0 ]
then
    PYCOV=(-m coverage run --rcfile="$COVERAGE_RC" --append --branch --debug=trace)
    TEST=(./manage.py test --keepdb --noinput --settings="$SETTINGS_AUTOTEST_NODEBUG" -v 2)
    if [ -z "$FOCUS" ]
    then
        echo "[INFO] Starting browser tests run" >>"$LOG"
        python3 -u "${PYCOV[@]}" "${TEST[@]}" "Plein.tests.test_js_in_browser" &>>"$LOG"
        RES=$?
    else
        echo "[INFO] Starting browser tests run for focus_$FOCUS" >>"$LOG"
        python3 -u "${PYCOV[@]}" "${TEST[@]}" "Plein.tests.test_js_in_browser.TestBrowser.focus_$FOCUS" &>>"$LOG"
        RES=$?
    fi
    #echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"
    [ $RES -eq 3 ] && ABORTED=1

    echo >>"$LOG"
    echo "[INFO] Finished browser tests run" >>"$LOG"
fi

# stop showing the additions to the logfile, because the rest is less interesting
# use bash construct to prevent the Terminated message on the console
sleep 0.1
kill "$PID_TAIL"
wait "$PID_TAIL" 2>/dev/null

# launch log in editor
[ $RES -eq 0 ] || geany --new-instance --no-msgwin "$LOG" &

# cleanup test data directories
[ -d "$TEST_DIR" ] && rm -rf "$TEST_DIR"

if [ $ABORTED -eq 0 ]
then
    echo "[INFO] Generating reports" | tee -a "$LOG"

    # delete old coverage report
    [ -d "$REPORT_DIR" ] && rm -rf "$REPORT_DIR" &>>"$LOG"

    PRECISION=2     # 2 decimalen achter de komma
    OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate
    JS="*/js/*.js"

    if [ -z "$FOCUS" ]
    then
        python3 -m coverage report --rcfile="$COVERAGE_RC" --precision=$PRECISION --include="$JS" "$OMIT" 2>&1 | tee -a "$LOG"
        python3 -m coverage html --rcfile="$COVERAGE_RC" -d "$REPORT_DIR" --precision=$PRECISION --include="$JS" "$OMIT" &>>"$LOG"
    else

        [ -n "$COV_INCLUDE" ] && COV_INCLUDE="--include=$COV_INCLUDE"
        python3 -m coverage report --rcfile="$COVERAGE_RC" --precision=$PRECISION --include="$JS,$FOCUS/*" "$OMIT" 2>&1 | tee -a "$LOG"
        python3 -m coverage html --rcfile="$COVERAGE_RC" -d "$REPORT_DIR" --precision=$PRECISION --include="$JS,$FOCUS/*" "$OMIT" &>>"$LOG"
    fi

    echo "COVERAGE_FILE=$COVERAGE_FILE"
    #rm "$COVERAGE_FILE"
fi

# restore performance mode
powerprofilesctl set balanced

# end of file
