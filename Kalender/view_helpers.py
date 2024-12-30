# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpRequest
from django.utils import timezone
from django.utils.formats import localize
from Account.models import get_account
from Kalender.definities import MAAND2URL
from Sporter.models import SporterBoog, get_sporter
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_DISCIPLINES, discipline2url
from Wedstrijden.models import Wedstrijd
from types import SimpleNamespace
from datetime import timedelta


def get_url_eerstvolgende_maand_met_wedstrijd():
    """ Geeft de URL terug voor de eerstvolgende maand met een wedstrijd """
    now = timezone.now()

    # default
    jaar = now.year
    maand = now.month

    # we willen in de eerstvolgende maand komen met een wedstrijd
    wedstrijden = (Wedstrijd
                   .objects
                   .exclude(toon_op_kalender=False)
                   .filter(status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                           datum_begin__gte=now)
                   .order_by('datum_begin'))

    for wedstrijd in wedstrijden:       # pragma: no branch
        deadline = wedstrijd.datum_begin - timedelta(days=wedstrijd.inschrijven_tot)
        if now.date() <= deadline:
            # hier kan nog op ingeschreven worden
            jaar = wedstrijd.datum_begin.year
            maand = wedstrijd.datum_begin.month
            break
    # for

    url = reverse('Kalender:maand',
                  kwargs={'jaar': jaar,
                          'maand': MAAND2URL[maand],
                          'soort': 'alle',
                          'bogen': 'auto',
                          'discipline': 'auto'})

    return url


def maak_compacte_wanneer_str(datum_begin, datum_einde):

    if datum_begin == datum_einde:
        # 5 mei 2022
        wanneer_str = localize(datum_begin)

    elif datum_begin.month == datum_einde.month:

        if datum_einde.day == datum_begin.day + 1:
            # 5 + 6 mei 2022
            wanneer_str = "%s + " % datum_begin.day
        else:
            # 5 - 8 mei 2022
            wanneer_str = "%s - " % datum_begin.day

        wanneer_str += localize(datum_einde)

    else:
        # 30 mei - 2 juni 2022
        wanneer_str = "%s - %s" % (localize(datum_begin),
                                   localize(datum_einde))

    return wanneer_str


def maak_soort_filter(context, gekozen_soort):
    if gekozen_soort not in ('alle', 'wa-a', 'wa-b', 'ifaa', 'khsn'):
        gekozen_soort = 'alle'

    context['soort_filter'] = [
        SimpleNamespace(
            opt_text='Alle',
            sel='s_alle',
            selected=(gekozen_soort == 'alle'),
            url_part='alle'),
        SimpleNamespace(
            opt_text='IFAA',
            sel='s_ifaa',
            selected=(gekozen_soort == 'ifaa'),
            url_part='ifaa'),
        SimpleNamespace(
            opt_text='WA A-status',
            sel='s_wa_a',
            selected=(gekozen_soort == 'wa-a'),
            url_part='wa-a'),
        SimpleNamespace(
            opt_text='WA B-status',
            sel='s_wa_b',
            selected=(gekozen_soort == 'wa-b'),
            url_part='wa-b'),
        SimpleNamespace(
            opt_text='KHSN',
            sel='s_khsn',
            selected=(gekozen_soort == 'khsn'),
            url_part='khsn'),
    ]

    return gekozen_soort


