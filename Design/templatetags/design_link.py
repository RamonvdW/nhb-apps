# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.safestring import mark_safe
from .design_icons import sv_icon
from .design_filters import filter_wbr_www
import functools

""" Centrale plaats om html te genereren voor knoppen

    sv-link-ext: externe link: opent apart tabblad in de browser

"""

register = template.Library()

@register.simple_tag(name='sv-link-ext')
@functools.cache
def sv_link_ext(url=''):

    kleur_class = 'btn-sv-blauw'

    """
                <i class="notranslate material-symbol left sv-blauw-text">open_in_new</i>
                <code>{{ wed.contact_website|wbr_www }}</code>
    """

    new_text = '<a href="%s" target="_blank" rel="noopener noreferrer">\n' % url

    new_text += '<span style="display:inline-block; padding-right:10px; vertical-align:bottom; height:21px">\n'
    new_text += sv_icon(icon_name='open url', kleur='blauw-text', icon_height=21)
    new_text += '</span>\n'

    new_text += '<code style="vertical-align:center">%s</code>' % filter_wbr_www(url)
    new_text += '</a>\n'

    return mark_safe(new_text)


# end of file
