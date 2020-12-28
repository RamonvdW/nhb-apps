#!/bin/bash

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# helper to check the uniqueness of the "op_pagina" for the feedback form

DTL_INCLUDES=$(echo "/menu.dtl /andere-sites-van-de-nhb.dtl /site_layout.dtl /card.dtl /card_logo.dtl /ga-naar-live-server.dtl" | tr ' ' '|')
DTL_BEWUST_NIET=$(echo "/niet-ondersteund.dtl /site-feedback- /tijdelijke-url- /Logboek/ /Handleiding/" | tr ' ' '|')

DTL_FILES=$(find . -name \*.dtl | grep -vE "$DTL_BEWUST_NIET" | grep -vE "$DTL_INCLUDES")

grep "with op_pagina" $DTL_FILES | cut -d':' -f2 | grep -E '^{' | cut -d' ' -f5 | sort | uniq -c | sort -n

echo "[DEBUG] Geen 'op_pagina':"
grep -L "with op_pagina" $DTL_FILES

# end of file
