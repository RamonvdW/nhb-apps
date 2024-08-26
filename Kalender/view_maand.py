# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.http import HttpRequest
from django.utils import timezone
from django.shortcuts import render
from django.utils.formats import localize
from django.views.generic import TemplateView
from django.db.models.query_utils import Q
from Account.models import get_account
from Bestel.operations.mandje import eval_mandje_inhoud
from Kalender.definities import MAANDEN, MAAND2URL
from Sporter.models import SporterBoog, get_sporter
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD,
                                    ORGANISATIE_IFAA, ORGANISATIE_WA, ORGANISATIE_KHSN,
                                    WEDSTRIJD_WA_STATUS_A, WEDSTRIJD_WA_STATUS_B)
from Wedstrijden.models import Wedstrijd
from datetime import date, timedelta
from types import SimpleNamespace

TEMPLATE_KALENDER_MAAND = 'kalender/overzicht-maand.dtl'


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
                          'bogen': 'auto'})

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

    context['gekozen_soort'] = gekozen_soort

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


class KalenderMaandView(TemplateView):

    """ Via deze view krijgen gebruikers en sporters de wedstrijdkalender te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_MAAND

    @staticmethod
    def _maand_to_nr(maand_str):
        maand_str = maand_str[:15].lower()      # afkappen voor de veiligheid

        for maand_nr, str1, str2 in MAANDEN:
            if maand_str == str1 or maand_str == str2:
                return maand_nr
        # for

        try:
            maand_nr = int(maand_str)
        except ValueError:
            pass
        else:
            return maand_nr

        raise Http404('Geen valide maand')

    @staticmethod
    def _validate_jaar_maand(jaar, maand):
        if not (2020 <= jaar <= 2050 and 1 <= maand <= 12):
            raise Http404('Geen valide jaar / maand combinatie')

    @staticmethod
    def _maak_prev_next(context, jaar, maand):
        prev_jaar = jaar
        prev_maand = maand - 1
        if prev_maand < 1:
            prev_maand += 12
            prev_jaar -= 1
        context['url_prev'] = reverse('Kalender:maand',
                                      kwargs={'jaar': prev_jaar,
                                              'maand': MAAND2URL[prev_maand],
                                              'soort': '~1',
                                              'bogen': '~2'})

        next_jaar = jaar
        next_maand = maand + 1
        if next_maand > 12:
            next_maand -= 12
            next_jaar += 1
        context['url_next'] = reverse('Kalender:maand',
                                      kwargs={'jaar': next_jaar,
                                              'maand': MAAND2URL[next_maand],
                                              'soort': '~1',
                                              'bogen': '~2'})

    def _maak_pagina(self, context, jaar, maand, gekozen_soort, gekozen_bogen, zoekterm):
        # url voor het insturen van de filter keuzes met een POST
        context['url_keuzes'] = reverse('Kalender:maand',
                                        kwargs={'jaar': jaar,
                                                'maand': MAAND2URL[maand],
                                                'soort': '~1',
                                                'bogen': '~2'})

        context['url_toon_jaar'] = reverse('Kalender:jaar',
                                           kwargs={'jaar': jaar,
                                                   'maand': MAAND2URL[maand],
                                                   'soort': gekozen_soort,
                                                   'bogen': gekozen_bogen})

        if zoekterm:
            # url voor het resetten van de filter keuzes en zoekterm
            context['url_toon_alles'] = reverse('Kalender:maand',
                                                kwargs={'jaar': jaar,
                                                        'maand': maand,
                                                        'soort': 'alle',
                                                        'bogen': 'alle'})

        self._maak_prev_next(context, jaar, maand)

        # bepaal de datum-range voor deze maand
        datum_vanaf = date(year=jaar, month=maand, day=1)
        if maand == 12:
            maand = 1
            jaar += 1
        else:
            maand += 1
        datum_voor = date(year=jaar, month=maand, day=1)

        context['datum'] = datum_vanaf

        wedstrijden = (Wedstrijd
                       .objects
                       .select_related('locatie')
                       .exclude(toon_op_kalender=False)
                       .filter(datum_begin__gte=datum_vanaf,
                               datum_begin__lt=datum_voor,
                               status__in=(WEDSTRIJD_STATUS_GEACCEPTEERD,
                                           WEDSTRIJD_STATUS_GEANNULEERD))
                       .order_by('datum_begin',
                                 'pk'))     # ingeval van gelijke datum

        context['zoekterm'] = zoekterm
        if zoekterm:
            wedstrijden = wedstrijden.filter(Q(titel__icontains=zoekterm) | Q(locatie__plaats__icontains=zoekterm))

        # filter wedstrijden op organisatie ("soort wedstrijd")
        if gekozen_soort == 'ifaa':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_IFAA)

        elif gekozen_soort == 'wa-a':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_WA,
                                             wa_status=WEDSTRIJD_WA_STATUS_A)

        elif gekozen_soort == 'wa-b':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_WA,
                                             wa_status=WEDSTRIJD_WA_STATUS_B)

        elif gekozen_soort == 'khsn':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_KHSN)

        # filter wedstrijden op bogen
        if gekozen_bogen != 'alle':
            boog_pks = context['boog_pks']      # ingevuld in maak_bogen_filter en gegarandeerd niet leeg
            # distinct is nodig om verdubbeling te voorkomen
            wedstrijden = wedstrijden.filter(boogtypen__pk__in=boog_pks).distinct('datum_begin', 'pk')

        now_date = timezone.now().date()

        for wed in wedstrijden:
            if wed.status == WEDSTRIJD_STATUS_GEANNULEERD:
                wed.titel = '[GEANNULEERD] ' + wed.titel
            else:
                wed.url_details = reverse('Wedstrijden:wedstrijd-details',
                                          kwargs={'wedstrijd_pk': wed.pk})

            wed.wanneer_str = maak_compacte_wanneer_str(wed.datum_begin, wed.datum_einde)
            wed.inschrijven_voor = wed.datum_begin - timedelta(days=wed.inschrijven_tot)
            wed.inschrijven_dagen = (wed.inschrijven_voor - now_date).days
            wed.inschrijven_let_op = (wed.inschrijven_dagen <= 7)
            wed.is_voor_sluitingsdatum = (now_date < wed.inschrijven_voor)
        # for

        context['wedstrijden'] = wedstrijden
        context['aantal_wedstrijden'] = len(wedstrijden)
        context['kan_aanmelden'] = self.request.user.is_authenticated
        context['canonical'] = reverse('Kalender:landing-page')

        # bepaal of het knopje voor het mandje getoond moet worden
        if self.request.user.is_authenticated:
            context['menu_toon_mandje'] = True
            eval_mandje_inhoud(self.request)

        context['kruimels'] = (
            (None, 'Wedstrijdkalender'),
        )

        return context

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        jaar = kwargs['jaar']                           # int
        maand = self._maand_to_nr(kwargs['maand'])      # str
        self._validate_jaar_maand(jaar, maand)

        if 'soort' in kwargs:
            gekozen_soort = kwargs['soort']
            gekozen_soort = gekozen_soort[:6]       # afkappen voor de veiligheid
        else:
            gekozen_soort = 'alle'
        gekozen_soort = maak_soort_filter(context, gekozen_soort)

        if 'bogen' in kwargs:
            gekozen_bogen = kwargs['bogen']
            gekozen_bogen = gekozen_bogen[:6]       # afkappen voor de veiligheid
        else:
            gekozen_bogen = 'auto'
        gekozen_bogen = maak_bogen_filter(self.request, context, gekozen_bogen)

        zoekterm = self.request.GET.get('zoek', '')
        zoekterm = str(zoekterm)[:50]   # afkappen voor de veiligheid
        self._maak_pagina(context, jaar, maand, gekozen_soort, gekozen_bogen, zoekterm)

        return context

    def post(self, request, *args, **kwargs):
        context = dict()

        jaar = kwargs['jaar']  # int
        maand = self._maand_to_nr(kwargs['maand'])
        self._validate_jaar_maand(jaar, maand)

        gekozen_soort = kwargs['soort']
        gekozen_soort = gekozen_soort[:6]           # afkappen voor de veiligheid
        gekozen_soort = maak_soort_filter(context, gekozen_soort)

        gekozen_bogen = kwargs['bogen']
        gekozen_bogen = gekozen_bogen[:6]           # afkappen voor de veiligheid
        gekozen_bogen = maak_bogen_filter(request, context, gekozen_bogen)

        zoekterm = request.POST.get('zoekterm', '')
        zoekterm = zoekterm[:50]    # afkappen voor de veiligheid
        context['zoekterm'] = zoekterm

        self._maak_pagina(context, jaar, maand, gekozen_soort, gekozen_bogen, zoekterm)

        return render(request, self.template_name, context)


# end of file
