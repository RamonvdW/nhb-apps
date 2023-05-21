# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView
from Bestel.operations.mandje import eval_mandje_inhoud
from Kalender.definities import MAANDEN, MAAND2URL
from Kalender.view_maand import maak_soort_filter, maak_compacte_wanneer_str
from Plein.menu import menu_dynamics
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD,
                                    ORGANISATIE_IFAA, ORGANISATIE_WA, WEDSTRIJD_WA_STATUS_A, WEDSTRIJD_WA_STATUS_B)
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
        context['arg_prev'] = '%s-%s' % (prev_jaar, prev_maand)

        next_jaar = jaar
        next_maand = maand + 1
        if next_maand > 12:
            next_maand -= 12
            next_jaar += 1
        context['arg_next'] = '%s-%s' % (next_jaar, next_maand)

    def _maak_pagina(self, context, jaar, maand, zoekterm):

        # url voor het insturen van de filter keuzes met een POST
        context['url_keuzes'] = reverse('Kalender:jaar',
                                        kwargs={'jaar': jaar, 'maand': MAAND2URL[maand]})

        context['url_toon_maand'] = reverse('Kalender:maand', kwargs={'jaar': jaar, 'maand': MAAND2URL[maand]})

        # bepaal de datum-range
        datum_vanaf = date(year=jaar, month=maand, day=1)
        datum_voor = date(year=jaar + 1, month=maand, day=1)

        context['datum_vanaf'] = datum_vanaf
        context['datum_tot'] = datum_voor

        self._maak_prev_next(context, jaar, maand)

        wedstrijden = (Wedstrijd
                       .objects
                       .select_related('locatie')
                       .exclude(toon_op_kalender=False)
                       .filter(datum_begin__gte=datum_vanaf,
                               datum_begin__lt=datum_voor,
                               status__in=(WEDSTRIJD_STATUS_GEACCEPTEERD,
                                           WEDSTRIJD_STATUS_GEANNULEERD))
                       .order_by('datum_begin'))

        context['zoekterm'] = zoekterm
        if zoekterm:
            wedstrijden = wedstrijden.filter(titel__icontains=zoekterm)

            # url voor het resetten van de filter keuzes en zoekterm
            context['url_toon_alles'] = context['url_keuzes']

        # verder verkleinen
        gekozen_soort = context['gekozen_soort']

        if gekozen_soort == 'ifaa':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_IFAA)

        elif gekozen_soort == 'wa_a':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_WA,
                                             wa_status=WEDSTRIJD_WA_STATUS_A)

        elif gekozen_soort == 'wa_b':
            wedstrijden = wedstrijden.filter(organisatie=ORGANISATIE_WA,
                                             wa_status=WEDSTRIJD_WA_STATUS_B)

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
            wed.kan_inschrijven = (now_date < wed.inschrijven_voor)
        # for

        context['wedstrijden'] = wedstrijden
        context['kan_aanmelden'] = self.request.user.is_authenticated

        # bepaal of het knopje voor het mandje getoond moet worden
        if self.request.user.is_authenticated:
            context['menu_toon_mandje'] = True
            eval_mandje_inhoud(self.request)

        context['kruimels'] = (
            (None, 'Wedstrijdkalender'),
        )

        menu_dynamics(self.request, context)
        return context

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        jaar = kwargs['jaar']                           # int
        maand = self._maand_to_nr(kwargs['maand'])      # str
        self._validate_jaar_maand(jaar, maand)

        soort = ''
        maak_soort_filter(context, soort)

        zoekterm = ''
        self._maak_pagina(context, jaar, maand, zoekterm)

        return context

    def post(self, request, *args, **kwargs):
        jaar = kwargs['jaar']  # int
        maand = self._maand_to_nr(kwargs['maand'])  # str

        # ondersteuning voor springen naar een ander jaar/maand
        arg = request.POST.get('arg', '')
        arg = arg[:10]  # afkappen voor de veiligheid
        if arg:
            # format: jaar-maand
            spl = arg.split('-')
            if len(spl) == 2:
                try:
                    arg1 = int(spl[0])
                    arg2 = int(spl[1])
                except ValueError:
                    pass
                else:
                    jaar, maand = arg1, arg2

        self._validate_jaar_maand(jaar, maand)

        context = dict()

        soort = request.POST.get('soort', '')
        soort = soort[:6]       # afkappen voor de veiligheid
        maak_soort_filter(context, soort)

        zoekterm = request.POST.get('zoekterm', '')
        zoekterm = zoekterm[:50]    # afkappen voor de veiligheid
        context['zoekterm'] = zoekterm

        self._maak_pagina(context, jaar, maand, zoekterm)

        return render(request, self.template_name, context)


# end of file
