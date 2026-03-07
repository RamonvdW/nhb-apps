# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from CompLaagRayon.operations import maak_mutatie_kamp_aanmelden_rk_indiv, maak_mutatie_kamp_afmelden_rk_indiv
from CompLaagRayon.models import DeelnemerRK
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_huidige, rol_get_beschrijving
from Sporter.operations import get_sporter

TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_DEELNEMER = 'complaagrayon/wijzig-status-rk-deelnemer.dtl'


class WijzigStatusRkDeelnemerView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de RKO en HWL de status van een RK deelnemer aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPRAYON_WIJZIG_STATUS_RK_DEELNEMER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None
        self.kruimel = list()       # voor de get
        self.url_next = ''          # voor na de post

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_RKO, Rol.ROL_HWL)

    def _check_toegang(self, deelnemer: DeelnemerRK):
        comp = deelnemer.kamp.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K', 'L'):
            raise Http404('Mag niet wijzigen')

        if self.rol_nu == Rol.ROL_RKO:
            if self.functie_nu == deelnemer.kamp.functie:
                # RKO van het rayon van het RK

                self.url_next = reverse('CompLaagRayon:lijst-rk',
                                        kwargs={'deelkamp_pk': deelnemer.kamp.pk})

                self.kruimels = (
                    (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                    (reverse('CompBeheer:overzicht',
                             kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
                    (self.url_next, 'RK selectie'),
                    (None, 'Wijzig sporter status')
                )
                return

            raise PermissionDenied('Geen toegang tot deze competitie')

        if self.rol_nu == Rol.ROL_HWL:
            if deelnemer.bij_vereniging == self.functie_nu.vereniging:
                # HWL van vereniging van de sporter

                # afmelden tijdens de wedstrijden (fase L) niet toestaan
                if comp.fase_indiv not in ('J', 'K'):
                    raise Http404('Mag niet wijzigen')

                self.url_next = reverse('CompLaagRayon:lijst-rk-ver',
                                        kwargs={'deelkamp_pk': deelnemer.kamp.pk})

                url_overzicht = reverse('Vereniging:overzicht')
                anker = '#competitie_%s' % comp.pk
                self.kruimels = (
                    (url_overzicht, 'Beheer vereniging'),
                    (url_overzicht + anker, comp.beschrijving.replace(' competitie', '')),
                    (self.url_next, 'Deelnemers RK'),
                    (None, 'Wijzig sporter status')
                )

                return

            # kijk of dit de HWL is van de vereniging die de RK wedstrijd organiseert
            for match in (deelnemer
                          .kamp
                          .matches
                          .filter(vereniging=self.functie_nu.vereniging)
                          .prefetch_related('indiv_klassen')
                          .all()):
                if deelnemer.indiv_klasse in match.indiv_klassen.all():
                    # deze klasse is onderdeel van de RK-wedstrijd bij deze vereniging

                    self.url_next = reverse('CompLaagRayon:download-formulier', kwargs={'match_pk': match.pk})

                    self.kruimels = (
                        (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                        (reverse('CompScores:wedstrijden'), 'Competitiewedstrijden'),
                        (self.url_next, 'RK programma'),
                        (None, 'Wijzig sporter status')
                    )
                    return
            # for

            raise PermissionDenied('Geen sporter van jouw vereniging')

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (DeelnemerRK
                         .objects
                         .select_related('kamp',
                                         'kamp__competitie',
                                         'kamp__rayon',
                                         'sporterboog__sporter',
                                         'bij_vereniging',
                                         'indiv_klasse')
                         .get(pk=deelnemer_pk))
        except (ValueError, DeelnemerRK.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        self._check_toegang(deelnemer)      # kan 403 of 404 geven

        sporter = deelnemer.sporterboog.sporter
        deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

        if deelnemer.bij_vereniging:
            deelnemer.ver_str = str(deelnemer.bij_vereniging)
        else:
            deelnemer.ver_str = "?"

        context['deelnemer'] = deelnemer

        context['url_wijzig'] = reverse('CompLaagRayon:wijzig-status-rk-deelnemer',
                                        kwargs={'deelnemer_pk': deelnemer.pk})

        context['kruimels'] = self.kruimels

        return context

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de beheerder op de knop drukt om een wijziging door te voeren """
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])  # afkappen voor de veiligheid
            deelnemer = (DeelnemerRK
                         .objects
                         .select_related('kamp',
                                         'kamp__competitie',
                                         'kamp__rayon',
                                         'sporterboog__sporter',
                                         'bij_vereniging',
                                         'indiv_klasse')
                         .get(pk=deelnemer_pk))
        except (ValueError, DeelnemerRK.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        bevestig = str(request.POST.get('bevestig', ''))[:2]
        afmelden = str(request.POST.get('afmelden', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        self._check_toegang(deelnemer)

        account = get_account(request)
        door_str = "%s %s" % (rol_get_beschrijving(request), account.get_account_full_name())
        door_str = door_str[:149]       # afkappen zodat het in het veld past

        if bevestig == "1":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Sporter moet lid zijn bij een vereniging')
            maak_mutatie_kamp_aanmelden_rk_indiv(deelnemer, door_str, snel == '1')
        elif afmelden == "1":
            maak_mutatie_kamp_afmelden_rk_indiv(deelnemer, door_str, snel == '1')

        return HttpResponseRedirect(self.url_next)


class SporterWijzigStatusRkDeelnameView(UserPassesTestMixin, TemplateView):

    """ Deze view laat de sporter zelf de status van RK deelname aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rol.ROL_SPORTER

    @staticmethod
    def get(request, *args, **kwargs):
        raise Http404('Niet mogelijk')

    @staticmethod
    def post(request, *args, **kwargs):
        """ wordt aangeroepen als de sporter op de knop drukt om een wijziging te maken """

        account = get_account(request)
        sporter = get_sporter(account)

        pk = request.POST.get('deelnemer', '?')[:7]     # afkappen voor de veiligheid

        try:
            pk = int(pk)
            deelnemer = (DeelnemerRK
                         .objects
                         .select_related('kamp',
                                         'kamp__competitie')
                         .get(pk=pk,
                              sporterboog__sporter=sporter))
        except (ValueError, TypeError, DeelnemerRK.DoesNotExist):
            raise Http404('Deelnemer niet gevonden')

        comp = deelnemer.kamp.competitie
        comp.bepaal_fase()
        if comp.fase_indiv not in ('J', 'K'):
            raise Http404('Mag niet wijzigen')

        keuze = str(request.POST.get('keuze', ''))[:2]
        snel = str(request.POST.get('snel', ''))[:1]

        door_str = account.get_account_full_name()
        door_str = door_str[:149]

        if keuze == "J":
            if not deelnemer.bij_vereniging:
                # kan niet bevestigen zonder verenigingslid te zijn
                raise Http404('Je moet lid zijn bij een vereniging')

            maak_mutatie_kamp_aanmelden_rk_indiv(deelnemer, door_str, snel == '1')

        elif keuze == "N":
            maak_mutatie_kamp_afmelden_rk_indiv(deelnemer, door_str, snel == '1')

        url = reverse('Sporter:profiel')
        return HttpResponseRedirect(url)


# end of file
