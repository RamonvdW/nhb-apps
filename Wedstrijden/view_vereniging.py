# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import (GESLACHT_ALLE,
                                   ORGANISATIE_WA, ORGANISATIE_IFAA, ORGANISATIE_KHSN, ORGANISATIES2SHORT_STR)
from BasisTypen.operations import get_organisatie_boogtypen, get_organisatie_klassen
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Wedstrijden.definities import (WEDSTRIJD_DISCIPLINE_3D, ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS,
                                    WEDSTRIJD_STATUS_TO_STR)
from Wedstrijden.models import Wedstrijd
import datetime


TEMPLATE_WEDSTRIJDEN_KIES_TYPE = 'wedstrijden/nieuwe-wedstrijd-kies-type.dtl'
TEMPLATE_WEDSTRIJDEN_OVERZICHT_VERENIGING = 'wedstrijden/overzicht-vereniging.dtl'


class VerenigingWedstrijdenView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de wedstrijden van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'
    toon_dagen = 31
    toon_meer = 'Wedstrijden:vereniging-zes-maanden'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        context['ver'] = ver = self.functie_nu.vereniging

        context['huidige_rol'] = rol_get_beschrijving(request)

        if self.toon_meer:
            context['url_toon_meer'] = reverse(self.toon_meer)

        datum = timezone.now().date()
        datum -= datetime.timedelta(days=self.toon_dagen)

        wedstrijden = (Wedstrijd
                       .objects
                       .filter(organiserende_vereniging=ver,
                               datum_begin__gt=datum)
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
            if wed.eis_kwalificatie_scores:
                wed.url_check_kwalificatie_scores = reverse('Wedstrijden:check-kwalificatie-scores',
                                                            kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        # vereniging kan alleen een wedstrijd beginnen als er een locatie is
        if ver.wedstrijdlocatie_set.exclude(zichtbaar=False).count() > 0:
            context['url_nieuwe_wedstrijd'] = reverse('Wedstrijden:nieuwe-wedstrijd-kies-type')
        else:
            context['geen_locatie'] = True

        context['url_mollie'] = reverse('Betaal:vereniging-instellingen')
        context['url_overboeking_ontvangen'] = reverse('Bestelling:overboeking-ontvangen')

        context['url_voorwaarden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Wedstrijdkalender'),
        )

        return render(request, self.template_name, context)


class VerenigingZesMaandenWedstrijdenView(VerenigingWedstrijdenView):
    toon_dagen = 182            # vanaf 6 maanden geleden (182=365/2)
    toon_meer = 'Wedstrijden:vereniging-een-jaar'


class VerenigingEenJaarWedstrijdenView(VerenigingWedstrijdenView):
    toon_dagen = 365            # vanaf 1 jaar terug
    toon_meer = 'Wedstrijden:vereniging-twee-jaar'


class VerenigingTweeJaarWedstrijdenView(VerenigingWedstrijdenView):
    toon_dagen = 2 * 365        # vanaf 2 jaar terug
    toon_meer = None


class NieuweWedstrijdKiesType(UserPassesTestMixin, View):

    """ Via deze view geeft informatie over de verschillende typen wedstrijden """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_KIES_TYPE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['url_nieuwe_wedstrijd'] = reverse('Wedstrijden:nieuwe-wedstrijd-kies-type')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (None, 'Nieuwe wedstrijd')
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen
            met deze POST wordt een nieuwe wedstrijd aangemaakt
        """

        url = reverse('Wedstrijden:vereniging')

        account = get_account(request)
        ver = self.functie_nu.vereniging
        locaties = ver.wedstrijdlocatie_set.exclude(zichtbaar=False)
        aantal = locaties.count()
        if aantal > 0:
            # vereniging heeft een locatie

            keuze = request.POST.get('keuze', '')
            if keuze in ('wa', 'ifaa', 'khsn'):
                now = timezone.now()

                # zet de wedstrijd minstens 2 maanden in de toekomst
                day = 1
                month = now.month + 2
                year = now.year
                if now.day > 1:
                    month += 1
                if month > 12:
                    month -= 12
                    year += 1
                begin = datetime.date(year, month, day)

                keuze2organisatie = {
                    'wa': ORGANISATIE_WA,
                    'khsn': ORGANISATIE_KHSN,
                    'ifaa': ORGANISATIE_IFAA,
                }

                wed = Wedstrijd(
                            datum_begin=begin,
                            datum_einde=begin,
                            organiserende_vereniging=self.functie_nu.vereniging,
                            organisatie=keuze2organisatie[keuze],
                            locatie=locaties[0],
                            contact_naam=account.volledige_naam(),
                            contact_email=self.functie_nu.bevestigde_email,
                            contact_website=ver.website,
                            contact_telefoon=ver.telefoonnummer)

                if wed.organisatie == ORGANISATIE_IFAA:
                    wed.discipline = WEDSTRIJD_DISCIPLINE_3D

                wed.save()
                url = reverse('Wedstrijden:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})

                bogen = get_organisatie_boogtypen(wed.organisatie)
                wed.boogtypen.set(bogen)

                klassen = get_organisatie_klassen(wed.organisatie)

                if wed.organisatie == ORGANISATIE_KHSN:
                    # voorkom zowel gender-neutrale als man/vrouw klassen
                    klassen = klassen.exclude(leeftijdsklasse__wedstrijd_geslacht=GESLACHT_ALLE)

                wed.wedstrijdklassen.set(klassen)

        return HttpResponseRedirect(url)


# end of file
