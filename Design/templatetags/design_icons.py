# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from Design.icon_svg.Material_Symbols.symbol_svg import MATERIAL_SYMBOL_SVG
from Design.icon_svg.sv_symbols.symbol_svg import SV_SYMBOL_SVG
import functools

register = template.Library()

""" Centrale plaats om vertaling van iconen naar juiste html/css te doen """


# mapping van sv-icon gebruik naar Material Symbol icon name
ICON_NAME2MATERIAL_SYMBOL_NAME = {
    # algemene opties
    'aanpassen': 'edit',
    'copy': 'content_copy',
    'download': 'download',
    'email': 'mail',
    'open url': 'open_in_new',
    'opslaan': 'check',
    'sluiten': 'close',
    'terug': 'arrow_back_ios',
    'toevoegen': 'add',
    'toon details': 'play_arrow',
    'verwijder': 'delete',
    'zoek': 'search',

    # specifiek
    'account aanmaken': 'fingerprint',
    'account activiteit': 'recent_actors',
    'account inloggen': 'person',
    'account login as select': 'play_arrow',
    'account wachtwoord vergeten': 'help',
    'account wachtwoord wijzigen': 'lock',
    'admin': 'database',
    'annuleer bestelling': 'delete',
    'beheer vereniging': 'house_siding',
    'bestelling afronden': 'shopping_cart_checkout',
    'bestelling status betaald': 'check',
    'bestelling status geannuleerd': 'close',
    'bestelling status wacht op betaling': 'hourglass_empty',
    'bestelling toon details': 'play_arrow',
    'bestellingen overzicht': 'shopping_cart',
    'bestellingen zoek': 'search',
    'bondscompetities': 'my_location',
    'bondspas': 'id_card',
    'comp ag controle': 'how_to_reg',
    'comp ag vaststellen': 'how_to_reg',
    'comp beheer': 'store',
    'comp benodigde dagdelen': 'leaderboard',
    'comp bk teams': 'rule',
    'comp blanco resultaat': 'fast_forward',
    'comp doorzetten': 'mediation',
    'comp gekozen wedstrijden': 'leaderboard',
    'comp info indiv': 'info',
    'comp info teams': 'groups',
    'comp inschrijvingen': 'receipt',
    'comp kamp deelnemer afmelden': 'warning',
    'comp kamp deelnemer bevestig deelname': 'thumb_up',
    'comp kamp selectie status afgemeld': 'block',
    'comp kamp selectie status attentie': 'warning',
    'comp kamp selectie status bevestigd': 'check',
    'comp kamp selectie status onbekend': 'help',
    'comp kamp team bekijk': 'visibility',
    'comp kamp team koppelen': 'group',
    'comp kamp team lid blokkeer': 'square',
    'comp kamp team lid geselecteerd': 'check',
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
    'comp sporter status aangemeld': 'check',
    'comp statistiek': 'query_stats',
    'comp team koppel leden': 'group',
    'comp tijdlijn': 'schedule',
    'comp uitslagen': 'scoreboard',
    'comp wijzig datums': 'build',
    'controleer invoer overboeking': 'check',
    'drive toestemming': 'add_to_drive',
    'drive wedstrijdformulieren maken': 'add_to_drive',
    'evenement verkoopvoorwaarden': 'article',
    'evenementen': 'article',
    'feedback bedankt': 'record_voice_over',
    'feedback duimpje omhoog': 'thumb_up',
    'feedback duimpje omlaag': 'thumb_down',
    'feedback neutraal': 'thumbs_up_down',
    'feedback smiley bruikbaar': 'sentiment_neutral',
    'feedback smiley moet beter': 'sentiment_dissatisfied',
    'feedback smiley tevreden': 'sentiment_satisfied',
    'feedback verstuur': 'done',
    'feedback': 'chat',
    'functie 2fa controle': 'lock',
    'functie 2fa koppel': 'lock',
    'functie 2fa uitleg': 'article',
    'functie beheerders': 'supervisor_account',
    'functie login as': 'change_circle',
    'functie vhpg inzien': 'gavel',
    'functie vhpg status': 'verified_user',
    'functie vhpg': 'gavel',
    'functie wijzig beheerders': 'group_add',
    'functie wijzig email': 'alternate_email',
    'functie wissel sec': 'help',
    'functie wissel van rol': 'group',
    'functie wissel': 'switch_account',
    'geo clusters': 'group_work',
    'handleiding': 'menu_book',
    'handleidingen': 'menu_book',
    'het plein 2': 'home',
    'het plein': 'hub',
    'histcomp': 'undo',
    'inschrijven familie': 'family_restroom',
    'inschrijven groep': 'group',
    'inschrijven sporter': 'person',
    'interland lijst': 'flag',
    'kalender filter': 'filter_alt',
    'kalender toon alles': 'backspace',
    'kalender volgende': 'chevron_right',
    'kalender vorige': 'chevron_left',
    'kalender': 'event_note',
    'korting combi': 'stack',
    'korting persoonlijk': 'account_circle',
    'korting vereniging': 'home',
    'ledenvoordeel webwinkel': 'shopping_cart',
    'ledenvoordeel': 'redeem',
    'leeftijdsklassen': 'star',
    'logboek toon alles': 'backspace',
    'logboek': 'book',
    'mandje transport opties': 'local_shipping',
    'mandje': 'shopping_cart',
    'mijn bestellingen': 'receipt_long',
    'mijn pagina': 'account_circle',
    'nav menu dropdown': 'expand_more',
    'nav omlaag op pagina': 'arrow_downward',
    'open kaart': 'open_in_new',
    'opleiding aanmeldingen': 'group',
    'opleiding basiscursus': 'school',
    'opleiding crm overnemen': 'person_add',
    'opleiding instaptoets inzicht': 'query_stats',
    'opleiding instaptoets niet gehaald': 'thumb_down',
    'opleiding instaptoets niet ingeschreven': 'radar',
    'opleiding instaptoets': 'login',
    'opleiding lesmateriaal': 'book_2',
    'opleiding locaties': 'school',
    'opleiding verkoopvoorwaarden': 'article',
    'opleidingen': 'school',
    'otp stap 1': 'looks_one',
    'otp stap 2': 'looks_two',
    'otp stap 3': 'looks_3',
    'otp volgende stap': 'arrow_forward_ios',
    'otp vorige stap': 'arrow_back_ios',
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
    'spelden graadspelden': 'zoom_out_map',
    'spelden meesterspelden': 'category',
    'spelden tussenspelden': 'trending_up',
    'sporter voorkeuren': 'tune',
    'taken': 'inbox',
    'tijdelijke code ga door': 'check',
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
    'verwijder uit mandje': 'delete',
    'walibi webshop': 'shopping_cart',
    'webwinkel verkoopvoorwaarden': 'article',
    'webwinkel voorraad': 'inventory',
    'webwinkel': 'local_mall',
    'wedstrijden verkoopvoorwaarden': 'article',
    'wedstrijdklassen': 'equalizer',
    'zoek vereniging': 'travel_explore',
}

