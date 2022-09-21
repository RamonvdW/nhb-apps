#!/bin/bash

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# helper to check the uniqueness of the "op_pagina" for the feedback form

DTL_INCLUDES=$(echo "/menu.dtl /andere-sites-van-de-nhb.dtl /site_layout.dtl /site_layout_minimaal.dtl /fout_403.dtl /fout_404.dtl /fout_500.dtl /competitie/tijdlijn.dtl /card.dtl /card_logo.dtl /card_nog-niet-beschikbaar /card_logo_nog-niet-beschikbaar /ga-naar-live-server.dtl" | tr ' ' '|')
DTL_BEWUST_NIET=$(echo "/templates/email nhbapps/templates/snippets.dtl /plein-bezoeker.dtl /niet-ondersteund.dtl /feedback/ /tijdelijke-url- /Logboek/ /Handleiding/ /templates/plein/menu- /account/login-as-zoek.dtl /account/bevestigd.dtl /sporter/registreer-nhb-account.dtl" | tr ' ' '|')

DTL_FILES=$(find . -name \*.dtl | grep -vE "$DTL_BEWUST_NIET" | grep -vE "$DTL_INCLUDES")

COUNT=$(ls -1 $DTL_FILES | wc -l)
echo "[DEBUG] $COUNT templates met op_pagina:"

ALL=' 1 op_pagina'
[ $# -gt 0 ] && ALL='@@@@@'

grep "with op_pagina" $DTL_FILES | cut -d':' -f2 | tr ' ' '\n' | grep op_pagina | sort | uniq -c | sort -n | grep -v "$ALL"

[ $# -gt 0 ] || echo "Gebruik -v om alles te krijgen"

echo "[DEBUG] Geen 'op_pagina':"
grep -L "with op_pagina" $DTL_FILES

# end of file
