#!/bin/bash

#  Copyright (c) 2021-2022 Ramon van der Winkel.
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
EXCLUDE+="|site_layout.dtl"
EXCLUDE+="|site_layout_minimaal.dtl"

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

NEW_NR=0
OLD_NR=0
NR=0
for scherm in $SCHERMEN
do
    NR=$((NR + 1))

    grep -q 'class="row-nhb-blauw"' $scherm
    CHECK1=$?
    
    grep -q 'class="nhb-blauw-hoofd"' $scherm
    CHECK2=$?

    grep -q '<h3 class="nhb-rood-text">' $scherm
    CHECK3=$?
    
    if [ $CHECK1 -eq 0 -o $CHECK2 -eq 0 -o $CHECK3 -eq 0 ]
    then
        NEW_NR=$((NEW_NR + 1))
        TYPE='+'
    else
        OLD_NR=$((OLD_NR + 1))
        TYPE='-'
    fi

    if [ $# -ne 0 ]
    then
        echo "$NR: $TYPE $scherm"
    fi
done

if [ $# -ne 0 ]
then
    echo "Run with any argument to enumerate the screens"
fi

echo "Aantal schermen: $AANTAL"
echo "Oud: $OLD_NR"
echo "Nieuw: $NEW_NR"

# end of file
