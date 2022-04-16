# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import (GESLACHT_ALLE,
                               ORGANISATIE_WA, ORGANISATIE_IFAA, ORGANISATIE_NHB, ORGANISATIES2SHORT_STR)
from BasisTypen.operations import get_organisatie_boogtypen, get_organisatie_klassen
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Bestel.models import BESTEL_KORTINGSCODE_MINLENGTH
from Sporter.models import Sporter
from Plein.menu import menu_dynamics
from .models import (KalenderWedstrijd, KalenderWedstrijdKortingscode,
                     WEDSTRIJD_DISCIPLINE_3D, ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS, WEDSTRIJD_STATUS_TO_STR)
from datetime import date

TEMPLATE_KALENDER_KIES_TYPE = 'kalender/nieuwe-wedstrijd-kies-type.dtl'
TEMPLATE_KALENDER_OVERZICHT_VERENIGING = 'kalender/overzicht-vereniging.dtl'
TEMPLATE_KALENDER_OVERZICHT_VERENIGING_CODES = 'kalender/overzicht-verenging-codes.dtl'
TEMPLATE_KALENDER_WIJZIG_KORTING = 'kalender/wijzig-kortingscode.dtl'


class VerenigingKalenderWedstrijdenView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de wedstrijden van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_OVERZICHT_VERENIGING
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

        wedstrijden = (KalenderWedstrijd
                       .objects
                       .filter(organiserende_vereniging=ver)
                       .order_by('-datum_begin',
                                 'pk'))

        for wed in wedstrijden:
            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wed.organisatie]
            wed.disc_str = ORGANISATIES2SHORT_STR[wed.organisatie] + ' / '
            wed.disc_str += disc2str[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.url_wijzig = reverse('Kalender:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_sessies = reverse('Kalender:wijzig-sessies', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_aanmeldingen = reverse('Kalender:aanmeldingen', kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        # vereniging kan alleen een wedstrijd beginnen als er een locatie is
        if ver.wedstrijdlocatie_set.exclude(zichtbaar=False).count() > 0:
            context['url_nieuwe_wedstrijd'] = reverse('Kalender:nieuwe-wedstrijd-kies-type')
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
    template_name = TEMPLATE_KALENDER_KIES_TYPE
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

        context['url_nieuwe_wedstrijd'] = reverse('Kalender:nieuwe-wedstrijd-kies-type')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Kalender:vereniging'), 'Wedstrijdkalender'),
            (None, 'Nieuwe wedstrijd')
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        ver = self.functie_nu.nhb_ver
        locaties = ver.wedstrijdlocatie_set.exclude(zichtbaar=False)
        aantal = locaties.count()
        if aantal > 0:
            # vereniging heeft een wedstrijdlocatie

            keuze = request.POST.get('keuze', '')
            if keuze in ('wa', 'ifaa', 'nhb'):
                now = timezone.now()
                begin = date(now.year, now.month, now.day)

                keuze2organisatie = {
                    'wa': ORGANISATIE_WA,
                    'nhb': ORGANISATIE_NHB,
                    'ifaa': ORGANISATIE_IFAA,
                }

                wed = KalenderWedstrijd(
                            datum_begin=begin,
                            datum_einde=begin,
                            organiserende_vereniging=self.functie_nu.nhb_ver,
                            organisatie=keuze2organisatie[keuze],
                            voorwaarden_a_status_when=now,
                            locatie=locaties[0])

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

        url = reverse('Kalender:vereniging')
        return HttpResponseRedirect(url)


class VerenigingKortingcodesView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL de kortingscodes van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_OVERZICHT_VERENIGING_CODES
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

        context['huidige_rol'] = rol_get_beschrijving(request)

        codes = (KalenderWedstrijdKortingscode
                 .objects
                 .filter(uitgegeven_door=ver)
                 .select_related('voor_sporter')
                 .order_by('geldig_tot_en_met'))

        for korting in codes:
            korting.voor_wie_str = '-'

            if korting.voor_vereniging:
                korting.voor_wie_str = 'Leden van onze vereniging'

            if korting.voor_sporter:
                korting.voor_wie_str = korting.voor_sporter.volledige_naam()

            korting.voor_wedstrijden_str = '\n'.join(korting.voor_wedstrijden.order_by('datum_begin', 'pk').values_list('titel', flat=True))

            korting.url_wijzig = reverse('Kalender:vereniging-wijzig-code', kwargs={'korting_pk': korting.pk})
        # for

        context['codes'] = codes

        context['url_nieuwe_code'] = reverse('Kalender:vereniging-codes')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Kalender:vereniging'), 'Wedstrijdkalender'),
            (None, 'Kortingscodes'),
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL een nieuwe kortingscode aan wil maken """

        ver = self.functie_nu.nhb_ver
        now = timezone.now()

        korting = KalenderWedstrijdKortingscode(
                        geldig_tot_en_met=now.date(),
                        uitgegeven_door=ver)
        korting.save()

        url = reverse('Kalender:vereniging-wijzig-code', kwargs={'korting_pk': korting.pk})

        return HttpResponseRedirect(url)


class VerenigingWijzigKortingcodesView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL een kortingscode van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_WIJZIG_KORTING
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
        context['ver'] = ver

        try:
            korting_pk = kwargs['korting_pk'][:6]       # afkappen voor de veiligheid
            korting_pk = int(korting_pk)
            korting = (KalenderWedstrijdKortingscode
                       .objects
                       .select_related('voor_vereniging',
                                       'voor_sporter')
                       .get(pk=korting_pk,
                            uitgegeven_door=ver))
        except (ValueError, TypeError, KalenderWedstrijdKortingscode.DoesNotExist):
            raise Http404('Niet gevonden')

        context['korting'] = korting

        if korting.voor_vereniging:
            context['check_ver'] = True

        if korting.voor_sporter:
            context['voor_sporter_str'] = str(korting.voor_sporter.lid_nr_en_volledige_naam())

        gekozen_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))
        context['wedstrijden'] = wedstrijden = list()
        for wedstrijd in (KalenderWedstrijd
                          .objects
                          .filter(organiserende_vereniging=ver)
                          .order_by('datum_begin', 'pk')):

            wedstrijd.sel = 'wedstrijd_%s' % wedstrijd.pk
            if wedstrijd.pk in gekozen_pks:
                wedstrijd.is_gekozen = True

            wedstrijden.append(wedstrijd)
        # for

        context['min_code_len'] = BESTEL_KORTINGSCODE_MINLENGTH

        # nodig voor de datum picker
        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, korting.geldig_tot_en_met.year)   # zorg dat de huidige datum weer gekozen kan worden
        context['min_date'] = min(now.date(), korting.geldig_tot_en_met)
        context['max_date'] = date(now.year + 1, 12, 31)

        context['url_opslaan'] = reverse('Kalender:vereniging-wijzig-code', kwargs={'korting_pk': korting.pk})

        # verwijderen kan alleen als deze nog niet gebruikt is
        if korting.kalenderinschrijving_set.count() == 0:
            context['url_verwijder'] = context['url_opslaan']

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Kalender:vereniging'), 'Wedstrijdkalender'),
            (reverse('Kalender:vereniging-codes'), 'Kortingscodes'),
            (None, 'Wijzig'),
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'opslaan' gebruikt wordt door de HWL """

        ver = self.functie_nu.nhb_ver

        try:
            korting_pk = kwargs['korting_pk'][:6]       # afkappen voor de veiligheid
            korting_pk = int(korting_pk)
            korting = KalenderWedstrijdKortingscode.objects.get(pk=korting_pk,
                                                                uitgegeven_door=ver)
        except (ValueError, TypeError, KalenderWedstrijdKortingscode.DoesNotExist):
            raise Http404('Niet gevonden')

        if request.POST.get('verwijder', ''):
            # verwijderen deze kortingscode
            if korting.kalenderinschrijving_set.count() > 0:
                raise Http404('Korting is in gebruik')
            korting.delete()
        else:
            code = request.POST.get('code', '')
            # filter slechte tekens + forceer hoofdletters
            code = "".join([char.upper() for char in code if char.isalnum()])
            if len(code) < BESTEL_KORTINGSCODE_MINLENGTH:
                raise Http404('Te korte code')

            korting.code = code[:20]        # maximum lengte in database

            try:
                percentage = request.POST.get('percentage', '100')[:3]      # afkappen voor de veiligheid
                percentage = int(percentage)
            except (ValueError, KeyError, TypeError):
                raise Http404('Verkeerde parameter (percentage)')

            if not (0 <= percentage <= 100):
                raise Http404('Verkeerd percentage')
            korting.percentage = percentage

            voor_onze_ver = request.POST.get('voor_onze_ver', '')
            if voor_onze_ver:
                korting.voor_vereniging = ver
                korting.voor_sporter = None
            else:
                korting.voor_vereniging = None

                voor_lid_nr = request.POST.get('voor_lid_nr', '')[:6]           # afkappen voor de veiligheid
                if voor_lid_nr:
                    if voor_lid_nr == '000000':
                        korting.voor_sporter = None
                    else:
                        try:
                            voor_lid_nr = int(voor_lid_nr)
                            sporter = Sporter.objects.get(lid_nr=voor_lid_nr)
                        except (ValueError, TypeError, Sporter.DoesNotExist):
                            raise Http404('Sporter niet gevonden')

                        korting.voor_sporter = sporter

            korting.save()

            keep_pks = list()
            for pk in (KalenderWedstrijd
                       .objects
                       .filter(organiserende_vereniging=ver)
                       .values_list('pk', flat=True)):

                sel = 'wedstrijd_%s' % pk
                if request.POST.get(sel, ''):
                    keep_pks.append(pk)
            # for
            korting.voor_wedstrijden.set(keep_pks)

        url = reverse('Kalender:vereniging-codes')
        return HttpResponseRedirect(url)


# end of file