def maak_bogen_filter(request: HttpRequest, context, gekozen_bogen):
    boog_pks = list()
    if request.user.is_authenticated:                               # pragma: no branch
        account = get_account(request)
        sporter = get_sporter(account)
        if sporter and sporter.is_actief_lid:
            boog_pks = list(SporterBoog
                            .objects
                            .filter(sporter=sporter,
                                    heeft_interesse=True)
                            .values_list('boogtype__pk', flat=True))

    context['boog_pks'] = boog_pks

    if len(boog_pks) > 0:
        # transitie van 'auto' naar 'mijn'
        if gekozen_bogen == 'auto':
            gekozen_bogen = 'mijn'
    else:
        # niet ingelogd / geen bogen, dus forceer 'alle'
        gekozen_bogen = 'alle'

    if gekozen_bogen not in ('alle', 'mijn'):
        gekozen_bogen = 'alle'

    context['bogen_filter'] = [
        SimpleNamespace(
            opt_text='Alle',
            sel='b_alle',
            selected=(gekozen_bogen == 'alle'),
            url_part='alle'),
        SimpleNamespace(
            opt_text='Mijn voorkeuren',
            sel='b_mijn',
            selected=(gekozen_bogen == 'mijn'),
            disabled=(len(boog_pks) == 0),
            url_part='mijn'),
    ]

    return gekozen_bogen


def maak_discipline_filter(context, gekozen_discipline):
    """ gekozen_discipline is de URL parameter en kan een van de discipline2url zijn, 'auto' zijn of totale garbage.
        geeft de opgeschoonde gekozen_discipline terug die gebruikt kan worden in reverse() operaties.
    """
    # WEDSTRIJD_DISCIPLINES = (
    #     (WEDSTRIJD_DISCIPLINE_OUTDOOR, 'Outdoor'),
    #     (WEDSTRIJD_DISCIPLINE_INDOOR, 'Indoor'),  # Indoor = 18m/25m 3pijl
    #     (WEDSTRIJD_DISCIPLINE_25M1P, '25m 1pijl'),
    #     (WEDSTRIJD_DISCIPLINE_CLOUT, 'Clout'),
    #     (WEDSTRIJD_DISCIPLINE_VELD, 'Veld'),
    #     (WEDSTRIJD_DISCIPLINE_RUN, 'Run Archery'),
    #     (WEDSTRIJD_DISCIPLINE_3D, '3D')
    # )
    #
    # discipline2url = {
    #     WEDSTRIJD_DISCIPLINE_3D: '3d',
    #     WEDSTRIJD_DISCIPLINE_RUN: 'run-archery',
    #     WEDSTRIJD_DISCIPLINE_VELD: 'veld',
    #     WEDSTRIJD_DISCIPLINE_25M1P: '25m1pijl',
    #     WEDSTRIJD_DISCIPLINE_CLOUT: 'clout',
    #     WEDSTRIJD_DISCIPLINE_INDOOR: 'indoor',
    #     WEDSTRIJD_DISCIPLINE_OUTDOOR: 'outdoor',
    # }
    #
    # url2discipline = {
    #     'run-archery': WEDSTRIJD_DISCIPLINE_RUN,
    #     '25m1pijl': WEDSTRIJD_DISCIPLINE_25M1P,
    #     'outdoor': WEDSTRIJD_DISCIPLINE_OUTDOOR,
    #     'indoor': WEDSTRIJD_DISCIPLINE_INDOOR,
    #     'clout': WEDSTRIJD_DISCIPLINE_CLOUT,
    #     'veld': WEDSTRIJD_DISCIPLINE_VELD,
    #     '3d': WEDSTRIJD_DISCIPLINE_3D,
    # }

    if gekozen_discipline not in discipline2url.keys():
        gekozen_discipline = 'alle'

    context['soort_discipline'] = [
        SimpleNamespace(
            opt_text='Alle',
            sel='s_alle',
            selected=(gekozen_discipline == 'alle'),
            url_part='alle'),
    ]

    for code, text in WEDSTRIJD_DISCIPLINES:
        url_part = discipline2url[code]
        context['soort_discipline'].append(
            SimpleNamespace(
                opt_text=text,
                sel='s_' + code,
                selected=(gekozen_discipline == url_part),
                url_part=url_part)
        )

    return gekozen_discipline


def split_zoek_urls(context: dict):
    """ split context entries waarvan de key begint met url_ en de value ~1 bevat
    """
    for key in context.keys():
        if key.startswith('url_'):
            value = context[key]
            pos = value.find('~1')
            if pos > 0:
                tup = (value[:pos], value[pos:])
                context[key] = tup
    # for


# end of file
