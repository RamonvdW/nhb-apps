# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import ORGANISATIE_IFAA
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Wedstrijden.definities import WEDSTRIJD_DUUR_MAX_DAGEN, WEDSTRIJD_DUUR_MAX_UREN, WEDSTRIJD_STATUS_GEANNULEERD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie
from types import SimpleNamespace
import datetime

TEMPLATE_WEDSTRIJDEN_WIJZIG_SESSIES = 'wedstrijden/wijzig-sessies.dtl'
TEMPLATE_WEDSTRIJDEN_WIJZIG_SESSIE = 'wedstrijden/wijzig-sessie.dtl'


class WedstrijdSessiesView(UserPassesTestMixin, View):

    """ Via deze view kunnen de HWL en BB de sessies van een wedstrijd wijzigen """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_WIJZIG_SESSIES
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_HWL)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        context['wed'] = wedstrijd
        sessies = (wedstrijd
                   .sessies
                   .prefetch_related('wedstrijdklassen')
                   .order_by('datum',
                             'tijd_begin',
                             'beschrijving'))
        for sessie in sessies:
            # sessie.klassen_ordered = sessie.wedstrijdklassen.order_by('volgorde')
            #
            # if wedstrijd.organisatie == ORGANISATIE_IFAA:
            #     for klasse in sessie.klassen_ordered:
            #         klasse.beschrijving += ' [%s]' % klasse.afkorting
            #     # for

            sessie.url_wijzig = reverse('Wedstrijden:wijzig-sessie',
                                        kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                'sessie_pk': sessie.pk})
        # for
        context['sessies'] = sessies

        if wedstrijd.status != WEDSTRIJD_STATUS_GEANNULEERD:
            context['url_nieuwe_sessie'] = reverse('Wedstrijden:wijzig-sessies',
                                                   kwargs={'wedstrijd_pk': wedstrijd.pk})

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Wedstrijd sessies'),
            )
        else:
            context['kruimels'] = (
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
                (None, 'Wedstrijd sessies'),
            )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        try:
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=kwargs['wedstrijd_pk']))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        if wedstrijd.status != WEDSTRIJD_STATUS_GEANNULEERD and request.POST.get('nieuwe_sessie', ''):
            # voeg een nieuwe sessie toe aan deze wedstrijd
            sessie = WedstrijdSessie(
                            datum=wedstrijd.datum_begin,
                            tijd_begin='10:00',
                            tijd_einde='15:00',
                            max_sporters=50)
            sessie.save()
            wedstrijd.sessies.add(sessie)

            # zet alle klassen default 'aan'
            wkl_pks = wedstrijd.wedstrijdklassen.all().values_list('pk', flat=True)
            sessie.wedstrijdklassen.set(wkl_pks)
        else:
            pass

        url = reverse('Wedstrijden:wijzig-sessies',
                      kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)


