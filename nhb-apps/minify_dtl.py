# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Zorg voor compacte webpagina's door onnodige spaties en newlines
    te verwijderen uit de templates bij het inladen.
"""

# credits to martinsvoboda for a good example

from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
import re


class Loader(AppDirectoriesLoader):
    """ template loader die template files opschoont vlak na inladen.
        hierdoor kunnen de .dtl sources leesbaar blijven
    """

    @staticmethod
    def minify_scripts(contents):
        """ Verwijder commentaar en onnodige spaties uit
            scripts embedded in templates
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
                # else: pass-through variant: <script src=".." variant
                clean += contents[:pos+8]   # includes script start tag
                clean += script
                clean += '</script>'
                contents = contents[pos2+9:]
            else:
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
            else:
                print("[WARNING] remove_html_comments: missing comment end-tag")
                clean += contents
                contents = ""
            pos = contents.find('<!--')
        # while
        clean += contents
        return clean

    def get_contents(self, origin):
        """ Deze Loader methode lijkt aangeroepen """
        contents = super().get_contents(origin)
        # in our project we use .dtl for "django template language" files
        if origin.template_name.endswith('.dtl'):
            # print("minifying %s" % repr(origin.template_name))

            contents = self.remove_html_comments(contents)

            # TODO: zoek uit of het minder cpu kost als de reg-exps gecompileerd worden
            # TODO: zoek uit of het minder cpu kost als de reg-exps gecombineerd worden

            # remove whitespace between html tags
            contents = re.sub(r'>\s+<', '><', contents, flags=re.MULTILINE)

            # remove whitespace between template tags
            contents = re.sub(r'\%}\s+{%', '%}{%', contents, flags=re.MULTILINE)

            # remove whitespace between template tags en html tags
            contents = re.sub(r'\%}\s+<', '%}<', contents, flags=re.MULTILINE)
            contents = re.sub(r'>\s+{%', '>{%', contents, flags=re.MULTILINE)

            # remove whitespace between template context variables en html tags
            contents = re.sub(r'>\s+{{', '>{{', contents, flags=re.MULTILINE)
            contents = re.sub(r'}}\s+<', '}}<', contents, flags=re.MULTILINE)

            # remove css block comments
            contents = re.sub(r'/\*(.*?)\*/', '', contents, flags=re.MULTILINE)

            # remove empty lines
            contents = re.sub(r'\n\n', '\n', contents)

            # handling inline javascript
            contents = self.minify_scripts(contents)

        return contents

# TODO: minify style blocks - niet in deze template loader maar tijdens collectstatic ofzo

# end of file
