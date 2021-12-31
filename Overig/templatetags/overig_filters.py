# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


def filter_highlight(text, search_for):
    """  highlight filter looks for occurrences of 'search_for' in 'text'
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

            # find the next occurrence
            pos = text.lower().find(search_for)
        # while

    return mark_safe(new_text + text)


def filter_wbr_email(text):
    """  wbr_email filter looks for places where the e-mail address could be wrapped
         and insert a <wbr> html tag before that character.
    """
    new_text = ""

    while len(text) > 0:
        pos1 = text.find('.')
        pos2 = text.find('@')

        if pos1 >= 0:
            if pos1 < pos2:
                new_text += escape(text[:pos1]) + '<wbr>' + escape(text[pos1])
                text = text[pos1+1:]
                continue        # with the while

        if pos2 >= 0:
            new_text += escape(text[:pos2]) + '<wbr>' + escape(text[pos2])
            text = text[pos2+1:]
            continue            # with the while

        # niets meer gevonden
        new_text += escape(text)
        text = ''

    # while

    return mark_safe(new_text)


# register the filters
register = template.Library()
register.filter('highlight', filter_highlight)
register.filter('wbr_email', filter_wbr_email)

# end of file