ICON_NAME2SV_SYMBOL = {
    'comp planning toon details': 'zoom_in',
}


def _get_icon_material_symbol(icon_name, icon_height, extra_style, kleur_class):
    new_text = ''

    # zoek het bijbehorende Material Symbol op
    material_symbol = ICON_NAME2MATERIAL_SYMBOL_NAME.get(icon_name, None)
    if material_symbol:

        if settings.DEBUG:
            new_text += '<!-- Material-Symbol: ' + material_symbol + ' -->\n'

        svg = MATERIAL_SYMBOL_SVG.get(material_symbol, None)
        if not svg:
            raise ValueError('No svg for material symbol: %s' % repr(material_symbol))

        if extra_style:
            extra_style += '; '
        extra_style += 'min-width:%spx' % icon_height

        svg = svg.replace(' height="48"', '')
        svg = svg.replace(' width="48"', '')
        svg = svg.replace('><path',
                          ' height="%s" width="%s" style="%s" draggable="false"><path' % (icon_height, icon_height, extra_style))

        if kleur_class:
            svg = svg.replace('<svg ',
                              '<svg class="%s" ' % kleur_class)
            svg = svg.replace('<path d=',
                              '<path fill="currentColor" d=')

        new_text += svg

    return new_text


def _get_icon_sv(icon_name, icon_height, extra_style, kleur_class):
    new_text = ''

    # zoek het bijbehorende Material Symbol op
    sv_symbol = ICON_NAME2SV_SYMBOL.get(icon_name, None)
    if sv_symbol:

        if settings.DEBUG:
            new_text += '<!-- sv-symbol: ' + sv_symbol + ' -->\n'

        svg = SV_SYMBOL_SVG.get(sv_symbol, None)
        if not svg:
            raise ValueError('No svg for sv symbol: %s' % repr(sv_symbol))

        if extra_style:
            extra_style += '; '
        extra_style += 'min-width:%spx' % icon_height

        svg = svg.replace(' viewBox=',
                          ' height="%s" width="%s" style="%s" draggable="false" viewBox=' % (icon_height, icon_height, extra_style))

        if kleur_class:
            svg = svg.replace('<svg ',
                              '<svg class="%s" ' % kleur_class)
            svg = svg.replace('<g id=',
                              '<g fill="currentColor" id=')

        new_text += svg

    return new_text


icon_use_to_icon_height = {
    'card': 64,                 # centrale op het kaartjes
    'card corner': 24,          # extern open in de rechter bovenhoek
    'button': 21,
    'text': 27,
    'feedback': 40,
}

icon_kleur_to_class = {
    'rood': 'sv-rood-text',
    'blauw': 'sv-blauw-text',
    'zwart': 'sv-zwart-text',
    'middel-blauw': 'sv-middel-blauw-text',
    'groen': 'green-text',
    'grijs': 'grey-text',
    'wit': 'white-text',
}


@register.simple_tag(name='sv-icon')
@functools.cache
def sv_icon(icon_name, use='button', kleur='rood', icon_height=0, extra_style=''):
    """
        use is een string die standaard icon_height kies - zie tabel hierboven
    """

    if not icon_height:
        icon_height = icon_use_to_icon_height.get(use, 24)

    kleur_class = ''
    if kleur:
        kleur_class = icon_kleur_to_class.get(kleur, None)
        if not kleur_class:
            raise ValueError('{sv-icon} kleur niet ondersteund: %s' % repr(kleur))

        #kleur_class = "green-text"        # TODO: tijdelijk!

    new_text = _get_icon_material_symbol(icon_name, icon_height, extra_style, kleur_class)

    if not new_text:
        new_text = _get_icon_sv(icon_name, icon_height, extra_style, kleur_class)

    if not new_text:
        raise ValueError('Unknown icon name: %s' % repr(icon_name))

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

    new_text += sv_icon(icon_name, kleur='wit', use='button')
    new_text += '</span>\n'

    new_text += tekst

    return mark_safe(new_text)


# end of file
