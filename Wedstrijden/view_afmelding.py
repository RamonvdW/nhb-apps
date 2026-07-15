# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import GESLACHT2STR
from Bestelling.operations import (bestel_mutatieverzoek_afmelden_wedstrijd,
                                   bestel_mutatieverzoek_verwijder_regel_uit_mandje)
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Sporter.operations import get_sporter_voorkeuren
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE
from Wedstrijden.models import WedstrijdInschrijving, WedstrijdAfgemeld
from Wedstrijden.view_aanmeldingen import get_inschrijving_mh_bestel_nr

TEMPLATE_WEDSTRIJDEN_AFGEMELD_DETAILS = 'wedstrijden/afgemeld-details.dtl'


class AfmeldenView(UserPassesTestMixin, View):

    """ Via deze view kunnen beheerders een sporter afmelden voor een wedstrijd """

    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:7]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = WedstrijdInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, WedstrijdInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        wedstrijd_pk = inschrijving.wedstrijd.pk

        if self.rol_nu != Rol.ROL_MWZ:
            # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
            ver = self.functie_nu.vereniging
            if inschrijving.wedstrijd.organiserende_vereniging != ver:
                raise Http404('Verkeerde vereniging')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            regel = inschrijving.bestelling_regel
            bestel_mutatieverzoek_verwijder_regel_uit_mandje(inschrijving.koper, regel, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel == '1')

        url = reverse('Wedstrijden:aanmeldingen', kwargs={'wedstrijd_pk': wedstrijd_pk})
        url += '#afgemeld'  # toon de lijst met afmeldingen die wat verder op de pagina staat

        return HttpResponseRedirect(url)


class WedstrijdAfgemeldDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een afmelding voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_AFGEMELD_DETAILS
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            afgemeld_pk = str(kwargs['afgemeld_pk'])[:7]     # afkappen voor de veiligheid
            afgemeld_pk = int(afgemeld_pk)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            afgemeld = (WedstrijdAfgemeld
                        .objects
                        .select_related('wedstrijd',
                                        'wedstrijd__organiserende_vereniging',
                                        'wedstrijdklasse',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'korting')
                        .get(pk=afgemeld_pk))
        except (ValueError, WedstrijdAfgemeld.DoesNotExist):
            raise Http404('Afmelding niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            # alleen van de eigen vereniging laten zien
            ver = self.functie_nu.vereniging
            wed = afgemeld.wedstrijd
            if not (wed.organiserende_vereniging == ver or wed.uitvoerende_vereniging == ver):
                raise Http404('Verkeerde vereniging')

        context['afgemeld'] = afgemeld
        context['sporter'] = sporter = afgemeld.sporterboog.sporter
        context['ver'] = sporter.bij_vereniging

        context['voorkeuren'] = voorkeuren = get_sporter_voorkeuren(sporter)
        voorkeuren.wedstrijdgeslacht_str = GESLACHT2STR[voorkeuren.wedstrijd_geslacht]

        afgemeld.reserveringsnummer += settings.TICKET_NUMMER_START__WEDSTRIJD

        afgemeld.bestelnummer_str = get_inschrijving_mh_bestel_nr(afgemeld)

        afgemeld.bedrag_ontvangen_str = format_bedrag_euro(afgemeld.bedrag_ontvangen)
        afgemeld.bedrag_retour_str = format_bedrag_euro(afgemeld.bedrag_retour)

        if afgemeld.korting:
            afgemeld.korting_str = '%s%%' % afgemeld.korting.percentage
        else:
            afgemeld.korting_str = None

        afgemeld.bedrag_ontvangen_str = format_bedrag_euro(afgemeld.bedrag_ontvangen)
        afgemeld.bedrag_retour_str = format_bedrag_euro(afgemeld.bedrag_retour)

        # prijs
        regel = afgemeld.bestelling_regel
        if regel:
            afgemeld.prijs_str = format_bedrag_euro(regel.bedrag_euro)
        else:
            afgemeld.prijs_str = None

        wedstrijd = afgemeld.wedstrijd

        if self.rol_nu == Rol.ROL_MWZ:
            context['kruimels'] = [
                (reverse('Wedstrijden:manager'), 'Beheer wedstrijdkalender'),
            ]
        else:
            # HWL
            context['kruimels'] = [
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            ]

        context['kruimels'].append((reverse('Wedstrijden:aanmeldingen',
                                            kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Aanmeldingen'))
        context['kruimels'].append((None, 'Details afmelding'))

        return context

# end of file
