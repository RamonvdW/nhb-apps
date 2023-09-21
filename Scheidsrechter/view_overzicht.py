# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.utils.http import urlencode
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import ORGANISATIE_IFAA
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Plein.menu import menu_dynamics
from Wedstrijden.definities import (WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_ORGANISATIE_TO_STR,
                                    ORGANISATIE_WA, WEDSTRIJD_WA_STATUS_TO_STR,
                                    WEDSTRIJD_BEGRENZING_TO_STR)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie

TEMPLATE_OVERZICHT = 'scheidsrechter/overzicht.dtl'
TEMPLATE_WEDSTRIJDEN = 'scheidsrechter/wedstrijden.dtl'
TEMPLATE_WEDSTRIJD_DETAILS = 'scheidsrechter/wedstrijd-details.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        if self.rol_nu == Rollen.ROL_CS:
            return True
        if self.rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        if self.rol_nu == Rollen.ROL_SPORTER:
            context['url_korps'] = reverse('Scheidsrechter:korps')
        else:
            context['url_korps'] = reverse('Scheidsrechter:korps-met-contactgegevens')

        context['kruimels'] = (
            (None, 'Scheidsrechters'),
        )

        menu_dynamics(self.request, context)
        return context


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_CS:
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        wedstrijden = (Wedstrijd
                       .objects
                       .exclude(status=WEDSTRIJD_STATUS_ONTWERP)
                       .exclude(is_ter_info=True)
                       .exclude(toon_op_kalender=False)
                       .order_by('-datum_begin'))       # nieuwste bovenaan

        for wedstrijd in wedstrijden:
            wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]
            if wedstrijd.organisatie == ORGANISATIE_WA:
                wedstrijd.organisatie_str += ' ' + WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]

            wedstrijd.url_details = reverse('Scheidsrechter:wedstrijd-details',
                                            kwargs={'wedstrijd_pk': wedstrijd.pk})
        # for

        context['wedstrijden'] = wedstrijden

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Wedstrijden')
        )

        menu_dynamics(self.request, context)
        return context


class WedstrijdDetailsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJD_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_CS:
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .exclude(status=WEDSTRIJD_STATUS_ONTWERP)
                         .exclude(is_ter_info=True)
                         .exclude(toon_op_kalender=False)
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]

        wedstrijd.begrenzing_str = WEDSTRIJD_BEGRENZING_TO_STR[wedstrijd.begrenzing]

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

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:wedstrijden'), 'Wedstrijden'),
            (None, 'Details'),
        )

        menu_dynamics(self.request, context)
        return context


# end of file
