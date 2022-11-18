# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from Bestel.operations.mandje import eval_mandje_inhoud
from Plein.menu import menu_dynamics
from Wedstrijden.models import Wedstrijd, WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_STATUS_GEANNULEERD
from datetime import date, timedelta


TEMPLATE_KALENDER_MAAND = 'kalender/overzicht-maand.dtl'

MAANDEN = (
    (1, 'januari', 'jan'),
    (2, 'februari', 'feb'),
    (3, 'maart', 'mrt'),
    (4, 'april', 'apr'),
    (5, 'mei', 'mei'),
    (6, 'juni', 'jun'),
    (7, 'juli', 'jul'),
    (8, 'augustus', 'aug'),
    (9, 'september', 'sep'),
    (10, 'oktober', 'okt'),
    (11, 'november', 'nov'),
    (12, 'december', 'dec')
)

MAAND2URL = {
    1: 'januari',
    2: 'februari',
    3: 'maart',
    4: 'april',
    5: 'mei',
    6: 'juni',
    7: 'juli',
    8: 'augustus',
    9: 'september',
    10: 'oktober',
    11: 'november',
    12: 'december'
}


def get_url_eerstvolgende_maand_met_wedstrijd():
    """ Geeft de URL terug voor de eerstvolgende maand met een wedstrijd """
    now = timezone.now()

    # default
    jaar = now.year
    maand = now.month

    # we willen in de eerstvolgende maand komen met een wedstrijd
    wedstrijden = (Wedstrijd
                   .objects
                   .filter(status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                           datum_begin__gte=now)
                   .order_by('datum_begin'))

    for wedstrijd in wedstrijden:
        deadline = wedstrijd.datum_begin - timedelta(days=wedstrijd.inschrijven_tot)
        if now.date() <= deadline:
            # hier kan nog op ingeschreven worden
            jaar = wedstrijd.datum_begin.year
            maand = wedstrijd.datum_begin.month
            break
    # for

    url = reverse('Kalender:maand',
                  kwargs={'jaar': jaar,
                          'maand': MAAND2URL[maand]})

    return url


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
    def _get_prev_next_urls(jaar, maand):
        prev_jaar = jaar
        prev_maand = maand - 1
        if prev_maand < 1:
            prev_maand += 12
            prev_jaar -= 1
        url_prev = reverse('Kalender:maand',
                           kwargs={'jaar': prev_jaar,
                                   'maand': MAAND2URL[prev_maand]})

        next_jaar = jaar
        next_maand = maand + 1
        if next_maand > 12:
            next_maand -= 12
            next_jaar += 1
        url_next = reverse('Kalender:maand',
                           kwargs={'jaar': next_jaar,
                                   'maand': MAAND2URL[next_maand]})

        return url_prev, url_next

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        jaar = kwargs['jaar']                           # int
        maand = self._maand_to_nr(kwargs['maand'])      # str
        self._validate_jaar_maand(jaar, maand)

        context['datum'] = date(year=jaar, month=maand, day=1)
        context['url_prev_maand'], context['url_next_maand'] = self._get_prev_next_urls(jaar, maand)

        datum_vanaf = date(year=jaar, month=maand, day=1)
        if maand == 12:
            maand = 1
            jaar += 1
        else:
            maand += 1
        datum_voor = date(year=jaar, month=maand, day=1)

        now_date = timezone.now().date()

        context['wedstrijden'] = wedstrijden = (Wedstrijd
                                                .objects
                                                .select_related('locatie')
                                                .filter(datum_begin__gte=datum_vanaf,
                                                        datum_begin__lt=datum_voor,
                                                        status__in=(WEDSTRIJD_STATUS_GEACCEPTEERD,
                                                                    WEDSTRIJD_STATUS_GEANNULEERD))
                                                .order_by('datum_begin'))

        for wed in wedstrijden:
            if wed.status == WEDSTRIJD_STATUS_GEANNULEERD:
                wed.titel = '[GEANNULEERD] ' + wed.titel
            else:
                wed.url_details = reverse('Wedstrijden:wedstrijd-details',
                                          kwargs={'wedstrijd_pk': wed.pk})

            wed.inschrijven_voor = wed.datum_begin - timedelta(days=wed.inschrijven_tot)
            wed.inschrijven_dagen = (wed.inschrijven_voor - now_date).days
            wed.inschrijven_let_op = (wed.inschrijven_dagen <= 7)
            wed.kan_inschrijven = (now_date < wed.inschrijven_voor)
        # for

        context['kan_aanmelden'] = self.request.user.is_authenticated

        # bepaal of het knopje voor het mandje getoond moet worden
        if self.request.user.is_authenticated:
            eval_mandje_inhoud(self.request)

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (None, 'Wedstrijdkalender'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
