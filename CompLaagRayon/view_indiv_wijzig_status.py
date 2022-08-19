# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (KampioenschapSchutterBoog, CompetitieMutatie,
                               MUTATIE_AFMELDEN, MUTATIE_AANMELDEN)
from Functie.rol import Rollen, rol_get_huidige_functie
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
import time


TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_DEELNEMER = 'complaagrayon/wijzig-status-rk-deelnemer.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)


class WijzigStatusRkDeelnemerView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de HWL en RKO de status van een RK selectie aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_DEELNEMER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

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
            deelnemer = (KampioenschapSchutterBoog
                         .objects
                         .select_related('deelcompetitie__competitie',
                                         'deelcompetitie__nhb_rayon',
                                         'sporterboog__sporter',
                                         'bij_vereniging')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSchutterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL and deelnemer.bij_vereniging != self.functie_nu.nhb_ver:
            raise PermissionDenied('Geen sporter van jouw vereniging')

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelnemer.deelcompetitie.functie:
            raise PermissionDenied('Geen toegang tot deze competitie')

        comp = deelnemer.deelcompetitie.competitie
        comp.bepaal_fase()
        if comp.fase < 'J':
            raise Http404('Mag nog niet wijzigen')

        # fase L = wedstrijden, maar dan willen we de RKO toch de status nog aan laten passen
        if comp.fase > 'L':
            raise Http404('Mag niet meer wijzigen')

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
                (reverse('Competitie:kies'), 'Bondscompetities'),
                (reverse('Competitie:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRayon:lijst-rk', kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk}), 'RK selectie'),
                (None, 'Wijzig sporter status')
            )
        else:
            # HWL
            url_overzicht = reverse('Vereniging:overzicht')
            anker = '#competitie_%s' % comp.pk
            context['kruimels'] = (
                (url_overzicht, 'Beheer Vereniging'),
                (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
                (reverse('CompLaagRayon:lijst-rk-ver', kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk}), 'Deelnemers RK'),
                (None, 'Wijzig sporter status')
            )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de gebruik op de knop OPSLAAN druk """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (KampioenschapSchutterBoog
                         .objects
                         .select_related('deelcompetitie',
                                         'deelcompetitie__competitie')
                         .get(pk=deelnemer_pk))
        except (ValueError, KampioenschapSchutterBoog.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        comp = deelnemer.deelcompetitie.competitie
        comp.bepaal_fase()
        if comp.fase < 'J':
            raise Http404('Mag nog niet wijzigen')

        if comp.fase > 'L':
            raise Http404('Mag niet meer wijzigen')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        if self.rol_nu == Rollen.ROL_HWL and deelnemer.bij_vereniging != self.functie_nu.nhb_ver:
            raise PermissionDenied('Geen sporter van jouw vereniging')

        if self.rol_nu == Rollen.ROL_RKO and self.functie_nu != deelnemer.deelcompetitie.functie:
            raise PermissionDenied('Geen toegang tot deze competitie')

        account = request.user
        door_str = "RKO %s" % account.volledige_naam()

        if bevestig == "1":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Sporter moet lid zijn bij een vereniging')
            mutatie = CompetitieMutatie(mutatie=MUTATIE_AANMELDEN,
                                        deelnemer=deelnemer,
                                        door=door_str)
        elif afmelden == "1":
            mutatie = CompetitieMutatie(mutatie=MUTATIE_AFMELDEN,
                                        deelnemer=deelnemer,
                                        door=door_str)
        else:
            mutatie = None

        if mutatie:
            mutatie.save()
            mutatie_ping.ping()

            if snel != '1':
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
                          kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk})
        else:
            url = reverse('CompLaagRayon:lijst-rk-ver',
                          kwargs={'rk_deelcomp_pk': deelnemer.deelcompetitie.pk})

        return HttpResponseRedirect(url)


# end of file