class WijzigWedstrijdSessieView(UserPassesTestMixin, View):

    """ Via deze view kunnen de HWL en BB een sessie wijzigen """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_WIJZIG_SESSIE
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MWZ, Rol.ROL_HWL)

    @staticmethod
    def _maak_opt_datums(wedstrijd, sessie):
        """ geef de keuzes terug voor de wedstrijddatum """
        datums = list()

        # duur van een wedstrijd is maximaal 5 dagen
        datum_offset = wedstrijd.datum_begin
        for lp in range(WEDSTRIJD_DUUR_MAX_DAGEN):
            if lp == 0 or datum_offset <= wedstrijd.datum_einde:
                datum = SimpleNamespace()
                datum.sel = 'datum_%s' % lp
                datum.datum = datum_offset
                datum.selected = (datum_offset == sessie.datum)
                datums.append(datum)
                datum_offset += datetime.timedelta(days=1)
        # for

        return datums

    @staticmethod
    def _maak_opt_duur(sessie):
        """ Bouw een lijst op met keuzes die steeds 30 min omhoog gaan """

        mins_begin = sessie.tijd_begin.hour * 60 + sessie.tijd_begin.minute
        mins_einde = sessie.tijd_einde.hour * 60 + sessie.tijd_einde.minute
        gekozen = mins_einde - mins_begin
        if gekozen < 0:
            gekozen += 24 * 60

        duur = list()
        lengte = 30
        while lengte <= WEDSTRIJD_DUUR_MAX_UREN * 60:
            opt = SimpleNamespace()
            opt.sel = "duur_%d" % lengte
            uren = int(lengte / 60)
            if lengte - uren * 60:
                if uren == 0:
                    opt.keuze_str = mark_safe("&frac12; uur")
                else:
                    opt.keuze_str = mark_safe("%d&frac12; uur" % uren)
            else:
                opt.keuze_str = "%d uur" % uren
            opt.selected = (gekozen == lengte)
            duur.append(opt)
            lengte += 30
        # while

        return duur

    @staticmethod
    def _maak_opt_klassen(wedstrijd, sessie):
        """ maak een lijst met wedstrijdklassen die gekozen kunnen worden """

        pks = list(sessie.wedstrijdklassen.values_list('pk', flat=True))

        klassen = (wedstrijd
                   .wedstrijdklassen
                   .select_related('leeftijdsklasse')
                   .order_by('volgorde'))

        for klasse in klassen:
            klasse.sel = 'klasse_%s' % klasse.pk
            klasse.selected = (klasse.pk in pks)

            # voeg afkorting toe aan klasse beschrijving
            if wedstrijd.organisatie == ORGANISATIE_IFAA:
                klasse.beschrijving += ' [%s]' % klasse.afkorting
        # for

        return klassen

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        context['wedstrijd'] = wedstrijd

        try:
            sessie_pk = int(str(kwargs['sessie_pk'])[:6])     # afkappen voor de veiligheid
            sessie = (WedstrijdSessie
                      .objects
                      .get(pk=sessie_pk))
        except WedstrijdSessie.DoesNotExist:
            raise Http404('Sessie niet gevonden')

        context['sessie'] = sessie

        if wedstrijd.sessies.filter(pk=sessie.pk).count() != 1:
            raise Http404('Sessie hoort niet bij wedstrijd')

        if wedstrijd.datum_begin != wedstrijd.datum_einde:
            context['opt_datums'] = self._maak_opt_datums(wedstrijd, sessie)

        sessie.tijd_begin_str = sessie.tijd_begin.strftime('%H:%M')

        context['opt_duur'] = self._maak_opt_duur(sessie)

        context['opt_klassen'] = self._maak_opt_klassen(wedstrijd, sessie)

        context['url_opslaan'] = reverse('Wedstrijden:wijzig-sessie',
                                         kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                 'sessie_pk': sessie.pk})

        if wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD:
            context['niet_verwijderbaar'] = True
        else:
            context['url_verwijder'] = context['url_opslaan']

        if self.rol_nu == Rol.ROL_HWL:
            url_top = reverse('Wedstrijden:vereniging')
        else:
            url_top = reverse('Wedstrijden:manager')

        url_terug = reverse('Wedstrijden:wijzig-sessies',
                            kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['kruimels'] = (
            (url_top, 'Wedstrijdkalender'),
            (url_terug, 'Wedstrijd sessies'),
            (None, 'Wijzig sessie')
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        try:
            sessie_pk = int(str(kwargs['sessie_pk'])[:6])     # afkappen voor de veiligheid
            sessie = (WedstrijdSessie
                      .objects
                      .get(pk=sessie_pk))
        except WedstrijdSessie.DoesNotExist:
            raise Http404('Sessie niet gevonden')

        if wedstrijd.sessies.filter(pk=sessie.pk).count() != 1:
            raise Http404('Sessie hoort niet bij wedstrijd')

        if request.POST.get('verwijder_sessie', ''):
            if wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD:
                raise Http404('Wedstrijd is geannuleerd')

            if sessie.wedstrijdinschrijving_set.count() > 0:
                raise Http404('Sessie heeft aanmeldingen')

            sessie.delete()
        else:
            updated = list()

            beschr = request.POST.get('beschrijving', '')[:50]
            if beschr != sessie.beschrijving:
                sessie.beschrijving = beschr
                updated.append('beschrijving')

            datum = request.POST.get('datum', '')       # bevat 'datum_N'
            if datum.startswith('datum_'):
                datum_offset = wedstrijd.datum_begin
                for lp in range(WEDSTRIJD_DUUR_MAX_DAGEN):
                    if lp == 0 or datum_offset <= wedstrijd.datum_einde:
                        sel = 'datum_%s' % lp
                        if sel == datum:
                            sessie.datum = datum_offset
                            updated.append('datum')
                            break       # from the for

                    datum_offset += datetime.timedelta(days=1)
                # for

            tijd_begin = request.POST.get('tijd_begin', '')
            if tijd_begin:
                # validate the input
                try:
                    tijd = datetime.datetime.strptime(tijd_begin, '%H:%M')
                except ValueError:
                    raise Http404('Geen valide tijd')

                sessie.tijd_begin = tijd_begin
                updated.append('tijd_begin')

                duur = request.POST.get('duur', '')             # bevat 'duur_NN'
                if duur.startswith('duur_'):
                    lengte = 30
                    while lengte <= WEDSTRIJD_DUUR_MAX_UREN * 60:
                        sel = "duur_%d" % lengte
                        if duur == sel:
                            base = tijd.hour * 60 + tijd.minute
                            base += lengte
                            if base >= 24 * 60:          # wrap-around middernacht
                                base -= 24 * 60
                            uren = int(base / 60)
                            sessie.tijd_einde = "%d:%02d" % (uren, base - uren * 60)
                            updated.append('tijd_einde')
                            break       # from the while

                        lengte += 30
                    # while

            sporters = request.POST.get('max_sporters', '')
            if sporters:
                try:
                    sporters = int(sporters[:4])        # afkappen voor de veiligheid
                except ValueError:
                    raise Http404('Geen toegestaan aantal sporters')

                if sporters < 1 or sporters > 999:
                    raise Http404('Geen toegestaan aantal sporters')

                sessie.max_sporters = sporters
                updated.append('max_sporters')

            sessie.save(update_fields=updated)

            gekozen = list()
            for klasse in wedstrijd.wedstrijdklassen.all():
                if request.POST.get('klasse_%s' % klasse.pk, ''):
                    gekozen.append(klasse)
            # for
            sessie.wedstrijdklassen.set(gekozen)

        url = reverse('Wedstrijden:wijzig-sessies',
                      kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)

# end of file
