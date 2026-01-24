# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import DEEL_RK, MUTATIE_KAMP_AFMELDEN_INDIV, MUTATIE_KAMP_AANMELDEN_INDIV
from Competitie.models import Competitie, CompetitieIndivKlasse, KampioenschapSporterBoog, CompetitieMutatie
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations import importeert_sheet_uitslag_indiv
from CompUitslagen.operations import (maak_url_uitslag_rk_indiv, maak_url_uitslag_bk_indiv,
                                      maak_url_uitslag_rk_teams, maak_url_uitslag_bk_teams)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie


class ImporteerUitslagIndivView(UserPassesTestMixin, View):

    """ Deze view laat de RKO en HWL de status van een RK deelnemer aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BB

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de beheerder op de knop drukt om een uitslag te importeren """
        try:
            status_pk = int(kwargs['status_pk'][:6])  # afkappen voor de veiligheid
            status = SheetStatus.objects.select_related('bestand').get(pk=status_pk, is_teams=False)
        except (ValueError, SheetStatus.DoesNotExist):
            raise Http404('Niet gevonden')

        bestand = status.bestand
        comp = Competitie.objects.filter(begin_jaar=bestand.begin_jaar, afstand=bestand.afstand).first()
        klasse = CompetitieIndivKlasse.objects.select_related('boogtype').get(pk=bestand.klasse_pk)

        importeert_sheet_uitslag_indiv(comp, klasse, status)

        seizoen_url = comp.maak_seizoen_url()
        klasse_str = klasse.beschrijving
        boog_type_url = klasse.boogtype.afkorting.lower()

        if bestand.is_bk:
            url = maak_url_uitslag_bk_indiv(seizoen_url, boog_type_url, klasse_str)
        else:
            url = maak_url_uitslag_rk_indiv(seizoen_url, bestand.rayon_nr, boog_type_url, klasse_str)

        return HttpResponseRedirect(url)


class ImporteerUitslagTeamsView(UserPassesTestMixin, View):

    """ Deze view laat de RKO en HWL de status van een RK deelnemer aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BB

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de beheerder op de knop drukt om een uitslag te importeren """
        try:
            status_pk = int(kwargs['status_pk'][:6])  # afkappen voor de veiligheid
            status = SheetStatus.objects.select_related('bestand').get(pk=status_pk, is_teams=True)
        except (ValueError, SheetStatus.DoesNotExist):
            raise Http404('Niet gevonden')

        bestand = status.bestand
        comp = Competitie.objects.filter(begin_jaar=bestand.begin_jaar, afstand=bestand.afstand).first()
        klasse = CompetitieIndivKlasse.objects.select_related('boogtype').get(pk=bestand.klasse_pk)

        importeert_sheet_uitslag_teams(comp, klasse, bestand)

        seizoen_url = comp.maak_seizoen_url()
        klasse_str = klasse.beschrijving
        team_type_url = klasse.team_type.afkorting.lower()

        if bestand.is_bk:
            url = maak_url_uitslag_bk_teams(seizoen_url, team_type_url, klasse_str)
        else:
            url = maak_url_uitslag_rk_teams(seizoen_url, bestand.rayon_nr, team_type_url, klasse_str)

        return HttpResponseRedirect(url)


# end of file
