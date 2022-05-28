# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.mutaties import bestel_mutatieverzoek_afmelden_wedstrijd, bestel_mutatieverzoek_verwijder_product_uit_mandje
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Sporter.models import Sporter
from .models import (KalenderWedstrijd, KalenderInschrijving, INSCHRIJVING_STATUS_TO_SHORT_STR,
                     INSCHRIJVING_STATUS_AFGEMELD, INSCHRIJVING_STATUS_RESERVERING_MANDJE)
from decimal import Decimal


TEMPLATE_KALENDER_AANMELDINGEN = 'kalender/aanmeldingen.dtl'
TEMPLATE_KALENDER_AANMELDINGEN_SPORTER = 'kalender/aanmeldingen-sporter.dtl'


class KalenderAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, KalenderWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        aanmeldingen = (KalenderInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .select_related('sessie',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'gebruikte_code')
                        .order_by('sessie',
                                  'status'))
        context['aanmeldingen'] = aanmeldingen

        totaal_ontvangen_euro = Decimal('000.00')
        totaal_retour_euro = Decimal('000.00')

        aantal_aanmeldingen = 0
        aantal_afmeldingen = 0
        for aanmelding in aanmeldingen:

            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter

            if aanmelding.status != INSCHRIJVING_STATUS_AFGEMELD:
                aantal_aanmeldingen += 1
                aanmelding.volg_nr = aantal_aanmeldingen

                aanmelding.bib = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD
            else:
                aantal_afmeldingen += 1

            aanmelding.status_str = INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status]

            aanmelding.sporter_str = sporter.lid_nr_en_volledige_naam()
            aanmelding.boog_str = sporterboog.boogtype.beschrijving

            aanmelding.korting_str = 'geen'
            if aanmelding.gebruikte_code:
                aanmelding.korting_str = '%s%%' % aanmelding.gebruikte_code.percentage

            aanmelding.url_sporter = reverse('Kalender:details-sporter',
                                             kwargs={'sporter_lid_nr': sporter.lid_nr})

            totaal_ontvangen_euro += aanmelding.ontvangen_euro
            totaal_retour_euro += aanmelding.retour_euro
        # for

        context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen
        context['aantal_afmeldingen'] = aantal_afmeldingen

        if self.rol_nu == Rollen.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Kalender:vereniging'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )
        else:
            context['kruimels'] = (
                (reverse('Kalender:manager'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )

        menu_dynamics(self.request, context)
        return context


class KalenderDetailsSporterView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de details van een inschrijving voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_AANMELDINGEN_SPORTER
    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            sporter_lid_nr = str(kwargs['sporter_lid_nr'])[:6]     # afkappen voor de veiligheid
            sporter_lid_nr = int(sporter_lid_nr)
        except (TypeError, ValueError):
            raise Http404('Geen valide parameter')

        try:
            context['sporter'] = Sporter.objects.get(lid_nr=sporter_lid_nr)
        except Sporter.DoesNotExist:
            raise Http404('Sporter niet gevonden')

        # maak een lijst met transacties van deze sporter
        # - aanmelding/reservering
        # - betaling
        # - afmelding
        # - restitutie
        context['lijst'] = lijst = list()

        inschrijvingen = (KalenderInschrijving
                          .objects
                          .filter(sporterboog__sporter__lid_nr=sporter_lid_nr)
                          .select_related('wedstrijd',
                                          'sessie',
                                          'wedstrijd__organiserende_vereniging',
                                          'sporterboog',
                                          'gebruikte_code'))
        if self.rol_nu != Rollen.ROL_BB:
            # HWL of SEC --> alleen van de eigen vereniging laten zien
            ver = self.functie_nu.nhb_ver
            inschrijvingen.filter(wedstrijd__organiserende_vereniging=ver)

        for inschrijving in inschrijvingen:

            inschrijving.status_str = INSCHRIJVING_STATUS_TO_SHORT_STR[inschrijving.status]

            if inschrijving.status != INSCHRIJVING_STATUS_AFGEMELD:
                inschrijving.url_afmelden = reverse('Kalender:afmelden', kwargs={'inschrijving_pk': inschrijving.pk})

            if inschrijving.gebruikte_code:
                inschrijving.korting_str = '%s%%' % inschrijving.gebruikte_code.percentage
            else:
                inschrijving.korting_str = '-'

            tup = (inschrijving.wanneer, 'I', inschrijving)
            lijst.append(tup)
        # for

        lijst.sort()

        menu_dynamics(self.request, context)
        return context


class AfmeldenView(UserPassesTestMixin, View):

    """ Via deze view kunnen beheerders een sporter afmelden voor een wedstrijd """

    raise_exception = True          # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_BB)

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen om de POST af te handelen"""

        try:
            inschrijving_pk = str(kwargs['inschrijving_pk'])[:6]     # afkappen voor de veiligheid
            inschrijving_pk = int(inschrijving_pk)
            inschrijving = KalenderInschrijving.objects.get(pk=inschrijving_pk)
        except (TypeError, ValueError, KalenderInschrijving.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        if self.rol_nu != Rollen.ROL_BB:
            # controleer dat dit een inschrijving is op een wedstrijd van de vereniging
            ver = self.functie_nu.nhb_ver
            if inschrijving.wedstrijd.organiserende_vereniging != ver:
                raise Http404('Verkeerde vereniging')

        snel = str(request.POST.get('snel', ''))[:1]

        if inschrijving.status == INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            product = inschrijving.bestelproduct_set.all()[0]
            bestel_mutatieverzoek_verwijder_product_uit_mandje(inschrijving.koper, product, snel == '1')
        else:
            bestel_mutatieverzoek_afmelden_wedstrijd(inschrijving, snel == '1')

        sporter_lid_nr = inschrijving.sporterboog.sporter.lid_nr
        url = reverse('Kalender:details-sporter', kwargs={'sporter_lid_nr': sporter_lid_nr})

        return HttpResponseRedirect(url)

# end of file
