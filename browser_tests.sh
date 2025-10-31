#!/bin/bash

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS=("$@")
#for idx in "${!ARGS[@]}"; do echo "ARGS[$idx]=${ARGS[$idx]}"; done

TEST_DIR="./Site/tmp_test_data"
TEST_DIR_FOTOS_WEBWINKEL="$TEST_DIR/webwinkel"
LOG="/tmp/browser_test_out.txt"
LOG2="/tmp/.browser_test.log"
REPORT_DIR="/tmp/covhtml"
STATIC_DIR="$PWD/Site/.static/"   # must be full path
SETTINGS_AUTOTEST_NODEBUG="Site.settings_autotest_nodebug"
SETTINGS_AUTOTEST_BROWSER="Site.settings_autotest_browser"
COVERAGE_RC="./Site/utils/coverage.rc"
TEST_DATABASE="test_data3"
PYCOV=(-m coverage run --rcfile="$COVERAGE_RC" --append --branch)    # --debug=trace
BG_DURATION=60

# -Wa = enable deprecation warnings
PY_OPTS=(-Wa)

if [ -z "$VIRTUAL_ENV" ]
then
    echo "[ERROR] Virtual environment not activated"
    exit 1
fi

rm -f "$LOG" "$LOG2"
touch "$LOG" "$LOG2"

export PYTHONDONTWRITEBYTECODE=1

# create empty test data directories
rm -rf "$TEST_DIR" &> /dev/null
mkdir "$TEST_DIR"
mkdir "$TEST_DIR_FOTOS_WEBWINKEL"

STAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[INFO] Now is $STAMP"

KEEP_DB=1
MAKE_REPORT=1
ASK_LAUNCH=1
CLEAN_COV=1
FOCUS=""
VERBOSE=0

