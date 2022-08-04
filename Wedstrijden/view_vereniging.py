# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import (GESLACHT_ALLE,
                               ORGANISATIE_WA, ORGANISATIE_IFAA, ORGANISATIE_NHB, ORGANISATIES2SHORT_STR)
from BasisTypen.operations import get_organisatie_boogtypen, get_organisatie_klassen
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Plein.menu import menu_dynamics
from Wedstrijden.models import (Wedstrijd,
                                WEDSTRIJD_DISCIPLINE_3D, ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS, WEDSTRIJD_STATUS_TO_STR)
from datetime import date

TEMPLATE_WEDSTRIJDEN_KIES_TYPE = 'wedstrijden/nieuwe-wedstrijd-kies-type.dtl'
TEMPLATE_WEDSTRIJDEN_OVERZICHT_VERENIGING = 'wedstrijden/overzicht-vereniging.dtl'


class VerenigingWedstrijdenView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de wedstrijden van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        ver = self.functie_nu.nhb_ver

        wedstrijden = (Wedstrijd
                       .objects
                       .filter(organiserende_vereniging=ver)
                       .order_by('datum_begin',
                                 'pk'))

        for wed in wedstrijden:
            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wed.organisatie]
            wed.disc_str = ORGANISATIES2SHORT_STR[wed.organisatie] + ' / '
            wed.disc_str += disc2str[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.url_wijzig = reverse('Wedstrijden:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_sessies = reverse('Wedstrijden:wijzig-sessies', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_aanmeldingen = reverse('Wedstrijden:aanmeldingen', kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        # vereniging kan alleen een wedstrijd beginnen als er een locatie is
        if ver.wedstrijdlocatie_set.exclude(zichtbaar=False).count() > 0:
            context['url_nieuwe_wedstrijd'] = reverse('Wedstrijden:nieuwe-wedstrijd-kies-type')
        else:
            context['geen_locatie'] = True

        context['huidige_rol'] = rol_get_beschrijving(request)

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Wedstrijdkalender'),
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)


class NieuweWedstrijdKiesType(UserPassesTestMixin, View):

    """ Via deze view geeft informatie over de verschillende typen wedstrijden """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_KIES_TYPE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['url_nieuwe_wedstrijd'] = reverse('Wedstrijden:nieuwe-wedstrijd-kies-type')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (None, 'Nieuwe wedstrijd')
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen
            met deze POST wordt een nieuwe wedstrijd aangemaakt
        """

        account = request.user

        ver = self.functie_nu.nhb_ver
        locaties = ver.wedstrijdlocatie_set.exclude(zichtbaar=False)
        aantal = locaties.count()
        if aantal > 0:
            # vereniging heeft een wedstrijdlocatie

            keuze = request.POST.get('keuze', '')
            if keuze in ('wa', 'ifaa', 'nhb'):
                now = timezone.now()
                begin = date(now.year, now.month, now.day)      # inschrijven kan alleen indien in toekomst

                keuze2organisatie = {
                    'wa': ORGANISATIE_WA,
                    'nhb': ORGANISATIE_NHB,
                    'ifaa': ORGANISATIE_IFAA,
                }

                wed = Wedstrijd(
                            datum_begin=begin,
                            datum_einde=begin,
                            organiserende_vereniging=self.functie_nu.nhb_ver,
                            organisatie=keuze2organisatie[keuze],
                            voorwaarden_a_status_when=now,
                            locatie=locaties[0],
                            contact_naam=account.volledige_naam(),
                            contact_email=self.functie_nu.bevestigde_email,
                            contact_website=ver.website,
                            contact_telefoon=ver.telefoonnummer)

                if wed.organisatie == ORGANISATIE_IFAA:
                    wed.discipline = WEDSTRIJD_DISCIPLINE_3D

                wed.save()

                bogen = get_organisatie_boogtypen(wed.organisatie)
                wed.boogtypen.set(bogen)

                klassen = get_organisatie_klassen(wed.organisatie)

                if wed.organisatie == ORGANISATIE_NHB:
                    # voorkom zowel gender-neutrale als man/vrouw klassen
                    klassen = klassen.exclude(leeftijdsklasse__wedstrijd_geslacht=GESLACHT_ALLE)

                wed.wedstrijdklassen.set(klassen)

        url = reverse('Wedstrijden:vereniging')
        return HttpResponseRedirect(url)


# end of file