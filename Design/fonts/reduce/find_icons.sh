#!/bin/bash

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# ga naar de directory van het script in ~/Plein/fonts/reduce
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

# ga naar de top directory van het project
cd ../../.. || exit 1

OUT="Design/fonts/reduce/needed-glyphs_material-symbols.txt"
HANDLED='@@@'   # dummy, to allow concatenation

OUT_TMP="/tmp/find_icons.txt"
rm -f "$OUT_TMP"
touch "$OUT_TMP"

echo "[INFO] Searching for icons in templates and sources"
grep material-symbol -- */templates/*/*dtl | grep -vE "secondary-content|subset-mh" | sed -s 's/material-symbol/@/' | cut -d@ -f2- | cut -d\> -f2- | sed -s 's#</i#@#' | cut -d@ -f1 >> "$OUT_TMP"

# handle include 'plein/card_..' icon="xxx"
grep icon= -- */templates/*/*dtl | sed 's/icon=/@/' | cut -d@ -f2 | cut -d\" -f2 >> "$OUT_TMP"
HANDLED+="|{{ icon }}"       # in Plein/templates/plain/card_*dtl

# handle {{ korting.icon_name }}
# handle icon/icoon gezet in view
find . -name \*py ! -name models.py ! -name test_asserts.py -exec grep -E 'icon=|icoon=|icon =|icoon =|icon_name' {} \+ | grep -v 'admin_list._boolean_icon' | cut -d= -f2- | tr \" \' | cut -d\' -f2 >> "$OUT_TMP"
HANDLED+="|kaartje.icon|kaartje.icoon|ander.icoon|{{ korting.icon_name }}"

# dynamische icons vanuit script
grep set_collapsible_icon\(id, Overig/js/collapsible_icons.js | tr \" \' |cut -d\' -f2 >> "$OUT_TMP"

# icons vanuit de Records module, eervolle vermeldingen
./manage.py shell --no-imports -c 'from Records.models import AnderRecord; qset=AnderRecord.objects.values_list("icoon", flat=True); print("\n".join(qset))' | grep -vE "^$" >> "$OUT_TMP"

echo "[INFO] Checking for missed situations"
grep -vE "$HANDLED" "$OUT_TMP" | sort -u > "$OUT"
rm "$OUT_TMP"
grep -E '{{|}' "$OUT"       # typical in template files

COUNT=$(wc -l < "$OUT")
echo "[INFO] Found $COUNT icons, see $OUT"

# end of file
