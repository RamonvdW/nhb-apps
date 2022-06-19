# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige_functie, rol_get_beschrijving
from Bestel.models import BESTEL_KORTINGSCODE_MINLENGTH
from Sporter.models import Sporter
from Plein.menu import menu_dynamics
from Wedstrijden.models import (Wedstrijd, WedstrijdKortingscode,
                                WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING, WEDSTRIJD_KORTING_COMBI)
import datetime

TEMPLATE_KALENDER_KORTINGSCODES_OVERZICHT = 'wedstrijden/overzicht-kortingscodes-vereniging.dtl'
TEMPLATE_KALENDER_NIEUWE_KORTINGSCODE = 'wedstrijden/nieuwe-kortingscode-vereniging.dtl'
TEMPLATE_KALENDER_WIJZIG_KORTINGSCODE_SPORTER = 'wedstrijden/wijzig-kortingscode-sporter.dtl'
TEMPLATE_KALENDER_WIJZIG_KORTINGSCODE_VERENIGING = 'wedstrijden/wijzig-kortingscode-vereniging.dtl'
TEMPLATE_KALENDER_WIJZIG_KORTINGSCODE_COMBI = 'wedstrijden/wijzig-kortingscode-combi.dtl'


class VerenigingKortingcodesView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL de kortingscodes van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_KORTINGSCODES_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        ver = self.functie_nu.nhb_ver

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        codes = (WedstrijdKortingscode
                 .objects
                 .filter(uitgegeven_door=ver)
                 .select_related('voor_sporter')
                 .order_by('geldig_tot_en_met'))

        for korting in codes:
            korting.voor_wie_str = '-'
            korting.voor_wedstrijden_str = '\n'.join(korting.voor_wedstrijden.order_by('datum_begin', 'pk').values_list('titel', flat=True))

            if korting.soort == WEDSTRIJD_KORTING_SPORTER:
                korting.icon_name = 'account_circle'
                if korting.voor_sporter:
                    korting.voor_wie_str = korting.voor_sporter.volledige_naam()

            elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
                korting.icon_name = 'home'
                korting.voor_wie_str = 'Leden van vereniging %s' % ver.ver_nr
                korting.voor_vereniging = ver

            elif korting.soort == WEDSTRIJD_KORTING_COMBI:       # pragma: no branch
                korting.icon_name = 'join_full'
                if korting.combi_basis_wedstrijd:
                    korting.voor_wedstrijden_str = korting.combi_basis_wedstrijd.titel

            else:       # pragma: no cover
                korting.voor_wie_str = "?"

            korting.url_wijzig = reverse('Wedstrijden:vereniging-wijzig-code', kwargs={'korting_pk': korting.pk})
        # for

        context['codes'] = codes

        context['url_nieuwe_code'] = reverse('Wedstrijden:vereniging-codes-nieuw-kies')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (None, 'Kortingscodes'),
        )

        menu_dynamics(self.request, context)
        return context


class NieuweKortingcodesView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL een nieuwe kortingscode van de vereniging aanmaken """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_NIEUWE_KORTINGSCODE
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

        context['url_nieuwe_korting'] = reverse('Wedstrijden:vereniging-codes-nieuw-kies')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (reverse('Wedstrijden:vereniging-codes'), 'Kortingscodes'),
            (None, 'Nieuwe aanmaken')
        )

        menu_dynamics(self.request, context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL een nieuwe kortingscode aan wil maken """

        ver = self.functie_nu.nhb_ver
        toekomst = timezone.now().date() + datetime.timedelta(days=30)

        korting = WedstrijdKortingscode(
                        geldig_tot_en_met=toekomst,
                        uitgegeven_door=ver)

        keuze = request.POST.get('keuze', '')

        if keuze == 'sporter':
            korting.soort = WEDSTRIJD_KORTING_SPORTER
        elif keuze == 'vereniging':
            korting.soort = WEDSTRIJD_KORTING_VERENIGING
            korting.voor_vereniging = ver
        elif keuze == 'combi':
            korting.soort = WEDSTRIJD_KORTING_COMBI
        else:
            raise Http404('Niet ondersteund')

        korting.save()

        url = reverse('Wedstrijden:vereniging-wijzig-code', kwargs={'korting_pk': korting.pk})

        return HttpResponseRedirect(url)


