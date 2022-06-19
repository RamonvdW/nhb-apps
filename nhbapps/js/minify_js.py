# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import sys
import re

""" Comprimeer een javascript file door onnodige spaces, newlines, commentaren, etc.
    te verwijderen. Nog geen obfuscation,
"""


def minify_part(script):
    """ Verwijder commentaar en onnodige spaties uit
        javascript embedded in templates
    """
    # remove block comments
    script = re.sub(r'/\*.*\*/', '', script)

    # remove single-line comments
    script = re.sub(r'//.*\n', '\n', script)

    # remove whitespace at start of the line
    script = re.sub(r'^\s+', '', script)
    script = re.sub(r'\n\s+', '\n', script)

    # remove whitespace at end of the line
    script = re.sub(r'\s+\n', '\n', script)

    # remove newlines
    script = re.sub(r'\n', '', script)

    # remove whitespace around certain operators
    script = re.sub(r' = ', '=', script)
    script = re.sub(r' -= ', '-=', script)
    script = re.sub(r' \+= ', '+=', script)
    script = re.sub(r'\+ ', '+', script)
    script = re.sub(r' \+', '+', script)
    script = re.sub(r' \* ', '*', script)
    script = re.sub(r' :', ':', script)
    script = re.sub(r' == ', '==', script)
    script = re.sub(r' != ', '!=', script)
    script = re.sub(r' === ', '===', script)
    script = re.sub(r' !== ', '!==', script)
    script = re.sub(r' \+ ', '+', script)
    script = re.sub(r' - ', '-', script)
    script = re.sub(r' \? ', '?', script)
    script = re.sub(r' < ', '<', script)
    script = re.sub(r' > ', '>', script)
    script = re.sub(r' / ', '/', script)
    script = re.sub(r' && ', '&&', script)
    script = re.sub(r' \|\| ', '||', script)
    script = re.sub(r' >= ', '>=', script)
    script = re.sub(r' <= ', '<=', script)
    script = re.sub(r', ', ',', script)
    script = re.sub(r': ', ':', script)
    script = re.sub(r'; ', ';', script)
    script = re.sub(r'\) {', '){', script)
    script = re.sub(r'{ ', '{', script)
    script = re.sub(r' \(', '(', script)
    script = re.sub(r'} else', '}else', script)
    script = re.sub(r'else {', 'else{', script)
    script = re.sub(r' }', '}', script)

    return script


def zoek_eind_quote(script, stop_char):
    start = pos = 0
    while start < len(script):
        pos = script.find(stop_char, start)
        if pos > 0 and script[pos-1] == '\\':
            # escaped, dus overslaan
            start = pos+1
        else:
            break   # from the while
    # while
    return pos


def minify_javascript(script):
    """ Doorloop javascript en minify alles behalve strings (rudimentair!)
    """
    # keep the copyright header
    pos = script.find('*/\n')
    clean = script[:pos+3]
    script = script[pos+3:]

    while len(script):
        # zoek strings zodat we die niet wijzigen
        pos_sq = script.find('"')
        pos_dq = script.find("'")

        if pos_sq >= 0 and pos_dq >= 0:
            pos_q = min(pos_sq, pos_dq)  # both not -1 --> take first, thus min
        else:
            pos_q = max(pos_sq, pos_dq)  # either one is -1 --> take max, thus the positive one

        # zoek commentaar zodat we geen quotes in commentaar pakken /* can't */
        pos_sc = script.find('//')      # single line comment
        pos_bc = script.find('/*')      # block comment

        if pos_sc >= 0 and pos_bc >= 0:
            pos_c = min(pos_sc, pos_bc)  # both not -1 --> take first, thus min
        else:
            pos_c = max(pos_sc, pos_bc)  # either one is -1 --> take max, thus the positive one

        if pos_c >= 0 and pos_q >= 0:
            # zowel quote and commentaar
            if pos_c < pos_q:
                # commentaar komt eerst

                # verwerk het stuk script voordat het commentaar begint
                pre_comment = script[:pos_c]
                clean += minify_part(pre_comment)
                script = script[pos_c:]

                # verwijder het commentaar
                if pos_c == pos_sc:
                    # verwijder single-line comment
                    pos = script.find('\n')
                    if pos > 0:
                        script = script[pos+1:]
                else:
                    # verwijder block comment
                    pos = script.find('*/')
                    if pos > 0:
                        script = script[pos+2:]

                # opnieuw evalueren
                continue

        if pos_q >= 0:
            pre_string = script[:pos_q]
            clean += minify_part(pre_string)

            stop_char = script[pos_q]
            script = script[pos_q+1:]         # kap pre-string en quote eraf
            pos = zoek_eind_quote(script, stop_char)
            clean += stop_char              # open char
            clean += script[:pos+1]         # kopieer string inclusief stop-char

            script = script[pos+1:]
        else:
            clean += minify_part(script)
            script = ""
    # while

    return clean


def convert_javascript(infile, outfile):
    print('[INFO] loading %s' % repr(infile))
    contents = open(infile, 'r').read()

    new_contents = minify_javascript(contents)

    print('[INFO] writing %s' % repr(outfile))
    open(outfile, 'w').write(new_contents)


if len(sys.argv) < 3:
    print("usage: %s infile outfile" % sys.argv[0])
else:
    infile = sys.argv[1]
    outfile = sys.argv[2]
    convert_javascript(infile, outfile)

# end of file
