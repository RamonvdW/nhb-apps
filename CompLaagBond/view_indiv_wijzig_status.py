# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import (DEEL_BK,
                                   DEELNAME_JA, DEELNAME_NEE,
                                   MUTATIE_KAMP_AFMELDEN_INDIV, MUTATIE_KAMP_AANMELDEN_INDIV)
from Competitie.models import Kampioenschap, KampioenschapSporterBoog, CompetitieMutatie
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_huidige
from Overig.background_sync import BackgroundSync
from Sporter.models import SporterVoorkeuren
from Sporter.operations import get_sporter
import time


TEMPLATE_COMPBOND_WIJZIG_STATUS_BK_DEELNEMER = 'complaagbond/wijzig-status-bk-deelnemer.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class WijzigStatusBkDeelnemerView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de BKO de status van een BK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBOND_WIJZIG_STATUS_BK_DEELNEMER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__functie',
                                         'kampioenschap__competitie',
                                         'sporterboog__sporter',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk,
                              kampioenschap__deel=DEEL_BK))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.functie_nu != deelnemer.kampioenschap.functie:
            raise PermissionDenied('Niet de beheerder')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('N', 'O', 'P'):
            raise Http404('Mag nog niet wijzigen')

        sporter = deelnemer.sporterboog.sporter
        deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

        if deelnemer.bij_vereniging:
            deelnemer.ver_str = str(deelnemer.bij_vereniging)
        else:
            deelnemer.ver_str = "?"

        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('CompLaagBond:wijzig-status-bk-deelnemer',
                                        kwargs={'deelnemer_pk': deelnemer.pk})

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht',
                     kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (reverse('CompLaagBond:bk-selectie',
                     kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk}), 'BK selectie'),
            (None, 'Wijzig sporter status')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de beheerder op de knop OPSLAAN drukt """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__functie',
                                         'kampioenschap__competitie')
                         .get(pk=deelnemer_pk,
                              kampioenschap__deel=DEEL_BK))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.functie_nu != deelnemer.kampioenschap.functie:
            raise PermissionDenied('Niet de beheerder')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('N', 'O', 'P'):
            raise Http404('Mag niet meer wijzigen')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        account = get_account(request)
        door_str = "BKO %s" % account.volledige_naam()

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

        url = reverse('CompLaagBond:bk-selectie',
                      kwargs={'deelkamp_pk': deelnemer.kampioenschap.pk})

        return HttpResponseRedirect(url)


class SporterWijzigStatusBkDeelnameView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de sporter zelf de status van BK deelname aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    @staticmethod
    def post(request, *args, **kwargs):
        """ wordt aangeroepen als de sporter op de knop drukt om een wijziging te maken """

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
                              kampioenschap__deel=DEEL_BK))
        except (ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        comp = deelnemer.kampioenschap.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('N', 'O', 'P'):
            raise Http404('Mag niet wijzigen')

        keuze = str(request.POST.get('keuze', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        door_str = account.get_account_full_name()

        if keuze == "J":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Je moet lid zijn bij een vereniging')
            mutatie = CompetitieMutatie(mutatie=MUTATIE_KAMP_AANMELDEN_INDIV,
                                        deelnemer=deelnemer,
                                        door=door_str)
        elif keuze == "N":
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