class VerenigingWijzigKortingcodesView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL een kortingscode van de vereniging beheren """

    # class variables shared by all instances
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
            korting = (WedstrijdKortingscode
                       .objects
                       .select_related('voor_vereniging',
                                       'voor_sporter')
                       .get(pk=korting_pk,
                            uitgegeven_door=ver))
        except (ValueError, TypeError, WedstrijdKortingscode.DoesNotExist):
            raise Http404('Niet gevonden')

        context['korting'] = korting

        if korting.soort == WEDSTRIJD_KORTING_SPORTER:
            template_name = TEMPLATE_KALENDER_WIJZIG_KORTINGSCODE_SPORTER
        elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
            template_name = TEMPLATE_KALENDER_WIJZIG_KORTINGSCODE_VERENIGING
        elif korting.soort == WEDSTRIJD_KORTING_COMBI:                           # pragma: no branch
            template_name = TEMPLATE_KALENDER_WIJZIG_KORTINGSCODE_COMBI
        else:                                                                   # pragma: no cover
            raise Http404('Niet ondersteund')

        if korting.voor_vereniging:
            context['check_ver'] = True

        if korting.voor_sporter:
            context['voor_sporter_str'] = str(korting.voor_sporter.lid_nr_en_volledige_naam())

        context['wedstrijden'] = wedstrijden = list()
        gekozen_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))

        if korting.combi_basis_wedstrijd:
            wedstrijd = korting.combi_basis_wedstrijd

            wedstrijd.sel = 'wedstrijd_%s' % wedstrijd.pk
            wedstrijd.is_gekozen = True

            wedstrijden.append(wedstrijd)
        else:
            for wedstrijd in (Wedstrijd
                              .objects
                              .filter(organiserende_vereniging=ver)
                              .order_by('datum_begin', 'pk')):

                wedstrijd.sel = 'wedstrijd_%s' % wedstrijd.pk
                if wedstrijd.pk in gekozen_pks:
                    wedstrijd.is_gekozen = True

                wedstrijden.append(wedstrijd)
            # for

        context['combi_wedstrijden'] = combi_wedstrijden = list()
        for wedstrijd in (Wedstrijd
                          .objects
                          .filter(organiserende_vereniging=ver)
                          .order_by('datum_begin', 'pk')):

            wedstrijd.sel = 'combi_%s' % wedstrijd.pk
            if wedstrijd.pk in gekozen_pks:
                wedstrijd.is_gekozen = True

            combi_wedstrijden.append(wedstrijd)
        # for

        context['min_code_len'] = BESTEL_KORTINGSCODE_MINLENGTH

        # nodig voor de datum picker
        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, korting.geldig_tot_en_met.year)   # zorg dat de huidige datum weer gekozen kan worden
        context['min_date'] = min(now.date(), korting.geldig_tot_en_met)
        context['max_date'] = datetime.date(now.year + 1, 12, 31)

        context['url_opslaan'] = reverse('Wedstrijden:vereniging-wijzig-code', kwargs={'korting_pk': korting.pk})

        # verwijderen kan alleen als deze nog niet gebruikt is
        if korting.wedstrijdinschrijving_set.count() == 0:
            context['url_verwijder'] = context['url_opslaan']

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (reverse('Wedstrijden:vereniging-codes'), 'Kortingscodes'),
            (None, 'Wijzig'),
        )

        menu_dynamics(self.request, context)
        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'opslaan' gebruikt wordt door de HWL """

        ver = self.functie_nu.nhb_ver

        try:
            korting_pk = kwargs['korting_pk'][:6]       # afkappen voor de veiligheid
            korting_pk = int(korting_pk)
            korting = WedstrijdKortingscode.objects.get(pk=korting_pk,
                                                        uitgegeven_door=ver)
        except (ValueError, TypeError, WedstrijdKortingscode.DoesNotExist):
            raise Http404('Niet gevonden')

        if request.POST.get('verwijder', ''):
            # verwijderen deze kortingscode
            if korting.wedstrijdinschrijving_set.count() > 0:
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

            datum_ymd = request.POST.get('geldig_tm', '')[:10]  # afkappen voor de veiligheid
            if datum_ymd:
                try:
                    datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
                except ValueError:
                    raise Http404('Geen valide datum')

                datum = datetime.date(datum.year, datum.month, datum.day)
                now = timezone.now()
                min_date = datetime.date(now.year, now.month, now.day)
                max_date = datetime.date(now.year + 1, 12, 31)
                if min_date <= datum <= max_date:
                    korting.geldig_tot_en_met = datum
                else:
                    raise Http404('Geen valide datum')

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

            eerste_wedstrijd = None
            combi_pks = list()
            keep_pks = list()
            for wedstrijd in (Wedstrijd
                              .objects
                              .filter(organiserende_vereniging=ver)):

                pk = wedstrijd.pk

                sel = 'wedstrijd_%s' % pk
                if request.POST.get(sel, ''):
                    if len(keep_pks) == 0:
                        eerste_wedstrijd = wedstrijd
                    keep_pks.append(pk)

                sel = 'combi_%s' % pk
                if request.POST.get(sel, ''):
                    combi_pks.append(pk)
            # for

            if len(combi_pks) > 0 and eerste_wedstrijd is not None:
                # dit wordt een combinatie-korting
                korting.combi_basis_wedstrijd = eerste_wedstrijd
                korting.save()
                korting.voor_wedstrijden.set(combi_pks)
            else:
                # dit is een gewone korting
                korting.combi_basis_wedstrijd = None
                korting.save()
                korting.voor_wedstrijden.set(keep_pks)

        url = reverse('Wedstrijden:vereniging-codes')
        return HttpResponseRedirect(url)


# end of file
