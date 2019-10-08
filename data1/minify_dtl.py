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
    def get_contents(self, origin):
        """ Deze Loader methode lijkt aangeroepen """
        contents = super().get_contents(origin)
        # in our project we use .dtl for "django template language" files
        if origin.template_name.endswith('.dtl'):

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

        return contents


# end of file
