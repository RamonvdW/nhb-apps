#!/bin/bash

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

ARGS=("$@")
#for idx in "${!ARGS[@]}"; do echo "ARGS[$idx]=${ARGS[$idx]}"; done

COV_AT_LEAST=96.80
RED="\e[31m"
RESET="\e[0m"
TEST_DIR="./Site/tmp_test_data"
TEST_DIR_FOTOS_WEBWINKEL="$TEST_DIR/webwinkel"
REPORT_DIR="/tmp/covhtml"
LOG="/tmp/test_out.txt"
TMP_HTML="/tmp/tmp_html/"             # used by e2e_open_in_browser()
STATIC_DIR="$PWD/Site/.static/"   # must be full path
SETTINGS_AUTOTEST="Site.settings_autotest"
SETTINGS_AUTOTEST_NODEBUG="Site.settings_autotest_nodebug"
COVERAGE_RC="./Site/utils/coverage.rc"
COVERAGE_FILE="/tmp/.coverage.$$"
TEST_DATABASE="test_data3"

# -Wa = enable deprecation warnings
PY_OPTS=(-Wa)

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

COVRC="--rcfile=$COVERAGE_RC"
PYCOV=(-m coverage run "$COVRC" --append --branch)       # --pylib
[ -n "$COV_INCLUDE_3RD_PARTY" ] && PYCOV+=(--include="*${COV_INCLUDE_3RD_PARTY}*")

export PYTHONDONTWRITEBYTECODE=1

OMIT="--omit=*/lib/python3*/site-packages/*"    # use , to separate

# kill the simulators, if still running in the background
# -f check entire commandline program name is python and does not match
pgrep -f websim > /dev/null
RES=$?
if [ $RES -eq 0 ]
then
    echo "[WARNING] simulators found running - cleaning up now"
    pkill -f websim
fi

FORCE_REPORT=0
FORCE_FULL_COV=0
KEEP_DB=1
TEST_ALL=0

