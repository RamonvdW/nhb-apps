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
    'account aanmaken': 'fingerprint',
    'account activiteit': 'recent_actors',
    'account wachtwoord vergeten': 'help',
    'account wachtwoord wijzigen': 'lock',
    'account inloggen': 'person',
    'sluiten': 'close',
    'admin': 'database',
    'beheer vereniging': 'house_siding',
    'bestellingen overzicht': 'shopping_cart',
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
    'drive toestemming': 'add_to_drive',
    'drive wedstrijdformulieren maken': 'add_to_drive',
    'email': 'mail',
    'evenement verkoopvoorwaarden': 'article',
    'evenementen': 'article',
    'functie 2fa controle': 'lock',
    'functie 2fa koppel': 'lock',
    'functie 2fa uitleg': 'article',
    'functie beheerders': 'face',
    'functie login as': 'switch_access_shortcut',
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
    'korting combi': 'stack',
    'korting persoonlijk': 'account_circle',
    'korting vereniging': 'home',
    'ledenvoordeel webwinkel': 'shopping_cart',
    'ledenvoordeel': 'redeem',
    'leeftijdsklassen': 'star',
    'logboek': 'book',
    'mandje': 'shopping_cart',
    'mijn bestellingen': 'receipt_long',
    'mijn pagina': 'account_circle',
    'opleiding basiscursus': 'school',
    'opleiding crm overnemen': 'person_add',
    'opleiding instaptoets inzicht': 'insights',
    'opleiding instaptoets niet gehaald': 'thumb_down',
    'opleiding instaptoets niet ingeschreven': 'radar',
    'opleiding instaptoets': 'login',
    'opleiding lesmateriaal': 'book_2',
    'opleiding locaties': 'school',
    'opleiding verkoopvoorwaarden': 'article',
    'opleidingen': 'school',
    'privacyverklaring': 'security',
    'record ander': 'auto_awesome',
    'records filteren': 'filter_alt',
    'records verbeterbaar': 'leaderboard',
    'records zoeken': 'search',
    'records': 'insights',
    'registreer gast': 'explore',
    'registreer lid': 'badge',
    'scheids beschikbaarheid': 'event_available',
    'scheids competitie': 'my_location',
    'scheids handleiding': 'menu_book',
    'scheids kalender': 'event_note',
    'scheids korps': 'star',
    'scheidsrechters': 'sports',
    'score geschiedenis': 'history',
    'scores invoeren': 'edit',
    'site feedback': 'chat',
    'spelden graadspelden': 'zoom_out_map',
    'spelden meesterspelden': 'category',
    'spelden tussenspelden': 'trending_up',
    'sporter voorkeuren': 'tune',
    'taken': 'inbox',
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
    'ver gast accounts': 'import_contacts',
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
