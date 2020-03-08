# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


def filter_highlight(text, search_for):
    """  highlight filter looks for occurences of 'search_for' in 'text'
         and puts a html tags around it to highlight that text.
         The search is case-insensitive.
    """
    new_text = ""
    if search_for:
        # not None, not empty
        search_for = search_for.lower()
        search_len = len(search_for)
        pos = text.lower().find(search_for)
        limit = 10
        while pos >= 0 and limit > 0:
            limit -= 1
            # found an instance that we want to highlight
            # eat all text before that point + perform escaping
            new_text += escape(text[:pos])
            text = text[pos:]

            new_text += '<b>'           # highlighter prefix

            # take over the found part, in the original case + perform escaping
            new_text += escape(text[:search_len])
            text = text[search_len:]

            new_text += '</b>'          # highlighter postfix

            # find the next occurence
            pos = text.lower().find(search_for)
        # while

    return mark_safe(new_text + text)


# register the filter
register = template.Library()
register.filter('highlight', filter_highlight)

# end of file
