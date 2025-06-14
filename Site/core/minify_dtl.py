# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Zorg voor compacte webpagina's door onnodige spaties en newlines
    te verwijderen uit de templates bij het inladen.

    Inladen gebeurt eenmalig na het starten van de applicatie.
    Let op: dit is vOOr expansie van tags en die kunnen whitespace toevoegen
"""

# credits to martinsvoboda for a good example       # noqa

from django.conf import settings
from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
import re


def minify_js(script):
    """ Remove unnecessary comments, spaces and newlines from javascript """

    clean = ''

    # remove single-line comments
    script = re.sub(r'//.*\n', '\n', script)

    # remove block-comments
    # script = re.sub(re.compile(r'/\*.*?\*/', re.DOTALL), '', script)    # ? = non-greedy

    # zoek naar string, zodat we die over kunnen slaan
    in_quotes = ""
    while len(script) > 0:

        if script[0] in ("'", '"'):
            in_quotes = script[0]
            script = script[1:]
            clean += in_quotes

        if in_quotes != '':
            # op zoek naar het einde van de quotes
            pos = script.find(in_quotes)
            if pos < 0:  # pragma: no branch
                # on-gebalanceerde quotes
                pos = len(script)  # pragma: no cover

            clean += script[:pos + 1]
            script = script[pos + 1:]
            in_quotes = ''
        else:
            # zoek het begin van een nieuwe quoted sectie
            pos1 = script.find("'")
            pos2 = script.find('"')

            if pos1 >= 0:
                if pos2 < 0:
                    pos = pos1
                else:
                    pos = min(pos1, pos2)
            else:
                pos = pos2

            if pos < 0:
                # geen quote meer gevonden, dus neem alles
                deel = script
                script = ''
            else:
                deel = script[:pos]
                script = script[pos:]

            # remove whitespace at start and end of the line
            deel = re.sub(r'\n\s+', '\n', deel)
            deel = re.sub(r'\s+\n', '\n', deel)
            deel = deel.strip()

            # remove whitespace around operators
            # let op: deze tekens hebben speciale betekenis voor regexp en moeten escaped worden: /*+?.|()[]{}\
            deel = re.sub(r' = ', '=', deel)
            deel = re.sub(r' == ', '==', deel)
            deel = re.sub(r' != ', '!=', deel)
            deel = re.sub(r' === ', '===', deel)
            deel = re.sub(r' !== ', '!==', deel)
            deel = re.sub(r' \+ ', '+', deel)
            deel = re.sub(r' \+= ', '+=', deel)
            deel = re.sub(r' - ', '-', deel)
            deel = re.sub(r' -= ', '-=', deel)
            deel = re.sub(r' < ', '<', deel)
            deel = re.sub(r' && ', '&&', deel)
            deel = re.sub(r' => ', '=>', deel)
            deel = re.sub(r' > ', '>', deel)
            deel = re.sub(r' < ', '<', deel)
            deel = re.sub(r', ', ',', deel)
            deel = re.sub(r': ', ':', deel)
            deel = re.sub(r'; ', ';', deel)
            deel = re.sub(r' \(', '(', deel)
            deel = re.sub(r'\) ', ')', deel)
            deel = re.sub(r'\{ ', '{', deel)
            deel = re.sub(r' }', '}', deel)

            # remove unnecessary newlines
            deel = re.sub(r'\n\{', '{', deel)
            deel = re.sub(r'\{\n', '{', deel)
            deel = re.sub(r'\n}', '}', deel)
            deel = re.sub(r'}\n', '}', deel)  # breekt javascript als er een ; ontbreekt!
            deel = re.sub(r';\n', ';', deel)
            deel = re.sub(r',\n', ',', deel)
            deel = re.sub(r'\)\ncontinue', ')continue', deel)

            # verwijder onnodige newlines aan het begin van het script
            if clean == '' and deel[0] == '\n':         # pragma: no cover
                deel = deel[1:]

            clean += deel
    # while

    return clean


def minify_scripts(contents):
    """ Verwijder commentaar en onnodige spaties uit
        javascript embedded in templates

        Skipped sourced scripts
        Skipped application/json script sections
    """
    clean = ""
    pos_start = contents.find('<script')
    while len(contents) and pos_start >= 0:
        pos_close = contents.find('</script>')
        if pos_close > pos_start:
            # section of <script[...]>..</script>
            pos_end_start = contents.find('>', pos_start)
            start_tag = contents[pos_start:pos_end_start+1]
            if 'type="application/json"' in start_tag or ' src="' in start_tag:
                # keep as-is
                clean += contents[:pos_close+9]
            else:
                # javascript to minify
                clean += contents[:pos_end_start+1]      # consume complete start tag
                clean += minify_js(contents[pos_end_start+1:pos_close])
                clean += contents[pos_close:pos_close+9]  # </script>

            contents = contents[pos_close + 9:]
        else:  # pragma: no cover
            # unexpected: start-tag but no end-tag
            # print("[WARNING] minify_scripts: missing script end-tag")
            clean += contents
            contents = ""
        pos_start = contents.find('<script')
    # while
    clean += contents
    return clean


def remove_html_comments(contents):
    """ verwijder html comments
        begin: <!--
        einde: -->
    """
    clean = ""
    pos = contents.find('<!--')
    while len(contents) and pos >= 0:
        clean += contents[:pos]
        endpos = contents.find('-->', pos)
        if endpos >= 0:
            contents = contents[endpos + 3:]
        else:  # pragma: no cover
            # print("[WARNING] remove_html_comments: missing comment end-tag")
            clean += contents
            contents = ""
        pos = contents.find('<!--')
    # while
    clean += contents
    return clean


def minify_css(style):
    """ Minify the CSS styling (komt uit een <style> tag) """

    style = style.replace('\n', ' ').strip()

    # remove whitespace between elements
    style = style.replace('{', '{;')
    style = re.sub(r';\s+\B', ';', style)
    style = style.replace('{;', '{')
    style = style.replace('; ', ';')

    # remove whitespace at the start of the style
    style = re.sub(r'}\s+\B', '}', style)

    style = style.replace(': ', ':')
    style = style.replace('} ', '}')
    style = style.replace(' { ', '{')

    # verwijder onnodige puntkomma
    style = style.replace(';}', '}')

    # print('style: %s' % repr(style))

    return style


def minify_template(contents):
    """ Minify the complete inhoud van een Django Template (.dtl file) """

    # remove /* css block comments */
    contents = re.sub(r'/\*(.*?)\*/', '', contents)

    # remove whitespace between template tags
    contents = re.sub(r'%}\s+{%', '%}{%', contents)

    # remove whitespace between template tags and html tags
    contents = re.sub(r'%}\s+<', '%}<', contents)
    contents = re.sub(r'>\s+{%', '>{%', contents)

    # trivial removal of newlines inside meta and script tags
    contents = re.sub(r'\s+data-', ' data-', contents)
    contents = re.sub(r'\s+content=', ' content=', contents)

    # remove whitespace between template variables and html tags
    # NIET DOEN: dit kunnen echte layout spaties zijn!
    # contents = re.sub(r'}}\s+<', '}}<', contents)
    # contents = re.sub(r'>\s+{{', '>{{', contents)

    # remove whitespace between html tags
    contents = re.sub(r'>\s+<', '><', contents)

    # whitespace voor een @import statement in een <style> block
    contents = re.sub(r'>\s+@import', '>@import', contents)

    # whitespace tussen een css-syntax puntkomma en een block
    contents = re.sub(r';\s+{%', ';{%', contents)

    # whitespace tussen laatste javascript statement en </script>
    contents = re.sub(r'\s+</script>', '</script>', contents)

    # optimize inside <style>
    new_contents = ''
    pos = contents.find('<style>')
    if pos > 0:                                 # pragma: no branch
        pos2 = contents.find('</style>')
        new_contents += contents[:pos+7]        # <style>
        new_contents += minify_css(contents[pos+7:pos2])
        contents = contents[pos2:]              # </style> and onwards
    new_contents += contents
    contents = new_contents

    # optimize in inline style=""
    new_contents = ''
    pos = contents.find('style="')      # let op: neemt ook img_style="padding:10px" mee
    while pos > 0:
        new_contents += contents[:pos+7]
        contents = contents[pos+7:]

        pos = contents.find('"')
        if pos > 0:                     # pragma: no branch
            style = contents[:pos]
            contents = contents[pos:]

            style = style.replace(';  ', ';')
            style = style.replace('; ', ';')
            style = style.replace(': ', ':')

            if style[-1] == ';':
                style = style[:-1]

            new_contents += style

        pos = contents.find('style="')
    # while
    new_contents += contents
    contents = new_contents

    # optimize in inline class=""
    new_contents = ''
    pos = contents.find(' class="')
    while pos > 0:
        new_contents += contents[:pos+8]
        contents = contents[pos+8:]

        pos = contents.find('"')
        if pos > 0:                     # pragma: no branch
            klass = contents[:pos]
            contents = contents[pos:]

            # remove extra spaces between class names
            klass = klass.replace('  ', ' ')

            new_contents += klass

        pos = contents.find(' class="')
    # while
    new_contents += contents

    return new_contents


def minify_html(contents):
    contents = remove_html_comments(contents)
    contents = minify_template(contents)            # OK on pure html
    contents = minify_scripts(contents)

    # remove terminating newline
    while len(contents) > 0 and contents[-1] == '\n':
        contents = contents[:-1]

    return contents


class Loader(AppDirectoriesLoader):
    """ template loader die template files opschoont vlak na inladen.
        hierdoor kunnen de .dtl sources leesbaar blijven
    """

    def get_contents(self, origin):
        """ laad een template """
        contents = super().get_contents(origin)

        # in our project we use .dtl for "django template language" files
        if settings.ENABLE_MINIFY:               # pragma: no branch
            # own templates are .dtl
            # .html is for 3rd party templates
            if origin.template_name.endswith('.dtl') or origin.template_name.endswith('.html'):  # pragma: no branch
                # print("minifying %s" % repr(origin.template_name))

                contents = remove_html_comments(contents)
                contents = minify_template(contents)
                contents = minify_scripts(contents)

                # remove terminating newline
                while len(contents) > 0 and contents[-1] == '\n':
                    contents = contents[:-1]
            # if

        return contents


# end of file
