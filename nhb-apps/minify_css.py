# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Zorg voor compacte webpagina's door onnodige spaties en newlines
    te verwijderen uit de een css file
"""

import sys
import re

# TODO: zoek uit of het minder cpu kost als de reg-exps gecompileerd worden
# TODO: zoek uit of het minder cpu kost als de reg-exps gecombineerd worden
# (re.compile)


def minify_css_contents(contents):
    clean = ""
    pos = contents.find('/*')
    while len(contents) and pos >= 0:
        pos2 = contents.find('*/')
        if pos2 > pos:
            # remove this block comment
            clean += contents[:pos]
            contents = contents[pos2+2:]
        else:
            # wel begin maar geen einde --> geef het op
            break
        pos = contents.find('/*')
    # while
    clean += contents

    # remove all newlines
    clean = re.sub(r'\n', '', clean)

    # remove whitespace after colon, semi-colon and comma
    clean = re.sub(r':\s+', ':', clean)
    clean = re.sub(r';\s+', ';', clean)
    clean = re.sub(r',\s+', ',', clean)

    # remove whitespace before and after after curly brace
    clean = re.sub(r'\s*}\s*', '}', clean)
    clean = re.sub(r'\s*{\s*', '{', clean)

    # remove semicolon before curly brace
    #TODO: TEST if still functional
    # clean = re.sub(r';}', '}', clean)

    return clean


def process(src_fname, dst_fname):
    # read
    contents = open(src_fname, "r").read()
    # modify
    contents = minify_css_contents(contents)
    # write
    open(dst_fname, "w").write(contents)


# program entry point
if len(sys.argv) == 3:
    infile = sys.argv[1]
    outfile = sys.argv[2]
    process(infile, outfile)

# end of file
