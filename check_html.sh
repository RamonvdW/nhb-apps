#!/bin/bash

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# retrieve a few html pages and check if html is tidy

SERVER="localhost:80"

PAGES='
/
/plein/
/plein/privacy/
/records/record-OD-1/
/records/zoek/
/records/zoek/?zoekterm=schijndel
/account/login/
/account/registreer/
/account/uitgelogd/
/account/wachtwoord-vergeten/
/overig/feedback/plus/plein/
/overig/feedback/inzicht/
'
#/hist/
#/hist/2010-2011/18/Recurve/indiv/

TMPDIR="/tmp/check_html"
CURL_OPTIONS="-sL --max-redirs 5"
TIDY_OPTIONS="-qi --wrap 200 --doctype html5 --strict-tags-attributes yes"
TIDY_ISSUES="$TMPDIR/tidy_issues"
TIDY_ISSUES_CLEANED="$TIDY_ISSUES".cleaned

rm -rf "$TMPDIR"
mkdir "$TMPDIR"

nr=0
for page in $PAGES
do
    nr=$((nr + 1))
    file_cache="$TMPDIR/page_$nr.html"
    file_pretty="$TMPDIR/page_$nr.pretty.html"
    curl $CURL_OPTIONS "$SERVER$page" -o "$file_cache"
    RES=$?
    if [ $RES -ne 0 ]
    then
        echo "Curl exit code $RES for $SERVER$page"
        exit 1
    else
        grep -q "Django tried these URL patterns" "$file_cache"
        if [ $? -eq 0 ]
        then
            echo "## ERROR ## BAD URL: $page"
        else
            # voeg wat newlines toe om het leesbaarder te maken
            sed 's#</#\n</#g' "$file_cache" > "$file_pretty"
            echo "Checking $file_pretty containing $page"
            tidy $TIDY_OPTIONS -o /dev/null -f "$TIDY_ISSUES" "$file_pretty"
            if [ $? -ne 0 ]
            then
                # suppress some warnings
                cat "$TIDY_ISSUES" | grep -v 'Warning: <input> proprietary attribute "minlength"' > "$TIDY_ISSUES_CLEANED"
                # anything left to show?
                LC=$(cat "$TIDY_ISSUES_CLEANED" | wc -l)
                if [ $LC -ne 0 ]
                then
                    echo "-----------------------------------"
                    cat $TIDY_ISSUES_CLEANED
                    echo "-----------------------------------"
                    echo
                fi
            fi
        fi
    fi
done

# end of file

