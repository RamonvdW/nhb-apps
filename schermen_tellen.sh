#!/bin/bash

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

EXCLUDE="plein/menu-"
EXCLUDE+="|plein/site-layout"
EXCLUDE+="|overig/site-feedback-sidebar.dtl"
EXCLUDE+="|plein/card"
EXCLUDE+="|plein/ga-naar-live-server.dtl"
EXCLUDE+="|plein/andere-sites-van-de-nhb.dtl"
EXCLUDE+="|logboek/common"
EXCLUDE+="|competitie/tijdlijn"
EXCLUDE+="|competitie/menu.dtl"
EXCLUDE+="|handleiding/menu.dtl"

INCLUDES=$(grep '{% include' */templates/*/*dtl | grep -vE "$EXCLUDE")
RES=$?
if [ $RES -eq 0 ]
then
    echo "---"
    echo "$INCLUDES"
    echo "---"
    echo "EXCLUDE uitbreiden met bovenstaande"
    exit
fi

SCHERMEN=$(ls -1 */templates/*/*dtl | grep -vE "$EXCLUDE")
AANTAL=$(echo $SCHERMEN | wc -w)

if [ $# -ne 0 ]
then
    NR=0
    for scherm in $SCHERMEN
    do
        NR=$((NR + 1))
        echo "$NR: $scherm"
    done
else
    echo "Run with any argument to enumerate the screens"
fi

echo "Aantal schermen: $AANTAL"

# end of file
