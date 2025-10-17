# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

""" Centrale plaats om vertaling van iconen naar juiste html/css te doen """


# mapping van sv-icon gebruik naar Material Symbol icon name
MATERIAL_SYMBOLS = {
    'aanmaken wedstrijdformulieren': 'add_to_drive',
    'account aanmaken': 'fingerprint',
    'account activiteit': 'recent_actors',
    'admin': 'database',
    'beheer vereniging': 'store',
    'beheerders': 'face',
    'bestellingen overzicht': 'shopping_cart',
    'bondscompetities': 'my_location',
    'bondspas': 'id_card',
    'comp beheer': 'store',
    'comp info indiv': 'info',
    'comp info teams': 'groups',
    'comp scores deelnemers': 'add',
    'email': 'mail',
    'evenementen': 'article',
    'functie 2fa controle': 'lock',
    'functie 2fa koppel': 'lock',
    'functie 2fa uitleg': 'article',
    'functie vhpg inzien': 'gavel',
    'functie vhpg status': 'verified_user',
    'functie vhpg': 'gavel',
    'functie wissel sec': 'help',
    'functie wissel': 'switch_access_shortcut',
    'handleiding': 'menu_book',
    'het plein': 'hub',
    'histcomp': 'undo',
    'inschrijven familie': 'family_restroom',
    'inschrijven group': 'group',
    'inschrijven sporter': 'person',
    'interland lijst': 'flag',
    'kalender': 'event_note',
    'korting combi': 'stack',
    'korting persoonlijk': 'account_circle',
    'korting vereniging': 'home',
    'leeftijdsklassen': 'star',
    'logboek': 'book',
    'mandje': 'shopping_cart',
    'mijn bestellingen': 'receipt_long',
    'mijn-pagina': 'account_circle',
    'opleiding basiscursus': 'school',
    'opleiding crm overnemen': 'person_add',
    'opleiding instaptoets inzicht': 'insights',
    'opleiding instaptoets niet gehaald': 'thumb_down',
    'opleiding instaptoets niet ingeschreven': 'radar',
    'opleiding instaptoets': 'login',
    'opleiding lesmateriaal': 'book_2',
    'opleiding locaties': 'school',
    'opleiding voorwaarden': 'article',
    'opleidingen': 'school',
    'privacyverklaring': 'article',
    'rcl team scores': 'gavel',
    'records filteren': 'filter_alt',
    'records verbeterbaar': 'leaderboard',
    'records zoeken': 'search',
    'records': 'insights',
    'registreer gast engels': 'public',
    'registreer gast': 'explore',
    'registreer lid': 'badge',
    'scheidsrechters': 'sports',
    'scheids beschikbaarheid': 'event_available',
    'scheids competitie': 'my_location',
    'scheids handleiding': 'article',
    'scheids kalender': 'event_note',
    'scheids korps': 'star',
    'score geschiedenis': 'history',
    'scores invoeren': 'edit',
    'seizoen afsluiten': 'waving_hand',
    'site feedback': 'chat',
    'spelden graadspelden': 'zoom_out_map',
    'spelden meesterspelden': 'category',
    'spelden tussenspelden': 'trending_up',
    'sporter voorkeuren': 'tune',
    'start competitie': 'playlist_add',
    'statistiek': 'query_stats',
    'taken': 'inbox',
    'tijdlijn': 'schedule',
    'toestemming google drive': 'add_to_drive',
    'uitloggen': 'logout',
    'uitslag bk indiv': 'flag',
    'uitslag bk teams': 'flag',
    'uitslag regio indiv': 'view_compact',
    'uitslag regio teams': 'view_compact',
    'uitslag rk indiv': 'view_comfy',
    'uitslag rk teams': 'view_comfy',
    'ver accommodatie': 'account_balance',
    'ver beheerders': 'supervisor_account',
    'ver evenement locaties': 'school',
    'ver ext crm': 'group',
    'ver externe locaties': 'hike',
    'ver gast accounts': 'import_contacts',
    'ver ledenlijst': 'import_contacts',
    'ver mollie': 'settings',
    'ver overboekingen': 'euro_symbol',
    'ver voorkeuren': 'tune',
    'ver voorwaarden': 'article',
    'verder winkelen': 'event_note',
    'verenigingen': 'share_location',
    'wachtwoord vergeten': 'help',
    'walibi webshop': 'shopping_cart',
    'webwinkel voorraad': 'inventory',
    'webwinkel': 'local_mall',
    'wedstrijdklassen': 'equalizer',
    'wissel-van-rol': 'group',
    'ledenvoordeel': 'redeem',
    'zoek vereniging': 'travel_explore',
}


@register.simple_tag(name='sv-icon')
def sv_icon(icon_name, kleur='sv-rood-text', icon_height='', extra_class='', extra_style=''):

    # zoek het bijbehorende Material Symbol op
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

    if extra_style or icon_height:
        new_text += '" style="' + extra_style

        if icon_height:
            new_text += '; font-size:' + icon_height

    new_text += '">' + material_symbol + '</i>'

    return mark_safe(new_text)


# end of file
