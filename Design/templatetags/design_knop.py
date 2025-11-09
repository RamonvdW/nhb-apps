# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.safestring import mark_safe
from .design_icons import sv_icon
import functools

""" Centrale plaats om html te genereren voor knoppen

    sv-knop-nav:   navigeer naar andere pagina
    sv-knop-ext:   externe link: opent apart tabblad in de browser
    sv-knop-js:    wordt gekoppeld aan een javascript functie
    sv-knop-float: knop die in de linker onderhoek in beeld komt zodra ...

"""

register = template.Library()

@register.simple_tag(name='sv-knop-nav')
@functools.cache
def sv_knop_nav(url='', kleur='rood', icon='', tekst='##BUG', knop_id='',
                smal=False, extra_class='', extra_style=''):

    if kleur == 'rood':
        a_class = 'btn-sv-rood'
    else:
        a_class = 'btn-sv-blauw'

    if extra_class:
        a_class += ' ' + extra_class

    new_text = '<a class="%s" href="%s"' % (a_class, url)

    if knop_id:
        new_text += ' id="%s"' % knop_id

    if smal and len(tekst) > 0:
        smal = False

    if smal:
        if extra_style:
            extra_style += ';'
        extra_style += 'width:35px; padding:0'

    if extra_style:
        new_text += ' style="%s"' % extra_style

    new_text += '>\n'

    if icon:
        new_text += '<span style="display:inline-block; vertical-align:text-bottom; height:24px'

        if tekst:
            new_text += '; padding-right:10px'

        new_text += '">\n'

        new_text += sv_icon(icon, kleur='wit', use='button')
        new_text += '</span>\n'

    new_text += tekst
    new_text += '</a>\n'

    return mark_safe(new_text)


@register.simple_tag(name='sv-knop-mailto')
@functools.cache
def sv_knop_mailto(kleur='rood', icon='email', email='', tekst=''):

    if kleur == 'rood':
        kleur_class = 'btn-sv-rood'
    else:
        kleur_class = 'btn-sv-blauw'

    new_text = '<a class="%s" href="mailto:%s">\n' % (kleur_class, email)

    if icon:
        new_text += '<span style="display:inline-block; vertical-align:text-bottom; height:24px">\n'
        new_text += sv_icon('email', kleur='wit', use='text')
        new_text += '</span>\n'

    new_text += tekst

    new_text += '</a>\n'

    return mark_safe(new_text)


@register.simple_tag(name='sv-knop-ext')
@functools.cache
def sv_knop_ext(kleur='rood', icon='open url', tekst='tbd', url='', extra_stijl=''):

    if kleur == 'rood':
        kleur_class = 'btn-sv-rood'
    else:
        kleur_class = 'btn-sv-blauw'

    new_text = '<a class="%s" href="%s" target="_blank" rel="noopener noreferrer"' % (kleur_class, url)
    if extra_stijl:
        new_text += ' style="%s"' % extra_stijl
    new_text += '>\n'

    new_text += '<span style="display:inline-block; vertical-align:text-bottom; height:24px'
    if tekst:
        new_text += '; padding-right:10px'
    new_text += '">\n'

    new_text += sv_icon(icon, kleur='wit')

    new_text += '</span>\n'

    new_text += tekst

    new_text += '</a>\n'

    return mark_safe(new_text)


@register.simple_tag(name='sv-knop-modal')
@functools.cache
def sv_knop_modal(id_prefix, id_specific, kleur='rood', icon='', tekst='##BUG', extra_class='', extra_style=''):
    """ knop om een modal dialog box mee op te roepen

        href wordt: '#' + id_prefix + id_specific

    """

    url = '#%s%s' % (id_prefix, id_specific)
    if extra_class:
        extra_class += ' '
    extra_class += 'modal-trigger'

    return sv_knop_nav(url=url, kleur=kleur, icon=icon, tekst=tekst, extra_class=extra_class, extra_style=extra_style)


# end of file
