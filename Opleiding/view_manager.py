# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving, rol_get_huidige
from Instaptoets.models import Instaptoets
from Locatie.models import EvenementLocatie
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

    @staticmethod
    def _get_opleiding_or_404(kwargs):
        try:
            opleiding_pk = int(kwargs['opleiding_pk'])
            opleiding = Opleiding.objects.get(pk=opleiding_pk)
        except (TypeError, ValueError, Opleiding.DoesNotExist):
            raise Http404('Opleiding niet gevonden')

        return opleiding

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['opleiding'] = opleiding = self._get_opleiding_or_404(kwargs)

        context['url_opslaan'] = reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk})

        # zorg dat de huidige datum weer gekozen kan worden
        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, opleiding.periode_begin.year)
        context['min_date'] = datetime.date(now.year, 1, 1)
        context['max_date'] = datetime.date(now.year + 2, 12, 31)

        context['opt_dagen'] = self._maak_opt_dagen(opleiding)

        momenten = list()
        for moment in opleiding.momenten.all():
            moment.url_edit = reverse('Opleiding:wijzig-moment', kwargs={'opleiding_pk': opleiding.pk,
                                                                         'moment_pk': moment.pk})
            moment.sel = 'M_%s' % moment.pk
            moment.is_selected = True

            tup = (moment.datum, moment.pk, moment)
            momenten.append(tup)
        # for

        for moment in OpleidingMoment.objects.annotate(aantal=Count('opleiding')).filter(aantal=0).all():
            moment.url_edit = reverse('Opleiding:wijzig-moment', kwargs={'opleiding_pk': opleiding.pk,
                                                                         'moment_pk': moment.pk})
            moment.sel = 'M_%s' % moment.pk
            moment.is_selected = False
            tup = (moment.datum, moment.pk, moment)
            momenten.append(tup)
        # for

        momenten.sort()
        context['momenten'] = [tup[-1]
                               for tup in momenten]

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (None, 'Wijzig opleiding'),
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de manager de Opslaan knop indrukt """

        opleiding = self._get_opleiding_or_404(kwargs)

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
                pass
            else:
                datum = datetime.date(datum.year, datum.month, datum.day)
                if min_date <= datum <= max_date:
                    opleiding.periode_begin = datum

        # periode einde
        datum_ymd = request.POST.get('periode_einde', '')[:10]  # afkappen voor de veiligheid
        if datum_ymd:
            try:
                datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
            except ValueError:
                pass
            else:
                datum = datetime.date(datum.year, datum.month, datum.day)
                if opleiding.periode_begin <= datum <= max_date:
                    opleiding.periode_einde = datum

        # aantal dagen
        param = request.POST.get('dagen', '1')[:2]  # afkappen voor de veiligheid
        try:
            param = int(param)
            opleiding.aantal_dagen = param
        except (ValueError, TypeError):
            pass

        # aantal uren
        param = request.POST.get('uren', '1')[:2]  # afkappen voor de veiligheid
        try:
            param = int(param)
            opleiding.aantal_uren = param
        except (ValueError, TypeError):
            pass

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

        # momenten
        old_pks = list(opleiding.momenten.values_list('pk', flat=True))
        check_pks = list()
        new_pks = list()
        for key in request.POST.keys():
            if key[:2] == 'M_':
                try:
                    pk = int(key[2:2+7])        # afkappen voor de veiligheid
                except (ValueError, TypeError):
                    pass
                else:
                    if pk in old_pks:
                        new_pks.append(pk)
                    else:
                        # controleer dat deze nog niet in gebruik is
                        check_pks.append(pk)
        # for

        if len(check_pks):
            new_pks.extend(
                    list(
                        OpleidingMoment
                        .objects
                        .filter(pk__in=check_pks)
                        .annotate(aantal=Count('opleiding'))
                        .filter(aantal=0)
                        .values_list('pk', flat=True)
                    ))

        # vervang de lijst de hele lijst van momenten voor deze opleiding
        momenten = OpleidingMoment.objects.filter(pk__in=new_pks)
        opleiding.momenten.set(momenten)

        # redirect naar de GET pagina, anders geeft F5 in de browser een nieuwe POST
        url = reverse('Opleiding:manager')
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

    def _get_min_max_dates(self, opleiding: Opleiding):
        min_date = datetime.date(opleiding.periode_begin.year, opleiding.periode_begin.month, 1)

        if opleiding.periode_einde.month == 12:
            max_date = datetime.date(opleiding.periode_einde.year + 1, 1, 1)
        else:
            max_date = datetime.date(opleiding.periode_einde.year, opleiding.periode_einde.month + 1, 1)
        max_date -= datetime.timedelta(days=1)       # end of previous month

        return min_date, max_date

    @staticmethod
    def _get_opleiding_moment_or_404(kwargs):
        try:
            opleiding_pk = int(kwargs['opleiding_pk'])
            opleiding = Opleiding.objects.get(pk=opleiding_pk)
        except (TypeError, ValueError, Opleiding.DoesNotExist):
            raise Http404('Opleiding niet gevonden')

        try:
            moment_pk = int(kwargs['moment_pk'])
            moment = OpleidingMoment.objects.select_related('locatie').get(pk=moment_pk)
        except (TypeError, ValueError, OpleidingMoment.DoesNotExist):
            raise Http404('Moment niet gevonden')

        return opleiding, moment

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        opleiding, moment = self._get_opleiding_moment_or_404(kwargs)

        context['opleiding'] = opleiding
        context['moment'] = moment
        context['min_date'], context['max_date'] = self._get_min_max_dates(opleiding)

        context['locaties'] = locaties = EvenementLocatie.objects.exclude(zichtbaar=False)
        for locatie in locaties:
            locatie.is_selected = (moment.locatie and moment.locatie.pk == locatie.pk)
        # for

        context['url_opslaan'] = reverse('Opleiding:wijzig-moment', kwargs={'opleiding_pk': opleiding.pk,
                                                                            'moment_pk': moment.pk})

        context['kruimels'] = (
            (reverse('Opleiding:manager'), 'Opleidingen'),
            (reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk}), 'Wijzig opleiding'),
            (None, 'Wijzig moment'),
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de manager de Opslaan knop indrukt """

        opleiding, moment = self._get_opleiding_moment_or_404(kwargs)
        min_date, max_date = self._get_min_max_dates(opleiding)

        # datum
        datum_ymd = request.POST.get('datum', '')[:10]  # afkappen voor de veiligheid
        if datum_ymd:
            try:
                datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
            except ValueError:
                pass
            else:
                datum = datetime.date(datum.year, datum.month, datum.day)
                if min_date <= datum <= max_date:
                    moment.datum = datum

        # aantal dagen
        param = request.POST.get('dagen', '1')
        try:
            param = int(param)
            if 1 <= param <= 7:
                moment.aantal_dagen = param
        except (ValueError, TypeError):
            pass

        # begin tijd
        param = request.POST.get('begin_tijd', '10:00')[:5]
        try:
            hours = int(param[0:0+2])
            mins = int(param[3:3+2])
            if 0 <= hours <= 23 and 0 <= mins <= 59:
                moment.begin_tijd = "%02d:%02d" % (hours, mins)
        except (ValueError, TypeError):
            pass

        # duur in minuten
        param = request.POST.get('minuten', '60')
        try:
            param = int(param)
            if 1 <= param <= 600:
                moment.duur_minuten = param
        except (ValueError, TypeError):
            pass

        # locatie
        param = request.POST.get('locatie', '')[:6]     # afkappen voor de veiligheid
        try:
            moment.locatie = EvenementLocatie.objects.get(pk=int(param))
        except (ValueError, TypeError, EvenementLocatie.DoesNotExist):
            pass

        # naam docent
        param = request.POST.get('naam', '')
        moment.opleider_naam = param[:150]

        # e-mail docent
        param = request.POST.get('email', '')
        moment.opleider_email = param[:254]

        # telefoonnummer docent
        param = request.POST.get('tel', '')
        moment.opleider_telefoon = param[:25]

        moment.save()

        # redirect naar de GET pagina, anders geeft F5 in de browser een nieuwe POST
        url = reverse('Opleiding:wijzig-opleiding', kwargs={'opleiding_pk': opleiding.pk})
        return HttpResponseRedirect(url)


# end of file
