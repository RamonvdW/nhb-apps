# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from Design.icon_svg.Material_Symbols.icon_svg import MATERIAL_ICONS_SVG
import functools

register = template.Library()

""" Centrale plaats om vertaling van iconen naar juiste html/css te doen """


# mapping van sv-icon gebruik naar Material Symbol icon name
MATERIAL_SYMBOLS = {
    'aanpassen': 'edit',
    'account aanmaken': 'fingerprint',
    'account activiteit': 'recent_actors',
    'account inloggen': 'person',
    'account wachtwoord vergeten': 'help',
    'account wachtwoord wijzigen': 'lock',
    'account wachtwoord opslaan': 'check',
    'admin': 'database',
    'beheer vereniging': 'house_siding',
    'bestelling afronden': 'shopping_cart_checkout',
    'bestelling toon details': 'play_arrow',
    'annuleer bestelling': 'delete',
    'bestellingen overzicht': 'shopping_cart',
    'mandje transport opslaan': 'check',
    'mandje transport opties': 'local_shipping',
    'bondscompetities': 'my_location',
    'bondspas': 'id_card',
    'comp ag controle': 'how_to_reg',
    'comp ag vaststellen': 'how_to_reg',
    'comp beheer': 'store',
    'comp bk teams': 'rule',
    'comp blanco resultaat': 'fast_forward',
    'comp doorzetten': 'mediation',
    'comp info indiv': 'info',
    'comp info teams': 'groups',
    'comp inschrijvingen': 'receipt',
    'comp klassengrenzen vaststellen': 'equalizer',
    'comp kleine klassen': 'merge',
    'comp limieten': 'accessibility_new',
    'comp medailles': 'military_tech',
    'comp planning': 'pending_actions',
    'comp rcl team scores': 'gavel',
    'comp regio afsluiten': 'done_outline',
    'comp regio ingeschreven teams': 'gamepad',
    'comp regio instellingen teams': 'flaky',
    'comp regio poules': 'grid_4x4',
    'comp regio teams': 'gamepad',
    'comp rk extra deelnemer': 'person_add',
    'comp rk selectie': 'rule',
    'comp rk teams': 'api',
    'comp scores deelnemers': 'add',
    'comp seizoen afsluiten': 'waving_hand',
    'comp seizoen starten': 'playlist_add',
    'comp statistiek': 'query_stats',
    'comp tijdlijn': 'schedule',
    'comp uitslagen': 'scoreboard',
    'comp wijzig datums': 'build',
    'download': 'download',
    'drive toestemming': 'add_to_drive',
    'drive wedstrijdformulieren maken': 'add_to_drive',
    'email': 'mail',
    'evenement verkoopvoorwaarden': 'article',
    'evenementen': 'article',
    'feedback verstuur': 'done',
    'feedback bedankt': 'record_voice_over',
    'feedback duimpje omhoog': 'thumb_up',
    'feedback neutraal': 'thumbs_up_down',
    'feedback duimpje omlaag': 'thumb_down',
    'functie 2fa controle': 'lock',
    'functie 2fa koppel': 'lock',
    'functie 2fa uitleg': 'article',
    'functie beheerders': 'supervisor_account',
    'functie login as': 'change_circle',
    'functie vhpg inzien': 'gavel',
    'functie vhpg status': 'verified_user',
    'functie vhpg': 'gavel',
    'functie wissel sec': 'help',
    'functie wissel van rol': 'group',
    'functie wissel': 'switch_account',
    'geo clusters': 'group_work',
    'handleiding': 'menu_book',
    'handleidingen': 'menu_book',
    'het plein': 'hub',
    'histcomp': 'undo',
    'inschrijven familie': 'family_restroom',
    'inschrijven groep': 'group',
    'inschrijven sporter': 'person',
    'interland lijst': 'flag',
    'kalender': 'event_note',
    'kalender toon alles': 'backspace',
    'kalender filter': 'filter_alt',
    'kalender volgende': 'chevron_right',
    'kalender vorige': 'chevron_left',
    'korting combi': 'stack',
    'korting persoonlijk': 'account_circle',
    'korting vereniging': 'home',
    'ledenvoordeel webwinkel': 'shopping_cart',
    'ledenvoordeel': 'redeem',
    'leeftijdsklassen': 'star',
    'logboek': 'book',
    'logboek toon alles': 'backspace',
    'mandje': 'shopping_cart',
    'verwijder uit mandje': 'delete',
    'mijn bestellingen': 'receipt_long',
    'mijn pagina': 'account_circle',
    'open kaart': 'open_in_new',
    'open url': 'open_in_new',
    'opleiding basiscursus': 'school',
    'opleiding crm overnemen': 'person_add',
    'opleiding instaptoets inzicht': 'query_stats',
    'opleiding instaptoets niet gehaald': 'thumb_down',
    'opleiding instaptoets niet ingeschreven': 'radar',
    'opleiding instaptoets': 'login',
    'opleiding lesmateriaal': 'book_2',
    'opleiding locaties': 'school',
    'opleiding verkoopvoorwaarden': 'article',
    'opleiding aanmeldingen': 'group',
    'opleidingen': 'school',
    'privacyverklaring': 'security',
    'record ander': 'star_shine',
    'records filteren': 'filter_alt',
    'records verbeterbaar': 'leaderboard',
    'records zoeken': 'search',
    'records': 'stars_2',
    'registreer gast': 'explore',
    'registreer lid': 'id_card',
    'scheids beschikbaarheid': 'event_available',
    'scheids competitie': 'my_location',
    'scheids handleiding': 'menu_book',
    'scheids kalender': 'event_note',
    'scheids korps': 'star',
    'scheidsrechters': 'sports',
    'score geschiedenis': 'history',
    'scores invoeren': 'edit',
    'feedback': 'chat',
    'sluiten': 'close',
    'spelden graadspelden': 'zoom_out_map',
    'spelden meesterspelden': 'category',
    'spelden tussenspelden': 'trending_up',
    'sporter voorkeuren': 'tune',
    'taken': 'inbox',
    'toevoegen': 'add',
    'uitloggen': 'logout',
    'uitslag bk indiv': 'flag',
    'uitslag bk teams': 'flag',
    'uitslag regio indiv': 'view_compact',
    'uitslag regio teams': 'view_compact',
    'uitslag rk indiv': 'view_comfy',
    'uitslag rk teams': 'view_comfy',
    'ver accommodatie': 'account_balance',
    'ver beheerders': 'supervisor_account',
    'ver comp kamp deelnemers status': 'rule',
    'ver comp wie schiet waar': 'gamepad',
    'ver competitie wedstrijden': 'event',
    'ver evenement locaties': 'school',
    'ver evenementen': 'event_note',
    'ver ext crm': 'group',
    'ver externe locaties': 'hiking',
    'ver gast accounts': 'list_alt_check',
    'ver kortingen': 'sell',
    'ver ledenlijst': 'import_contacts',
    'ver mollie': 'settings',
    'ver opleidingen': 'school',
    'ver overboekingen': 'euro_symbol',
    'ver regio teams': 'gamepad',
    'ver rk teams': 'api',
    'ver team invallers': 'how_to_reg',
    'ver voorkeuren leden': 'tune',
    'ver voorwaarden': 'article',
    'ver wedstrijden': 'event_note',
    'verder winkelen': 'event_note',
    'verenigingen': 'share_location',
    'walibi webshop': 'shopping_cart',
    'webwinkel verkoopvoorwaarden': 'article',
    'webwinkel voorraad': 'inventory',
    'webwinkel': 'local_mall',
    'wedstrijden verkoopvoorwaarden': 'article',
    'wedstrijdklassen': 'equalizer',
    'zoek vereniging': 'travel_explore',
    'zoek': 'search',
    'nav menu dropdown': 'expand_more',
    'tijdelijke code ga door': 'check',
}