FOCUS_ARGS=()
for arg in "${ARGS[@]}"
do
    # echo "[DEBUG] arg=$arg"

    if [ "$arg" = "-h" ] || [ "$arg" = "--help" ]
    then
        echo "./test.sh [options] [testcase selector(s)]"
        echo ""
        echo "options:"
        echo "  --force     Force generate of coverage, even when tests fail"
        echo "  --fullcov   Do not focus the coverage report"
        echo "  --clean     Remove database (automatic for full run)"
        echo
        echo "Example selector: App_dir.tests_dir.test_filename.TestCaseClass.test_func"

        exit 1

    elif [ "$arg" = "--force" ]
    then
        echo "[INFO] Forcing coverage report"
        FORCE_REPORT=1
        # remove from ARGS used to decide focus
        # will still be given to ./manage.py where --force has no effect

    elif [ "$arg" = "--fullcov" ]
    then
        echo "[INFO] Forcing full coverage report"
        FORCE_FULL_COV=1
        # remove from ARGS used to decide focus
        # will still be given to ./manage.py where --fullcov has no effect

    elif [ "$arg" = "--clean" ]
    then
        KEEP_DB=0
        # remove from ARGS used to decide focus
        # will still be given to ./manage.py where --clean has no effect

    else
        # convert a path to a module or test.py file into a test case
        arg=${arg//\//.}                              # replace all (//) occurrences of / with .
        [ "${arg: -1}" == "." ] && arg=${arg:0:-1}    # strip last . (case: Plein/)
        arg=${arg/.py/}                               # strip .py at the end

        FOCUS_ARGS+=("$arg")
    fi
done

FOCUS=""
FOCUS_SPECIFIC_TEST=0
if [ ${#FOCUS_ARGS[@]} -eq 0 ]
then
    # no args = test all = remove database
    KEEP_DB=0
    TEST_ALL=1
    COV_INCLUDE=""
else
    echo "[INFO] Focus arguments: \"${FOCUS_ARGS[*]}\" (${#FOCUS_ARGS[@]} arguments)"

    # convert Function.testfile.TestCase.test_functie into "Function"
    # also works for just "Function"
    FOCUS1=""
    for arg in "${FOCUS_ARGS[@]}";
    do
        [[ "$arg" == *".tests."* ]] && FOCUS_SPECIFIC_TEST=1
        clean_focus=$(echo "$arg" | cut -d'.' -f1)
        FOCUS1="$clean_focus $FOCUS1"
    done

    # support Func1 Func2 by converting to "Func1, Func2"
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
    # note: uses standard database, not test database
    python3 "${PY_OPTS[@]}" ./manage.py check --tag admin --tag models || exit $?
fi

export COVERAGE_FILE        # where to write coverage data to
python3 "${PY_OPTS[@]}" -m coverage erase

if [ $TEST_ALL -eq 1 ]
then
    # collect browser coverage at start of test-all
    echo "[INFO] Running JS browser tests"
    ./browser_tests.sh --auto
fi

# create empty test data directories
rm -rf "$TEST_DIR" &> /dev/null
mkdir "$TEST_DIR"
mkdir "$TEST_DIR_FOTOS_WEBWINKEL"

STAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[INFO] Now is $STAMP"

echo "[INFO] Refreshing static files"
# with minification (purely for coverage)
[ -d "$STATIC_DIR" ] && rm -rf "$STATIC_DIR"*     # keeps top directory
COLLECT=$(python3 -u "${PYCOV[@]}" ./manage.py collectstatic --link --settings "$SETTINGS_AUTOTEST_NODEBUG")
# without minification
[ -d "$STATIC_DIR" ] && rm -rf "$STATIC_DIR"*     # keeps top directory
COLLECT=$(python3 -u "${PYCOV[@]}" ./manage.py collectstatic --link --settings "$SETTINGS_AUTOTEST")
RES=$?
if [ $RES -ne 0 ]
then
    echo "$COLLECT"
    exit 1
fi

# create a link from /tmp/static to the actual static dir
# used to load static content from html written by e2e_open_in_browser()
[ -d "$TMP_HTML" ] && rm -rf "$TMP_HTML"
mkdir -p "$TMP_HTML"
ln -s "$STATIC_DIR" "$TMP_HTML/static"

ABORTED=0

# controleer dat de database niet kapot gemaakt is door de browser tests
if [ $KEEP_DB -eq 1 ]
then
    echo "[INFO] Checking database consistency"
    count=$(echo 'SELECT COUNT(*) FROM "BasisTypen_boogtype"' | python3 ./manage.py dbshell --database test | grep 'row)' --before=1 | head -1)
    count=$((count + 0))
    if [ $count -lt 17 ]
    then
        echo "[WARNING] Detected inconsistent database (aantal boogtypen: $count)"
        echo "[WARNING] Forcing database cleaning"
        KEEP_DB=0
    fi
fi

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

    echo "[INFO] Running migrations and performing run with nodebug"
    # ..and add coverage with no-debug
    # -v 2 shows progress of migrations
    python3 -u "${PY_OPTS[@]}" "${PYCOV[@]}" ./manage.py test --keepdb --noinput --settings=$SETTINGS_AUTOTEST_NODEBUG -v 2 Plein.tests.test_basics.TestPleinBasics.test_quick
    RES=$?
    [ $RES -eq 0 ] || ABORTED=1
    # echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"

    echo "[INFO] Running manage.py exit test"
    # trigger diff that generates exit code
    ./manage.py shell -c 'from ImportCRM.models import ImportLimieten as L; l = L.objects.first(); l.max_club_changes=1; l.save()' &>>"$LOG"
    python3 -u "${PY_OPTS[@]}" "${PYCOV[@]}" ./manage.py diff_crm_jsons --settings=$SETTINGS_AUTOTEST ./ImportCRM/test-files/testfile_19.json ./ImportCRM/test-files/testfile_23.json &>/dev/null
    RES=$?
    [ $RES -ne 0 ] || ABORTED=1
    # echo "[DEBUG] Debug run result: $RES --> ABORTED=$ABORTED"
fi

echo "[INFO] Starting websim tasks"

# start the mail transport service simulator
python3 -u "${PY_OPTS[@]}" ./Mailer/test_tools/websim_mailer.py &
PID_WEBSIM1=$!

# start the payment service simulator
python3 -u "${PY_OPTS[@]}" ./Betaal/test-tools/websim_betaal_test.py &
PID_WEBSIM2=$!

# start the google maps simulator
python3 -u "${PY_OPTS[@]}" ./Locatie/test_tools/websim_gmaps.py &
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

echo "[INFO] Capturing output in $LOG"
# --pid=$$ means: stop when parent stops
# -u = unbuffered stdin/stdout
tail -f "$LOG" --pid=$$ | python -u ./Site/utils/number_tests.py | grep --color -E "FAIL$|ERROR$|" &
PID_TAIL=$(jobs -p | tail -1)
# echo "PID_TAIL=$PID_TAIL"

# set high performance
powerprofilesctl set performance

# -u = unbuffered stdin/stdout --> also ensures the order of stdout/stderr lines
# -v = verbose
# note: double quotes not supported around $*
if [ $ABORTED -eq 0 ]
then
    echo "[INFO] Starting main test run" >>"$LOG"
    python3 "${PY_OPTS[@]}" -u "${PYCOV[@]}" ./manage.py test --keepdb --settings=$SETTINGS_AUTOTEST --exclude-tag=browser -v 2 "${FOCUS_ARGS[@]}" &>>"$LOG"
    RES=$?
    #echo "[DEBUG] Run result: $RES --> ABORTED=$ABORTED"
    [ $RES -eq 3 ] && ABORTED=1

    echo >>"$LOG"
    echo "[INFO] Finished main test run" >>"$LOG"

    # launch a browser with all the stored web pages
    find "$TMP_HTML" -type f | grep -q html
    RES2=$?
    # echo "[DEBUG] RES=$RES"
    if [ $RES2 -eq 0 ]
    then
        #  %T@ is modification time; %p is filename
        IFS=" " read -r -a HTML_FILES < <(find "$TMP_HTML" -type f -name '*html' -printf '%T@ %p\n' | cut -d' ' -f2 | tr '\n' ' ')
        echo "HTML_FILES: ${HTML_FILES[*]}"
        firefox "${HTML_FILES[@]}" &
    fi
fi

# stop showing the additions to the logfile, because the rest is less interesting
# use bash construct to prevent the Terminated message on the console
sleep 0.1
kill "$PID_TAIL"
wait "$PID_TAIL" 2>/dev/null

# launch log in editor
[ $RES -eq 0 ] || geany --new-instance --no-msgwin "$LOG" &

if [ $ABORTED -eq 0 ]
then
    if [ $RES -eq 0 ] && [ "$FOCUS" != "" ] && [ $FOCUS_SPECIFIC_TEST -eq 0 ]
    then
        echo "[INFO] Discovering all management commands in $FOCUS"
        for cmd in $(python3 ./manage.py --help);
        do
            if [ -f "$FOCUS/management/commands/$cmd.py" ]
            then
                echo -n '.'
                echo "[INFO] ./manage.py help $cmd" >>"$LOG"
                python3 "${PY_OPTS[@]}" -u "${PYCOV[@]}" ./manage.py help --settings="$SETTINGS_AUTOTEST" "$cmd" &>>"$LOG"
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
            python3 "${PY_OPTS[@]}" -u "${PYCOV[@]}" ./manage.py help "$cmd" --settings="$SETTINGS_AUTOTEST" &>>/dev/null    # ignore output
        done
        echo
    fi
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
[ -d "$TEST_DIR" ] && rm -rf "$TEST_DIR"

ASK_LAUNCH=0
COVERAGE_RED=0

if [ $ABORTED -eq 0 ] || [ $FORCE_REPORT -eq 1 ]
then
    if [ -e "/tmp/browser_js_cov.json" ]
    then
        # import the JS coverage data
        echo "[INFO] Importing coverage from browser tests (/tmp/browser_js_cov.json)"
        python3 "${PY_OPTS[@]}" -u "${PYCOV[@]}" ./manage.py test --keepdb --settings="$SETTINGS_AUTOTEST" -v 0 "Plein.tests.test_import_js_cov.TestPleinImportJsCov.import_js_cov"
    fi

    echo "[INFO] Generating reports" | tee -a "$LOG"

    # delete old coverage report
    [ -d "$REPORT_DIR" ] && rm -rf "$REPORT_DIR" &>>"$LOG"

    if [ -z "$FOCUS" ] || [ $FORCE_FULL_COV -ne 0 ]
    then
        python3 -m coverage report $COVRC --skip-covered --fail-under=$COV_AT_LEAST "$OMIT" 2>&1 | tee -a "$LOG"
        if [[ ${PIPESTATUS[0]} -gt 0 ]] && [[ ${#FOCUS_ARGS[@]} -eq 0 ]]
        then
            COVERAGE_RED=1
        fi

        python3 -m coverage html $COVRC -d "$REPORT_DIR" --skip-covered "$OMIT" &>>"$LOG"
    else
        [ -n "$COV_INCLUDE" ] && COV_INCLUDE="--include=$COV_INCLUDE"
        python3 -m coverage report $COVRC "$COV_INCLUDE" "$OMIT"
        python3 -m coverage html $COVRC -d "$REPORT_DIR" --skip-covered "$COV_INCLUDE" "$OMIT" &>>"$LOG"
    fi

    rm "$COVERAGE_FILE"

    ASK_LAUNCH=1
fi

# restore performance mode
powerprofilesctl set balanced

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
    if [ $RES -eq 0 ]
    then
        echo
        echo "Launching firefox"
        firefox $REPORT_DIR/index.html &>/dev/null &
        echo "Done"
    else
        # automatically abort
        echo "^C"
        exit 1
    fi
fi

# end of file
