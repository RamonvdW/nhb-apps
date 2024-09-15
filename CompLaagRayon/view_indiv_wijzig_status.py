# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import DEEL_RK, MUTATIE_KAMP_AFMELDEN_INDIV, MUTATIE_KAMP_AANMELDEN_INDIV
from Competitie.models import KampioenschapSporterBoog, CompetitieMutatie
from Functie.definities import Rollen, rol2url
from Functie.rol import rol_get_huidige_functie, rol_get_huidige
from Overig.background_sync import BackgroundSync
from Sporter.operations import get_sporter
import time


TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_DEELNEMER = 'complaagrayon/wijzig-status-rk-deelnemer.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class WijzigStatusRkDeelnemerView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO en HWL de status van een RK deelnemer aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_DEELNEMER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_RKO, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap__competitie',
                                         'kampioenschap__rayon',
                                         'sporterboog__sporter',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk,
                              kampioenschap__deel=DEEL_RK))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL and deelnemer.bij_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Geen sporter van jouw vereniging')

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelnemer.kampioenschap.functie:
            raise PermissionDenied('Geen toegang tot deze competitie')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K'):
            raise Http404('Mag niet wijzigen')

        sporter = deelnemer.sporterboog.sporter
        deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

        if deelnemer.bij_vereniging:
            deelnemer.ver_str = str(deelnemer.bij_vereniging)
        else:
            deelnemer.ver_str = "?"

        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('CompLaagRayon:wijzig-status-rk-deelnemer',
                                        kwargs={'deelnemer_pk': deelnemer.pk})

        if self.rol_nu == Rollen.ROL_RKO:
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRayon:lijst-rk', kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk}), 'RK selectie'),
                (None, 'Wijzig sporter status')
            )
        else:
            # HWL
            url_overzicht = reverse('Vereniging:overzicht')
            anker = '#competitie_%s' % comp.pk
            context['kruimels'] = (
                (url_overzicht, 'Beheer Vereniging'),
                (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRayon:lijst-rk-ver', kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk}), 'Deelnemers RK'),
                (None, 'Wijzig sporter status')
            )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruiker op de knop drukt om een wijziging door te voeren """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__competitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K'):
            raise Http404('Mag niet wijzigen')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        if self.rol_nu == Rollen.ROL_HWL and deelnemer.bij_vereniging != self.functie_nu.vereniging:
            raise PermissionDenied('Geen sporter van jouw vereniging')

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelnemer.kampioenschap.functie:
            raise PermissionDenied('Geen toegang tot deze competitie')

        account = get_account(request)
        door_str = "%s %s" % (rol2url[self.rol_nu], account.get_account_full_name())

        if bevestig == "1":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Sporter moet lid zijn bij een vereniging')
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AANMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        elif afmelden == "1":
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AFMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        else:
            mutatie = None

        if mutatie:
            mutatie.save()
            mutatie_ping.ping()

            if snel != '1':         # pragma: no cover
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        if self.rol_nu == Rollen.ROL_RKO:
            url = reverse('CompLaagRayon:lijst-rk',
                          kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk})
        else:
            url = reverse('CompLaagRayon:lijst-rk-ver',
                          kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk})

        return HttpResponseRedirect(url)


class SporterWijzigStatusRkDeelnameView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de sporter zelf de status van RK deelname aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruiker op de knop drukt om een wijziging te maken """

        account = get_account(request)
        sporter = get_sporter(account)

        pk = request.POST.get('deelnemer', '?')[:7]     # afkappen voor de veiligheid

        try:
            pk = int(pk)
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__competitie')
                         .get(pk=pk,
                              sporterboog__sporter=sporter,
                              kampioenschap__deel=DEEL_RK))
        except (ValueError, TypeError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K'):       # TODO: toestaan in de laatste 2 weken voor de wedstrijd (=fase L)?
            raise Http404('Mag niet wijzigen')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        door_str = account.get_account_full_name()

        if bevestig == "1":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Je moet lid zijn bij een vereniging')
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AANMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        elif afmelden == "1":
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AFMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        else:
            mutatie = None

        if mutatie:
            mutatie.save()
            mutatie_ping.ping()

            if snel != '1':         # pragma: no cover
                # wacht maximaal 3 seconden tot de mutatie uitgevoerd is
                interval = 0.2      # om steeds te verdubbelen
                total = 0.0         # om een limiet te stellen
                while not mutatie.is_verwerkt and total + interval <= 3.0:
                    time.sleep(interval)
                    total += interval   # 0.0 --> 0.2, 0.6, 1.4, 3.0
                    interval *= 2       # 0.2 --> 0.4, 0.8, 1.6, 3.2
                    mutatie = CompetitieMutatie.objects.get(pk=mutatie.pk)
                # while

        url = reverse('Sporter:profiel')
        return HttpResponseRedirect(url)


# end of file