@register.simple_tag(name='sv-icon')
@functools.cache
def sv_icon(icon_name, kleur='sv-rood-text', icon_height='', extra_class='', extra_style=''):

    # zoek het bijbehorende Material Symbol op
    material_symbol = MATERIAL_SYMBOLS.get(icon_name, None)
    if material_symbol is None:
        raise ValueError('Unknown icon name: %s' % repr(icon_name))

    new_text = ''
    if settings.DEBUG:
        new_text += '<!-- Material-Symbol: ' + material_symbol + ' -->\n'

    # bouw deze html:
    # <svg ...></svg>
    svg = MATERIAL_ICONS_SVG.get(material_symbol, None)
    if svg:
        if not icon_height:
            icon_height = 24

        svg = svg.replace(' height="48"', '')
        svg = svg.replace(' width="48"', '')
        svg = svg.replace('><path',
                          ' height="%s" width="%s"><path' % (icon_height, icon_height))

        if kleur:
            svg = svg.replace('<path d=',
                              '<path fill="currentColor" d=')
            kleur = "green-text"        # TODO: tijdelijk!
            svg = svg.replace('<svg',
                              '<svg class="%s"' % kleur)

        new_text += svg

    else:
        # TODO: obsolete this
        # bouw deze html:
        # <i class=".." style="..">icon_name</i>

        # "notranslate" prevent considering the icon name as translatable text
        new_text += '<i class="notranslate material-symbol'

        if kleur:
            new_text += ' ' + kleur

        if extra_class:
            new_text += ' ' + extra_class

        if extra_style or icon_height:
            new_text += '" style="' + extra_style

            if icon_height:
                # unset the width, otherwise material-symbol css forces it to 21px
                new_text += '; font-size:%spx; width:unset' % icon_height

        new_text += '">' + material_symbol + '</i>'

    return mark_safe(new_text)


@register.simple_tag(name='sv-icon-op-button')
@functools.cache
def sv_icon_op_button(icon_name, tekst='', extra_class='', extra_style=''):
    new_text = '<span'

    if extra_class:
        new_text += ' class="%s"' % extra_class

    new_text +=' style="display:inline-block; vertical-align:text-bottom; height:24px'

    if tekst:
        new_text += '; padding-right:10px'

    if extra_style:
        new_text += '; ' + extra_style

    new_text += '">\n'

    new_text += sv_icon(icon_name, kleur='white-text', icon_height=21)
    new_text += '</span>\n'

    new_text += tekst

    return mark_safe(new_text)


# end of file
