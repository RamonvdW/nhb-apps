# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from Instaptoets.models import Instaptoets
from Opleiding.definities import OPLEIDING_STATUS_TO_STR
from Opleiding.models import Opleiding, OpleidingInschrijving, OpleidingMoment
from decimal import Decimal
from types import SimpleNamespace
import datetime

TEMPLATE_OPLEIDING_OVERZICHT_MANAGER = 'opleiding/overzicht-manager.dtl'
TEMPLATE_OPLEIDING_NIET_INGESCHREVEN = 'opleiding/niet-ingeschreven.dtl'
TEMPLATE_OPLEIDING_WIJZIG_OPLEIDING = 'opleiding/wijzig-opleiding.dtl'
TEMPLATE_OPLEIDING_WIJZIG_MOMENT = 'opleiding/wijzig-moment.dtl'


class ManagerOpleidingenView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen de opleidingen beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_OVERZICHT_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['huidige_rol'] = rol_get_beschrijving(request)

        opleidingen = (Opleiding
                       .objects
                       .order_by('periode_begin',
                                 'periode_einde',
                                 'pk'))

        for opleiding in opleidingen:
            opleiding.status_str = OPLEIDING_STATUS_TO_STR[opleiding.status]
            opleiding.url_wijzig = reverse('Opleiding:wijzig-opleiding',
                                           kwargs={'opleiding_pk': opleiding.pk})
            opleiding.url_aanmeldingen = reverse('Opleiding:aanmeldingen',
                                                 kwargs={'opleiding_pk': opleiding.pk})
        # for

        context['opleidingen'] = opleidingen

        context['url_stats_instaptoets'] = reverse('Instaptoets:stats')
        context['url_gezakt'] = reverse('Instaptoets:gezakt')
        context['url_niet_ingeschreven'] = reverse('Opleiding:niet-ingeschreven')
        context['url_aanpassingen'] = reverse('Opleiding:aanpassingen')
        context['url_toevoegen'] = reverse('Opleiding:toevoegen')

        context['url_voorwaarden'] = settings.VERKOOPVOORWAARDEN_OPLEIDINGEN_URL

        context['kruimels'] = (
            (None, 'Opleidingen'),
        )

        return render(request, self.template_name, context)


class OpleidingToevoegenView(UserPassesTestMixin, View):

    """ View deze view kan de manager een nieuwe opleiding aanmaken """

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_MO

    @staticmethod
    def post(request, *args, **kwargs):
        now = timezone.now()
        opleiding = Opleiding(
                        laten_zien=False,
                        periode_begin=now,
                        periode_einde=now)
        opleiding.save()

        url = reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk})
        return HttpResponseRedirect(url)


class NietIngeschrevenView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen zien wie wel de instaptoets gehaald hebben,
        maar zich niet ingeschreven hebben voor de basiscursus.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_NIET_INGESCHREVEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['huidige_rol'] = rol_get_beschrijving(request)

        # TODO: filteren op status, want niet elke OpleidingInschrijving is ook definitief
        ingeschreven_lid_nrs = (OpleidingInschrijving
                                .objects
                                .filter(opleiding__is_basiscursus=True)
                                .distinct('sporter')
                                .values_list('sporter__lid_nr', flat=True))

        context['niet_ingeschreven'] = lijst = list()
        for toets in (Instaptoets
                      .objects
                      .filter(is_afgerond=True,
                              geslaagd=True)
                      .select_related('sporter')
                      .order_by('-afgerond')):      # nieuwste eerst

            if toets.sporter.lid_nr not in ingeschreven_lid_nrs:
                toets.basiscursus_str = 'Niet ingeschreven'
                toets.lid_nr_en_naam = toets.sporter.lid_nr_en_volledige_naam()

                lijst.append(toets)
        # for

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Niet ingeschreven'),
        )

        return render(request, self.template_name, context)


