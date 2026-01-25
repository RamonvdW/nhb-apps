# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_RK, DEEL_BK
from Competitie.models import Competitie, CompetitieIndivKlasse, Kampioenschap
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations import importeer_sheet_uitslag_indiv
from CompUitslagen.operations import (maak_url_uitslag_rk_indiv, maak_url_uitslag_bk_indiv,
                                      maak_url_uitslag_rk_teams, maak_url_uitslag_bk_teams)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie

TEMPLATE_COMPKAMPIOENSCHAP_WF_RESULTAAT_IMPORT = 'compkampioenschap/wf-resultaat-import.dtl'


class ImporteerUitslagIndivView(UserPassesTestMixin, View):

    """ Deze view laat de RKO en HWL de status van een RK deelnemer aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BB

    @staticmethod
    def post(request, *args, **kwargs):
        """ wordt aangeroepen als de beheerder op de knop drukt om een uitslag te importeren """
        try:
            status_pk = int(str(kwargs['status_pk'])[:6])  # afkappen voor de veiligheid
            status = SheetStatus.objects.select_related('bestand').get(pk=status_pk,
                                                                       bestand__is_teams=False)
        except (ValueError, SheetStatus.DoesNotExist):
            raise Http404('Niet gevonden')

        bestand = status.bestand
        comp = Competitie.objects.filter(begin_jaar=bestand.begin_jaar, afstand=bestand.afstand).first()
        klasse = CompetitieIndivKlasse.objects.select_related('boogtype').get(pk=bestand.klasse_pk)

        if bestand.is_bk:
            deelkamp = Kampioenschap.objects.filter(competitie=comp,
                                                    deel=DEEL_BK).first()
        else:
            deelkamp = Kampioenschap.objects.filter(competitie=comp,
                                                    deel=DEEL_RK,
                                                    rayon__rayon_nr=bestand.rayon_nr).first()

        if not deelkamp:
            raise Http404('Kampioenschap niet gevonden')

        # TODO: check competitie fase

        context = {
            'deelkamp': deelkamp,
            'klasse': klasse,
            'url_terug': reverse('CompKampioenschap:wf-status'),
        }

        seizoen_url = comp.maak_seizoen_url()
        klasse_str = klasse.beschrijving
        boog_type_url = klasse.boogtype.afkorting.lower()

        if bestand.is_bk:
            context['url_uitslag'] = maak_url_uitslag_bk_indiv(seizoen_url, boog_type_url, klasse_str)
        else:
            context['url_uitslag'] = maak_url_uitslag_rk_indiv(seizoen_url, bestand.rayon_nr, boog_type_url, klasse_str)

        context['bevat_fout'], context['blokjes_info'] = importeer_sheet_uitslag_indiv(deelkamp, klasse, status)

        if not context['bevat_fout']:
            status.uitslag_ingelezen_op = timezone.now()
            status.save(update_fields=['uitslag_ingelezen_op'])

        return render(request, TEMPLATE_COMPKAMPIOENSCHAP_WF_RESULTAAT_IMPORT, context)


class ImporteerUitslagTeamsView(UserPassesTestMixin, View):

    """ Deze view laat de RKO en HWL de status van een RK deelnemer aanpassen """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return rol_nu == Rol.ROL_BB

    @staticmethod
    def post(request, *args, **kwargs):
        """ wordt aangeroepen als de beheerder op de knop drukt om een uitslag te importeren """
        try:
            status_pk = int(kwargs['status_pk'][:6])  # afkappen voor de veiligheid
            status = SheetStatus.objects.select_related('bestand').get(pk=status_pk,
                                                                       bestand__is_teams=True)
        except (ValueError, SheetStatus.DoesNotExist):
            raise Http404('Niet gevonden')

        bestand = status.bestand
        comp = Competitie.objects.filter(begin_jaar=bestand.begin_jaar, afstand=bestand.afstand).first()
        klasse = CompetitieIndivKlasse.objects.select_related('boogtype').get(pk=bestand.klasse_pk)

        if bestand.is_bk:
            deelkamp = Kampioenschap.objects.filter(competitie=comp,
                                                    deel=DEEL_BK).first()
        else:
            deelkamp = Kampioenschap.objects.filter(competitie=comp,
                                                    deel=DEEL_RK,
                                                    rayon__rayon_nr=bestand.rayon_nr).first()

        if not deelkamp:
            raise Http404('Kampioenschap niet gevonden')

        context = {
            'deelkamp': deelkamp,
            'klasse': klasse,
            'url_terug': reverse('CompKampioenschap:wf-status'),
        }

        seizoen_url = comp.maak_seizoen_url()
        klasse_str = klasse.beschrijving
        team_type_url = klasse.team_type.afkorting.lower()

        if bestand.is_bk:
            context['url_uitslag'] = maak_url_uitslag_bk_teams(seizoen_url, team_type_url, klasse_str)
        else:
            context['url_uitslag'] = maak_url_uitslag_rk_teams(seizoen_url, bestand.rayon_nr, team_type_url, klasse_str)

        raise Http404('Niet geïmplementeerd')
        context['bevat_fout'], context['blokjes_info'] = importeer_sheet_uitslag_teams(deelkamp, klasse, bestand)

        return render(request, TEMPLATE_COMPKAMPIOENSCHAP_WF_RESULTAAT_IMPORT, context)


# end of file