for arg in "${ARGS[@]}"
do
    # echo "[DEBUG] arg=$arg"

    if [ "$arg" = "-h" ] || [ "$arg" = "--help" ]
    then
        echo "./browser_tests.sh [options]"
        echo ""
        echo "options:"
        echo "  --clean     Remove database (automatic for full run)"
        exit 1

    elif [ "$arg" = "--clean" ]
    then
        KEEP_DB=0

    elif [ "$arg" = "--auto" ]
    then
        # running as sub-test under test.sh
        MAKE_REPORT=0
        ASK_LAUNCH=0
        CLEAN_COV=0
        KEEP_DB=0

    elif [ "$arg" = "-v" ]
    then
        VERBOSE=1

    else
        arg=${arg//\//.}                              # replace all (//) occurrences of / with .
        [ "${arg: -1}" == "." ] && arg=${arg:0:-1}    # strip last . (case: Plein/)
        FOCUS="$arg"
        VERBOSE=1
        echo "[INFO] Focus is set to $FOCUS"
    fi
done

echo "[INFO] Checking application is free of fatal errors"
python3 "${PY_OPTS[@]}" ./manage.py check --tag admin --tag models || exit $?

# voor stand-alone gebruik
# bij aanroep vanuit test.sh is COVERAGE_FILE al gezet
if [ $CLEAN_COV -eq 1 ]
then
    COVERAGE_FILE="/tmp/.coverage.$$"
    export COVERAGE_FILE        # where to write coverage data to
    python3 "${PY_OPTS[@]}" -m coverage erase
fi
# echo "COVERAGE_FILE=$COVERAGE_FILE"

ABORTED=0
if [ $KEEP_DB -ne 1 ]
then
    echo "[INFO] Deleting test database"
    old_pwd="$PWD"
    cd "/tmp" || exit 2
    sudo -u postgres dropdb --if-exists $TEST_DATABASE || exit 1

    echo "[INFO] Creating clean database"
    sudo -u postgres createdb -E UTF8 $TEST_DATABASE || exit 1
    sudo -u postgres psql -d $TEST_DATABASE -q -c 'GRANT CREATE ON SCHEMA public TO django' || exit 1
    cd "$old_pwd" || exit 2

    echo "[INFO] Running migrations"
    # cannot run migrations stand-alone because it will not use the test database
    time python3 -u ./manage.py test --keepdb --noinput --settings="$SETTINGS_AUTOTEST_NODEBUG" -v 2 Plein.tests.test_basics.TestPleinBasics.test_root_redirect
    RES=$?
    [ $RES -eq 0 ] || exit 1
    # echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
fi

echo "[INFO] Refreshing static files"       # (webwinkel foto's, minified js, app static contents, etc.)
[ -d "$STATIC_DIR" ] && rm -rf "$STATIC_DIR"*     # keeps top directory
# note: it is important to use the autotest_browser settings, otherwise instrumentation of JS will not happen
python3 -u "${PYCOV[@]}" ./manage.py collectstatic --settings="$SETTINGS_AUTOTEST_BROWSER" --link
RES=$?
if [ $RES -ne 0 ]
then
    echo "[ERROR] Terminating"
    exit 1
fi

# set high performance
powerprofilesctl set performance

echo "[INFO] Capturing output in $LOG"
# --pid=$$ means: stop when parent stops
# -u = unbuffered stdin/stdout
TAIL_FILE="$LOG2"
[ $VERBOSE -eq 1 ] && TAIL_FILE="$LOG"
tail -f "$TAIL_FILE" --pid=$$ | python -u ./Site/utils/number_tests.py | grep --color -E "FAIL$|ERROR$|" &
PID_TAIL=$(jobs -p | tail -1)
# echo "PID_TAIL=$PID_TAIL"

# flush de database zodat we geen foutmeldingen krijgen over al bestaande records nadat de vorige test afgebroken was
# let op: dit reset NIET de migraties, die blijven gedaan. Statische records aangemaakt door migratie zijn dus weg.
./manage.py flush --database=test --noinput &>>"$LOG"

# start de achtergrondtaken

# start the mail transport service simulator
pkill -f websim_mailer
python3 -u ./Mailer/test_tools/websim_mailer.py &>>"$LOG" &

# start the payment service simulator
echo "[INFO] Starting Mollie simulator" >>"$LOG"
rm -f websim_data.json
pkill -f websim_betaal
python3 -u ./Betaal/test-tools/websim_betaal.py &>>"$LOG" &

# start the google maps simulator
echo "[INFO] Starting Google Maps simulator" >>"$LOG"
pkill -f websim_gmaps
python3 -u ./Locatie/test_tools/websim_gmaps.py &>>"$LOG" &

echo "[INFO] Starting betaal_mutaties (runtime: $BG_DURATION minutes)" >>"$LOG"
pkill -f betaal_mutaties
./manage.py betaal_mutaties --settings="$SETTINGS_AUTOTEST_BROWSER" --use-test-database $BG_DURATION &>>"$LOG" &

echo "[INFO] Starting bestel_mutaties (runtime: $BG_DURATION minutes)" >>"$LOG"
pkill -f bestel_mutaties
./manage.py bestel_mutaties --settings="$SETTINGS_AUTOTEST_BROWSER" --use-test-database $BG_DURATION &>>"$LOG" &

echo "[INFO] Starting competitie_mutaties (runtime: $BG_DURATION minutes)" >>"$LOG"
pkill -f competitie_mutaties
./manage.py competitie_mutaties --settings="$SETTINGS_AUTOTEST_BROWSER" --use-test-database $BG_DURATION &>>"$LOG" &

echo "[INFO] Starting regiocomp_tussenstand (runtime: $BG_DURATION minutes)" >>"$LOG"
pkill -f regiocomp_tussenstand
./manage.py regiocomp_tussenstand --settings="$SETTINGS_AUTOTEST_BROWSER" --use-test-database $BG_DURATION &>>"$LOG" &

echo "[INFO] Starting scheids_mutaties (runtime: $BG_DURATION minutes)" >>"$LOG"
pkill -f scheids_mutaties
./manage.py scheids_mutaties --settings="$SETTINGS_AUTOTEST_BROWSER" --use-test-database $BG_DURATION &>>"$LOG" &

# geef de achtergrondtaken wat tijd om op te starten
sleep 1
echo "" >>"$LOG"

# -u = unbuffered stdin/stdout --> also ensures the order of stdout/stderr lines
# -v = verbose
# note: double quotes not supported around $*
if [ $ABORTED -eq 0 ]
then
    TEST=(./manage.py test --keepdb --noinput --settings="$SETTINGS_AUTOTEST_BROWSER" -v 2)
    if [ -z "$FOCUS" ]
    then
        echo "[INFO] Starting browser tests run" >>"$LOG2"
        python3 -u "${PYCOV[@]}" "${TEST[@]}" "Plein.tests.test_js_in_browser" 2>&1 | tee -a "$LOG" >> "$LOG2"
        RES=${PIPESTATUS[0]}        # status of 'python3' instead of 'tee'
    else
        echo "[INFO] Starting browser tests run for focus_$FOCUS" >>"$LOG2"
        python3 -u "${PYCOV[@]}" "${TEST[@]}" "Plein.tests.test_js_in_browser.TestBrowser.focus_$FOCUS"  2>&1 | tee -a "$LOG" >> "$LOG2"
        RES=${PIPESTATUS[0]}        # status of 'python3' instead of 'tee'
    fi
    [ $RES -eq 3 ] && ABORTED=1
    echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"

    echo >>"$LOG2"
    echo "[INFO] Finished browser tests run" >>"$LOG2"
fi

# stop showing the additions to the logfile, because the rest is less interesting
# use bash construct to prevent the Terminated message on the console
sleep 0.1
kill "$PID_TAIL"
wait "$PID_TAIL" 2>/dev/null

# launch log in editor with log, in case of problems
[ $RES -eq 0 ] || geany --new-instance --no-msgwin "$LOG" &

# cleanup test data directories
[ -d "$TEST_DIR" ] && rm -rf "$TEST_DIR"

# TODO: consider deleting the database, because LiveServerTestCase/TransactionTestCase has flushed all tables

if [ $MAKE_REPORT -eq 1 ] && [ $ABORTED -eq 0 ]
then
    echo "[INFO] Generating reports" | tee -a "$LOG"

    # delete old coverage report
    [ -d "$REPORT_DIR" ] && rm -rf "$REPORT_DIR" &>>"$LOG"

    OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate

    if [ -z "$FOCUS" ]
    then
        python3 -m coverage report --rcfile="$COVERAGE_RC" --include="**/*.js" "$OMIT" 2>&1 | tee -a "$LOG"
        python3 -m coverage html   --rcfile="$COVERAGE_RC" --include="**/*.js" "$OMIT" -d "$REPORT_DIR" &>>"$LOG"
    else
        [ -n "$COV_INCLUDE" ] && COV_INCLUDE="--include=$COV_INCLUDE"
        python3 -m coverage report --rcfile="$COVERAGE_RC" --include="$FOCUS/**/*.js" "$OMIT" 2>&1 | tee -a "$LOG"
        python3 -m coverage html   --rcfile="$COVERAGE_RC" --include="$FOCUS/**/*.js" "$OMIT" -d "$REPORT_DIR" &>>"$LOG"
    fi

    # echo "COVERAGE_FILE=$COVERAGE_FILE"
    # rm "$COVERAGE_FILE"
fi

# kill the background processes
echo "[INFO] Stopping background tasks"
pkill -f regiocomp_tussenstand
pkill -f competitie_mutaties
pkill -f bestel_mutaties
pkill -f betaal_mutaties
pkill -f scheids_mutaties
pkill -f websim_gmaps
pkill -f websim_betaal
pkill -f websim_mailer

# restore performance mode
powerprofilesctl set balanced

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

exit $ABORTED

# end of file