class WijzigOpleidingView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen de definitie van een opleiding aanpassen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_WIJZIG_OPLEIDING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def _maak_opt_dagen(self, opleiding: Opleiding):
        opts = list()
        for aantal in range(1, 7+1):
            opt = SimpleNamespace(
                        sel=str(aantal),
                        keuze_str="%s dagen" % aantal,
                        selected=(aantal == opleiding.aantal_dagen))
            if aantal == 1:
                opt.keuze_str = "1 dag"
            opts.append(opt)
        # for
        return opts

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        try:
            opleiding_pk = int(kwargs['opleiding_pk'])
            opleiding = Opleiding.objects.prefetch_related('momenten').get(pk=opleiding_pk)
        except (TypeError, ValueError, Opleiding.DoesNotExist):
            raise Http404('Niet gevonden')

        context['opleiding'] = opleiding

        context['url_opslaan'] = reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk})

        # zorg dat de huidige datum weer gekozen kan worden
        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, opleiding.periode_begin.year)
        context['min_date'] = datetime.date(now.year, 1, 1)
        context['max_date'] = datetime.date(now.year + 2, 12, 31)

        context['opt_dagen'] = self._maak_opt_dagen(opleiding)

        context['momenten'] = momenten = list(opleiding.momenten.all())
        for moment in momenten:
            moment.url_edit = reverse('Opleiding:wijzig-moment', kwargs={'opleiding_pk': opleiding.pk,
                                                                         'moment_pk': moment.pk})
        # for

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Wijzig opleiding'),
        )

        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de manager de Opslaan knop indrukt """

        try:
            opleiding_pk = int(kwargs['opleiding_pk'])
            opleiding = Opleiding.objects.get(pk=opleiding_pk)
        except (TypeError, ValueError, Opleiding.DoesNotExist):
            raise Http404('Niet gevonden')

        # moment toevoegen
        param = request.POST.get('add-moment', '')
        if param == 'y':
            moment = OpleidingMoment(datum=opleiding.periode_begin)
            moment.save()
            opleiding.momenten.add(moment)

            url = reverse('Opleiding:wijzig-moment', kwargs={'opleiding_pk': opleiding.pk,
                                                             'moment_pk': moment.pk})
            return HttpResponseRedirect(url)

        # titel
        param = request.POST.get('titel', '?')
        opleiding.titel = param[:75]

        now = timezone.now()
        min_date = datetime.date(now.year, 1, 1)
        max_date = datetime.date(now.year + 2, 12, 31)

        # periode begin
        datum_ymd = request.POST.get('periode_begin', '')[:10]  # afkappen voor de veiligheid
        if datum_ymd:
            try:
                datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
            except ValueError:
                raise Http404('Geen valide begin datum')

            datum = datetime.date(datum.year, datum.month, datum.day)
            if min_date <= datum <= max_date:
                opleiding.periode_begin = datum

        # periode einde
        datum_ymd = request.POST.get('periode_einde', '')[:10]  # afkappen voor de veiligheid
        if datum_ymd:
            try:
                datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
            except ValueError:
                raise Http404('Geen valide eind datum')

            datum = datetime.date(datum.year, datum.month, datum.day)
            if opleiding.periode_begin <= datum <= max_date:
                opleiding.periode_einde = datum

        # aantal dagen
        param = request.POST.get('dagen', '1')[:2]  # afkappen voor de veiligheid
        try:
            param = int(param)
        except (ValueError, TypeError):
            raise Http404('Geen valide aantal dagen')
        opleiding.aantal_dagen = param

        # aantal uren
        param = request.POST.get('uren', '1')[:2]  # afkappen voor de veiligheid
        try:
            param = int(param)
        except (ValueError, TypeError):
            raise Http404('Geen valide aantal uren')
        opleiding.aantal_uren = param

        # beschrijving (text)
        param = request.POST.get('beschrijving', '')[:1500]     # afkappen voor de veiligheid
        opleiding.beschrijving = param

        # ingangseisen
        param = request.POST.get('eis_instaptoets', '')[:3]     # afkappen voor de veiligheid
        opleiding.eis_instaptoets = (param != '')

        param = request.POST.get('ingangseisen', '')[:1500]     # afkappen voor de veiligheid
        opleiding.ingangseisen = param

        param = request.POST.get('leeftijd_min', '16')[:2]
        try:
            param = int(param)
        except (ValueError, TypeError):
            param = 16
        opleiding.leeftijd_min = param

        param = request.POST.get('leeftijd_max', '0')[:2]
        try:
            param = int(param)
        except (ValueError, TypeError):
            param = 0
        opleiding.leeftijd_max = param

        # kosten
        param = request.POST.get('kosten', '0')
        param = param.replace(',', '.')     # dutch to standard decimal point
        try:
            param = float(param)
        except ValueError:
            param = 1.0
        param = min(param, 9999.99)     # avoid too large numbers
        param = max(param, 0.0)         # avoid negative numbers
        opleiding.kosten_euro = Decimal(param)

        opleiding.save()

        # redirect naar de GET pagina, anders geeft F5 in de browser een nieuwe POST
        url = reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk})
        return HttpResponseRedirect(url)


class WijzigMomentView(UserPassesTestMixin, View):

    """ Via deze view kan de Manager Opleidingen de definitie van een opleiding-moment aanpassen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OPLEIDING_WIJZIG_MOMENT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_MO

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        try:
            opleiding_pk = int(kwargs['opleiding_pk'])
            opleiding = Opleiding.objects.get(pk=opleiding_pk)
        except (TypeError, ValueError, Opleiding.DoesNotExist):
            raise Http404('Opleiding niet gevonden')

        try:
            moment_pk = int(kwargs['moment_pk'])
            moment = OpleidingMoment.objects.get(pk=moment_pk)
        except (TypeError, ValueError, OpleidingMoment.DoesNotExist):
            raise Http404('Moment niet gevonden')

        context['moment'] = moment

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk}), 'Wijzig opleiding'),
            (None, 'Wijzig moment'),
        )

        return render(request, self.template_name, context)


# end of file
