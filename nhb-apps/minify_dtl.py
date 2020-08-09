# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Zorg voor compacte webpagina's door onnodige spaties en newlines
    te verwijderen uit de templates bij het inladen.

    Inladen gebeurt eenmalig na het starten van de applicatie.
    Let op: dit is vOOr expansie van tags en die kunnen whitespace toevoegen
"""

# credits to martinsvoboda for a good example

from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
import re

# change to False to disable this utility
ENABLE_MINIFY = True


class Loader(AppDirectoriesLoader):
    """ template loader die template files opschoont vlak na inladen.
        hierdoor kunnen de .dtl sources leesbaar blijven
    """

    @staticmethod
    def minify_scripts(contents):
        """ Verwijder commentaar en onnodige spaties uit
            javascript embedded in templates
        """
        clean = ""
        pos = contents.find('<script')
        while len(contents) and pos >= 0:
            pos2 = contents.find('</script>')
            if pos2 > pos:
                script = contents[pos+8:pos2]
                if contents[pos+7] == '>':
                    # remove single-line comments
                    script = re.sub(r'//.*\n', '\n', script)
                    # remove whitespace at start of the line
                    script = re.sub(r'\n\s+', '\n', script)
                    # remove whitespace at end of the line
                    script = re.sub(r'\s+\n', '\n', script)
                    # remove whitespace around certain operators
                    script = re.sub(r' = ', '=', script)
                    script = re.sub(r' == ', '==', script)
                    script = re.sub(r' != ', '!=', script)
                    script = re.sub(r' === ', '===', script)
                    script = re.sub(r' !== ', '!==', script)
                    script = re.sub(r' \+ ', '+', script)
                    script = re.sub(r' - ', '-', script)
                    script = re.sub(r' < ', '<', script)
                    script = re.sub(r' && ', '&&', script)
                    script = re.sub(r', ', ',', script)
                    script = re.sub(r': ', ':', script)
                    script = re.sub(r'; ', ';', script)
                    script = re.sub(r'\) {', '){', script)
                    script = re.sub(r'{ ', '{', script)
                    script = re.sub(r' \(', '(', script)
                    # remove newlines
                    script = re.sub(r'\n', '', script)
                # else: pass-through variant: <script src=".." variant
                clean += contents[:pos+8]   # includes script start tag
                clean += script
                clean += '</script>'
                contents = contents[pos2+9:]
            else:   # pragma: no cover
                # unexpected: start-tag but no end-tag
                print("[WARNING] minify_scripts: missing script end-tag")
                clean += contents
                contents = ""
            pos = contents.find('<script')
        # while
        clean += contents
        return clean

    @staticmethod
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
                contents = contents[endpos+3:]
            else:   # pragma: no cover
                print("[WARNING] remove_html_comments: missing comment end-tag")
                clean += contents
                contents = ""
            pos = contents.find('<!--')
        # while
        clean += contents
        return clean

    @staticmethod
    def minify_template(contents):
        # remove /* css block comments */
        contents = re.sub(r'/\*(.*?)\*/', '', contents)

        # remove whitespace between template tags
        contents = re.sub(r'}\s+{', '}{', contents)

        # remove whitespace between template tags and html tags
        contents = re.sub(r'%}\s+<', '%}<', contents)
        contents = re.sub(r'>\s+{%', '>{%', contents)

        # remove whitespace between template context variables and html tags
        contents = re.sub(r'>\s+{{', '>{{', contents)
        contents = re.sub(r'}}\s+<', '}}<', contents)

        # remove whitespace between html tags
        contents = re.sub(r'>\s+<', '><', contents)

        return contents

    def get_contents(self, origin):
        """ Deze Loader methode lijkt aangeroepen """
        contents = super().get_contents(origin)

        # in our project we use .dtl for "django template language" files
        if ENABLE_MINIFY:
            # own templates are .dtl
            # .html is for 3rd party templates
            if origin.template_name.endswith('.dtl') or origin.template_name.endswith('.html'):
                # print("minifying %s" % repr(origin.template_name))

                contents = self.remove_html_comments(contents)
                contents = self.minify_template(contents)
                contents = self.minify_scripts(contents)

                # remove terminating newline
                while len(contents) > 0 and contents[-1] == '\n':
                    contents = contents[:-1]
            # if

        return contents


# end of file
