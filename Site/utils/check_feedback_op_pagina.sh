#!/bin/bash

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# helper to check the uniqueness of the "op_pagina" for the feedback form

DTL_INCLUDES=$(echo "/menu.dtl /andere-sites.dtl /site_layout.dtl /site_layout_minimaal.dtl /site_layout_favicons /site_layout_fonts /fout_403.dtl /fout_404.dtl /fout_500.dtl /card_icon.dtl /card_logo.dtl /card_icon_beschikbaar-vanaf /card_logo_beschikbaar-vanaf /ga-naar-live-server.dtl /card_product.dtl /card_niet-beschikbaar /tijdlijn.dtl /vhpg-tekst.dtl" | tr ' ' '|')
DTL_BEWUST_NIET=$(echo "/templates/email Site/templates/snippets.dtl /plein-bezoeker.dtl /niet-ondersteund.dtl /feedback/ tijdelijkecodes/code- /Logboek/ /records_specifiek.dtl /registreer-gast.dtl /registreer-normaal.dtl plein/test-" | tr ' ' '|')

DTL_FILES=$(find . -name \*.dtl | grep -vE "$DTL_BEWUST_NIET" | grep -vE "$DTL_INCLUDES")

COUNT=$(ls -1 $DTL_FILES | wc -l)
echo "[DEBUG] $COUNT templates met op_pagina:"

ALL=' 1 op_pagina'
[ $# -gt 0 ] && ALL='@@@@@'

grep "with op_pagina" $DTL_FILES | cut -d':' -f2 | tr ' ' '\n' | grep op_pagina | sort | uniq -c | sort -n | grep -v "$ALL"

for dtl in $DTL_FILES;
do
  AppName=$(echo "$dtl" | cut -d/ -f2)
  app_name=${AppName,,}
  verwacht="op_pagina=\"$app_name-"
  grep -q "$verwacht" "$dtl"
  RES=$?
  if [ $RES -ne 0 ]
  then
      # instaptoets heeft een op_pagina die gezet wordt door de view, om de vraag te reflecteren
      # voorkom dat we deze melden
      grep -q "<!-- disable check op_pagina -->" "$dtl" || echo "[WARNING] $verwacht niet gevonden in $dtl"
  fi
done

[ $# -gt 0 ] || echo "Gebruik -v om alles te krijgen"

echo "[DEBUG] Geen 'op_pagina':"
grep --files-without-match "with op_pagina" $DTL_FILES

# end of file
