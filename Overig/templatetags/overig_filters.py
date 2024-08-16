# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from Competitie.definities import DAGDEEL2LABEL


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

            new_text += '<b class="sv-rood-text">'           # highlighter prefix

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
        pos3 = text.find('handboogsport')

        if pos1 >= 0:
            # adres bevat nog een punt
            if (pos2 < 0 or pos1 < pos2) and (pos3 < 0 or pos1 < pos3):
                # punt staat eerst
                new_text += escape(text[:pos1]) + '<wbr>' + escape(text[pos1])
                text = text[pos1+1:]
                continue        # with the while

        if pos2 >= 0:
            if pos3 < 0 or pos2 < pos3:
                # apenstaartje staat eerst
                new_text += escape(text[:pos2]) + '<wbr>' + escape(text[pos2])
                text = text[pos2+1:]
                continue            # with the while

        if pos3 >= 0:
            new_text += escape(text[:pos3+8]) + '<wbr>'     # handboog<wbr>sport
            text = text[pos3+8:]
            continue

        # niets meer gevonden
        new_text += escape(text)
        text = ''

    # while

    return mark_safe(new_text)


def filter_wbr_www(text):
    """  wbr_email filter looks for places where the e-mail address could be wrapped
         and insert a <wbr> html tag before that character.
    """
    new_text = ""

    pos = text.find('://')
    if pos >= 0:
        new_text += escape(text[:pos+3]) + '<wbr>'
        text = text[pos+3:]

    while len(text) > 0:
        pos1 = text.find('handboogsport')
        pos2 = text.find('grensoverschreiden')
        pos3 = text.find('.')
        pos4 = text.find('/')
        if pos4 == len(text)-1:
            pos4 = -1

        if pos1 >= 0:
            if (pos2 < 0 or pos1 < pos2) and (pos3 < 0 or pos1 < pos3) and (pos4 < 0 or pos1 < pos4):
                new_text += escape(text[:pos1+8]) + '<wbr>' + escape('sport')
                text = text[pos1+13:]
                continue

        if pos2 >= 0:
            if (pos3 < 0 or pos2 < pos3) and (pos4 < 0 or pos2 < pos4):
                new_text += escape(text[:pos2+5]) + '<wbr>' + escape('over') + '<wbr>'
                text = text[pos2+9:]
                continue        # with the while

        if pos3 >= 0:
            if pos4 < 0 or pos3 < pos4:
                new_text += escape(text[:pos3+1:]) + '<wbr>'
                text = text[pos3 + 1:]
                continue

        if pos4 >= 0:
            new_text += escape(text[:pos4+1:]) + '<wbr>'
            text = text[pos4+1:]
            continue

        # niets meer gevonden
        new_text += escape(text)
        text = ''

    # while

    return mark_safe(new_text)


def filter_wbr_dagdeel(text):
    """  wbr_dagdeel filter geeft een korte en lange beschrijving van de dagdeel-afkorting
         voorbeeld:
            WO:
                <span class="hide-on-med-and-up">W</span>
                <span class="hide-on-small-only">Woensdag</span>

            ZAo:
                <span class="hide-on-med-and-up">Za-Och</span>
                <span class="hide-on-small-only">Zaterdag<wbr>ochtend</span>
    """

    try:
        tup = DAGDEEL2LABEL[text]
    except KeyError:
        new_text = text
    else:
        kort, lang = tup
        new_text = '<span class="hide-on-med-and-up">' + escape(kort) + '</span>'
        new_text += '<span class="hide-on-small-only">'

        done = False
        for suffix in ('avond', 'middag', 'ochtend'):
            suffix_len = len(suffix)
            if lang[-suffix_len:] == suffix:
                new_text += escape(lang[:-suffix_len]) + '<wbr>' + escape(suffix)
                done = True
                break   # from the for
        # for

        if not done:
            new_text += escape(lang)

        new_text += '</span>'

    return mark_safe(new_text)


def filter_wbr_seizoen(text):
    """  wbr_seizoen filter voegt een <wbr> toe aan de string "1111/2222"
    """

    pos = text.find('/')
    new_text = text[:pos+1] + '<wbr>' + text[pos+1:]

    return mark_safe(new_text)


# register the filters
register = template.Library()
register.filter('highlight', filter_highlight)
register.filter('wbr_email', filter_wbr_email)
register.filter('wbr_www', filter_wbr_www)
register.filter('wbr_dagdeel', filter_wbr_dagdeel)
register.filter('wbr_seizoen', filter_wbr_seizoen)

# end of file
