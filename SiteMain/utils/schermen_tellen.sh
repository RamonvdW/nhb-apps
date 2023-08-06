#!/bin/bash

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

EXCLUDE="plein/menu-"
EXCLUDE+="|plein/site-layout"
EXCLUDE+="|feedback/sidebar.dtl"
EXCLUDE+="|plein/card"
EXCLUDE+="|plein/ga-naar-live-server.dtl"
EXCLUDE+="|plein/andere-sites.dtl"
EXCLUDE+="|logboek/common"
EXCLUDE+="|competitie/menu.dtl"
EXCLUDE+="|site_layout.dtl"
EXCLUDE+="|site_layout_minimaal.dtl"
EXCLUDE+="|webwinkel/card_product.dtl"
EXCLUDE+="|vhpg-tekst.dtl"
EXCLUDE+="|snippets.dtl"

INCLUDES=$(grep -- '{% include' */templates/*/*dtl | grep -vE "$EXCLUDE")
RES=$?
if [ $RES -eq 0 ]
then
    echo "---"
    echo "$INCLUDES"
    echo "---"
    echo "EXCLUDE uitbreiden met bovenstaande"
    exit
fi

SCHERMEN=$(find ./*/templates -name \*dtl | grep -vE "$EXCLUDE")
AANTAL=$(echo "$SCHERMEN" | wc -w)

NR=0
for scherm in $SCHERMEN
do
    NR=$((NR + 1))
    if [ $# -ne 0 ]
    then
        echo "$NR: $scherm"
    fi
done

if [ $# -ne 0 ]
then
    echo "Run with any argument to enumerate the screens"
fi

echo "Aantal schermen: $AANTAL"

# end of file
