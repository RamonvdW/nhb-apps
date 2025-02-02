# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models.query_utils import Q
from Bestelling.operations.mandje import eval_mandje_inhoud
from Evenement.definities import EVENEMENT_STATUS_GEACCEPTEERD, EVENEMENT_STATUS_GEANNULEERD
from Evenement.models import Evenement
from Kalender.definities import MAANDEN, MAAND2URL
from Kalender.view_helpers import (maak_soort_filter, maak_bogen_filter, maak_discipline_filter,
                                   maak_compacte_wanneer_str, split_zoek_urls)
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD,
                                    ORGANISATIE_IFAA, ORGANISATIE_WA, ORGANISATIE_KHSN,
                                    WEDSTRIJD_WA_STATUS_A, WEDSTRIJD_WA_STATUS_B,
                                    url2discipline)
from Wedstrijden.models import Wedstrijd
from datetime import date, timedelta

TEMPLATE_KALENDER_JAAR = 'kalender/overzicht-jaar.dtl'


class KalenderJaarView(TemplateView):

    """ Via deze view krijgen gebruikers en sporters de wedstrijdkalender te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_JAAR

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
        context['url_prev'] = reverse('Kalender:jaar',
                                      kwargs={'jaar': prev_jaar,
                                              'maand': MAAND2URL[prev_maand],
                                              'soort': '~1',
                                              'bogen': '~2',
                                              'discipline': '~3'})

        next_jaar = jaar
        next_maand = maand + 1
        if next_maand > 12:
            next_maand -= 12
            next_jaar += 1
        context['url_next'] = reverse('Kalender:jaar',
                                      kwargs={'jaar': next_jaar,
                                              'maand': MAAND2URL[next_maand],
                                              'soort': '~1',
                                              'bogen': '~2',
                                              'discipline': '~3'})

    def _maak_pagina(self, context, jaar, maand, gekozen_soort, gekozen_bogen, gekozen_discipline, zoekterm):
        # url voor het insturen van de filter keuzes met een POST
        context['url_keuzes'] = reverse('Kalender:jaar',
                                        kwargs={'jaar': jaar,
                                                'maand': MAAND2URL[maand],
                                                'soort': '~1',
                                                'bogen': '~2',
                                                'discipline': '~3'})

        context['url_toon_maand'] = reverse('Kalender:maand',
                                            kwargs={'jaar': jaar,
                                                    'maand': MAAND2URL[maand],
                                                    'soort': gekozen_soort,
                                                    'bogen': gekozen_bogen,
                                                    'discipline': gekozen_discipline})

        if zoekterm:
            # url voor het resetten van de filter keuzes en zoekterm
            context['unfiltered_url'] = reverse('Kalender:jaar',
                                                kwargs={'jaar': jaar,
                                                        'maand': maand,
                                                        'soort': 'alle',
                                                        'bogen': 'alle',
                                                        'discipline': 'alle'})

        self._maak_prev_next(context, jaar, maand)

        # bepaal de datum-range
        datum_vanaf = date(year=jaar, month=maand, day=1)
        jaar += 1
        datum_voor = date(year=jaar, month=maand, day=1)

        context['datum_vanaf'] = datum_vanaf
        context['datum_tot'] = datum_voor

        wedstrijden = (Wedstrijd
                       .objects
                       .select_related('locatie')
                       .exclude(toon_op_kalender=False)
                       .filter(datum_begin__gte=datum_vanaf,
                               datum_begin__lt=datum_voor,
                               status__in=(WEDSTRIJD_STATUS_GEACCEPTEERD,
                                           WEDSTRIJD_STATUS_GEANNULEERD)))

        evenementen = (Evenement
                       .objects
                       .select_related('locatie')
                       .filter(datum__gte=datum_vanaf,
                               datum__lt=datum_voor,
                               status__in=(EVENEMENT_STATUS_GEACCEPTEERD,
                                           EVENEMENT_STATUS_GEANNULEERD)))

        context['zoekterm'] = zoekterm
        if zoekterm:
            wedstrijden = wedstrijden.filter(Q(titel__icontains=zoekterm) | Q(locatie__plaats__icontains=zoekterm))
            evenementen = evenementen.filter(Q(titel__icontains=zoekterm) | Q(locatie__plaats__icontains=zoekterm))

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

        if gekozen_discipline != 'alle':
            discipline = url2discipline[gekozen_discipline]
            wedstrijden = wedstrijden.filter(discipline=discipline)
            evenementen = list()

        now_date = timezone.now().date()

        context['regels'] = regels = list()
        aantal_wedstrijden = 0
        aantal_evenementen = 0

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

            if wed.inschrijven_dagen < -30:
                wed.is_ter_info = True

            tup = (wed.datum_begin, wed.pk, wed)
            regels.append(tup)
            aantal_wedstrijden += 1
        # for

        for evenement in evenementen:
            if evenement.status == EVENEMENT_STATUS_GEANNULEERD:
                evenement.titel = '[GEANNULEERD] ' + evenement.titel
            else:
                evenement.url_details = reverse('Evenement:details',
                                                kwargs={'evenement_pk': evenement.pk})

            evenement.wanneer_str = maak_compacte_wanneer_str(evenement.datum, evenement.datum)
            evenement.inschrijven_voor = evenement.datum - timedelta(days=evenement.inschrijven_tot)
            evenement.inschrijven_dagen = (evenement.inschrijven_voor - now_date).days
            evenement.inschrijven_let_op = (evenement.inschrijven_dagen <= 7)
            evenement.is_voor_sluitingsdatum = (now_date < evenement.inschrijven_voor)

            if evenement.inschrijven_dagen < -30:
                evenement.is_ter_info = True

            tup = (evenement.datum, evenement.pk, evenement)
            regels.append(tup)
            aantal_evenementen += 1
        # for

        regels.sort()
        context['regels'] = [regel[-1] for regel in regels]

        aantallen = '%s wedstrijd' % aantal_wedstrijden
        if aantal_wedstrijden != 1:
            aantallen += 'en'
        if aantal_evenementen > 0:
            aantallen += ' en %s evenement' % aantal_evenementen
            if aantal_evenementen != 1:
                aantallen += 'en'
        aantallen += ' gevonden'
        context['aantallen'] = aantallen

        # avoid google indexing (and complaining about) urls with ~1 and ~2 in them
        split_zoek_urls(context)

        context['kan_aanmelden'] = self.request.user.is_authenticated
        context['canonical'] = reverse('Kalender:landing-page')

        # bepaal of het knopje voor het mandje getoond moet worden
        if self.request.user.is_authenticated:
            context['menu_toon_mandje'] = True
            eval_mandje_inhoud(self.request)

        context['robots'] = 'nofollow'   # prevent crawling linked pages (we provide a sitemap for events+matches)

        context['kruimels'] = (
            (None, 'Kalender'),
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

        if 'discipline' in kwargs:
            gekozen_discipline = kwargs['discipline']
            # langste: 'run-archery'
            gekozen_discipline = gekozen_discipline[:11]        # afkappen voor de veiligheid
        else:
            gekozen_discipline = 'alle'
        gekozen_discipline = maak_discipline_filter(context, gekozen_discipline)

        zoekterm = self.request.GET.get('zoek', '')
        zoekterm = str(zoekterm)[:50]   # afkappen voor de veiligheid

        self._maak_pagina(context, jaar, maand, gekozen_soort, gekozen_bogen, gekozen_discipline, zoekterm)

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

        if 'discipline' in kwargs:
            gekozen_discipline = kwargs['discipline']
            gekozen_discipline = gekozen_discipline[:11]    # afkappen voor de veiligheid
        else:
            gekozen_discipline = 'alle'
        gekozen_discipline = maak_discipline_filter(context, gekozen_discipline)

        zoekterm = request.POST.get('zoekterm', '')
        zoekterm = zoekterm[:50]    # afkappen voor de veiligheid
        context['zoekterm'] = zoekterm

        self._maak_pagina(context, jaar, maand, gekozen_soort, gekozen_bogen, gekozen_discipline, zoekterm)

        return render(request, self.template_name, context)

# end of file
