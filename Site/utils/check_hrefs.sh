#!/bin/bash

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# check of URLs hard-coded into the templates and the settings

check_url() {
    URL="$1"
    # first line is "HTTP/2 200 "
    RES=$(curl -is "$URL" | head -n 1 | cut -d\  -f2)
    if [ "$RES" = "200" ]
    then
        echo "[OK]  $URL"
    else
        echo "[NOK] $URL (HTTP status $RES)"
    fi
}

for url in $(find Site -type f -name \*py -exec grep -Hn 'https://www.handboogsport.nl' {} \; | cut -d\' -f2);
do
    # note: this also matches on commented out line, but that is fine
    check_url "$url"
done

for url in $(find . -type f -name \*dtl -exec grep 'https://www.handboogsport' {} \; | tr ' ' \\n | grep https | cut -d\" -f2)
do
    check_url "$url"
done

# end of file
