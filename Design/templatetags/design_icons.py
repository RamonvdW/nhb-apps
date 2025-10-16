# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

""" Centrale plaats om vertaling van iconen naar juiste html/css te doen """


# mapping of sv-icon name to Material Symbol icon name
MATERIAL_SYMBOLS = {
    'mijn-pagina': 'account_circle',
    'bondspas': 'id_card',
    'uitloggen': 'logout',
    'taken': 'inbox',
    'admin': 'database',
    'wissel-van-rol': 'group',
    'email': 'mail',
}


@register.simple_tag(name='sv-icon')
def sv_icon(icon_name, kleur='sv-rood-text', extra_class='', extra_style=''):
    material_symbol = MATERIAL_SYMBOLS.get(icon_name, None)
    if material_symbol is None:
        raise ValueError('Unknown icon name: %s' % repr(icon_name))

    # bouw deze html:
    # <i class=".." style="..">icon_name</i>

    # "notranslate" prevent considering the icon name as translatable text
    new_text = '<i class="notranslate material-symbol'

    if kleur:
        new_text += ' ' + kleur

    if extra_class:
        new_text += ' ' + extra_class

    if extra_style:
        new_text += '" style="' + extra_style

    new_text += '">' + material_symbol + '</i>'

    return mark_safe(new_text)


# end of file
