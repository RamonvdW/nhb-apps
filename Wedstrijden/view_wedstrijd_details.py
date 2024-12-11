# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import TemplateView
from BasisTypen.definities import ORGANISATIE_WA, ORGANISATIE_IFAA
from Kalender.view_maand import MAAND2URL
from Wedstrijden.definities import (WEDSTRIJD_ORGANISATIE_TO_STR, WEDSTRIJD_BEGRENZING_TO_STR,
                                    WEDSTRIJD_WA_STATUS_TO_STR)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie
from datetime import timedelta


TEMPLATE_WEDSTRIJDEN_WEDSTRIJD_DETAILS = 'wedstrijden/wedstrijd-details.dtl'


class WedstrijdDetailsView(TemplateView):

    """ Via deze view krijgen sporters de details van een wedstrijd te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_WEDSTRIJD_DETAILS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd.uitslag_urls = (wedstrijd.url_uitslag_1, wedstrijd.url_uitslag_2,
                                  wedstrijd.url_uitslag_3, wedstrijd.url_uitslag_4)

        now_date = timezone.now().date()

        wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]

        wedstrijd.begrenzing_str = WEDSTRIJD_BEGRENZING_TO_STR[wedstrijd.begrenzing]

        wedstrijd.inschrijven_voor = wedstrijd.datum_begin - timedelta(days=wedstrijd.inschrijven_tot)
        wedstrijd.inschrijven_dagen = (wedstrijd.inschrijven_voor - now_date).days
        wedstrijd.inschrijven_let_op = (wedstrijd.inschrijven_dagen <= 7)

        if wedstrijd.organisatie == ORGANISATIE_WA:
            context['toon_wa_status'] = True
            wedstrijd.wa_status_str = WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]

        toon_kaart = wedstrijd.locatie.plaats != '(diverse)' and wedstrijd.locatie.adres != '(diverse)'
        if toon_kaart:
            zoekterm = wedstrijd.locatie.adres
            if wedstrijd.locatie.adres_uit_crm:
                # voeg de naam van de vereniging toe aan de zoekterm, voor beter resultaat
                zoekterm = wedstrijd.organiserende_vereniging.naam + ' ' + zoekterm
            zoekterm = zoekterm.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
            context['url_map'] = 'https://google.nl/maps?' + urlencode({'q': zoekterm})

        sessie_pks = list(wedstrijd.sessies.values_list('pk', flat=True))
        context['sessies'] = sessies = (WedstrijdSessie
                                        .objects
                                        .filter(pk__in=sessie_pks)
                                        .prefetch_related('wedstrijdklassen')
                                        .order_by('datum',
                                                  'tijd_begin',
                                                  'pk'))

        heeft_sessies = False
        for sessie in sessies:
            heeft_sessies = True
            sessie.aantal_beschikbaar = sessie.max_sporters - sessie.aantal_inschrijvingen
            sessie.klassen = sessie.wedstrijdklassen.order_by('volgorde')

            if wedstrijd.organisatie == ORGANISATIE_IFAA:
                # voeg afkorting toe aan klasse beschrijving
                for klasse in sessie.klassen:
                    klasse.beschrijving += ' [%s]' % klasse.afkorting
                # for
        # for
        context['toon_sessies'] = heeft_sessies

        # inschrijven moet voor de sluitingsdatum
        context['is_voor_sluitingsdatum'] = now_date < wedstrijd.inschrijven_voor

        context['kan_aanmelden'] = False
        context['hint_inloggen'] = False

        if not wedstrijd.extern_beheerd:
            # om aan te melden is een account nodig
            # extern beheerder wedstrijden kan je niet voor aanmelden
            # een wedstrijd zonder sessie is een placeholder op de agenda
            context['kan_aanmelden'] = self.request.user.is_authenticated
            context['hint_inloggen'] = not self.request.user.is_authenticated

        if context['kan_aanmelden']:
            context['menu_toon_mandje'] = True

            if context['is_voor_sluitingsdatum']:
                context['url_inschrijven_sporter'] = reverse('WedstrijdInschrijven:inschrijven-sporter',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
                context['url_inschrijven_groepje'] = reverse('WedstrijdInschrijven:inschrijven-groepje',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})
                context['url_inschrijven_familie'] = reverse('WedstrijdInschrijven:inschrijven-familie',
                                                             kwargs={'wedstrijd_pk': wedstrijd.pk})

        # inschrijf sectie (kaartjes) tonen voor deze wedstrijd?
        context['toon_inschrijven'] = False
        if not wedstrijd.is_ter_info:
            if wedstrijd.extern_beheerd and wedstrijd.contact_website:
                context['toon_inschrijven'] = context['is_voor_sluitingsdatum']
            elif heeft_sessies:
                context['toon_inschrijven'] = context['is_voor_sluitingsdatum']

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month],
                                    'soort': 'alle',
                                    'bogen': 'auto'})
        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (None, 'Wedstrijd details'),
        )

        return context


# end of file
