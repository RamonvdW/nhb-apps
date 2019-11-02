# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# importeer individuele competitie historie

import argparse
from django.core.management.base import BaseCommand

# https://unicode-table.com/
APPROVED_UNICODE_CHARS = (
    214,  # Ö
    216,  # Ø
    220,  # Ü
    224,  # à
    225,  # á
    228,  # ä
    229,  # å
    231,  # ç
    232,  # è
    233,  # é
    235,  # ë
    238,  # î
    239,  # ï
    243,  # ó
    244,  # ô
    246,  # ö
    248,  # ø
    252,  # ü
)


def check_unexpected_utf8(txt):
    """ check a string for unexpected bytes, hinting at non-utf8 files """
    for char in txt:
        char_nr = ord(char)  # decodes unicode to character value
        if not ((32 <= char_nr < 128) or char_nr in APPROVED_UNICODE_CHARS):
            print("[WARNING] Suspicious non-utf8: %s (char nr %s)" % (txt.encode(), char_nr))
    # for


# end of file

