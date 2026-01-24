# -*- coding: utf-8 -*-
#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_BK
from Competitie.models import Competitie, CompetitieMatch, Kampioenschap, CompetitieIndivKlasse, CompetitieTeamKlasse
from CompKampioenschap.models import SheetStatus
from CompUitslagen.operations import (maak_url_uitslag_bk_indiv, maak_url_uitslag_bk_teams,
                                      maak_url_uitslag_rk_indiv, maak_url_uitslag_rk_teams)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from GoogleDrive.models import Bestand

TEMPLATE_COMPKAMPIOENSCHAP_WF_STATUS = 'compkampioenschap/wf-status.dtl'


class StatusView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de manager om het de status van de wedstrijdformulieren te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPKAMPIOENSCHAP_WF_STATUS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    @staticmethod
    def _get_werk():
        werk = list()
        for comp in Competitie.objects.all():
            comp.bepaal_fase()

            is_teams = False
            if 'J' <= comp.fase_indiv <= 'L':
                is_bk = False
                tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                werk.append(tup)

            if 'N' <= comp.fase_indiv <= 'P':
                is_bk = True
                tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                werk.append(tup)

            if False:  # teams are Excel, for now
                is_teams = True
                if 'J' <= comp.fase_teams <= 'L':
                    is_bk = False
                    tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                    werk.append(tup)

                if 'N' <= comp.fase_teams <= 'P':
                    is_bk = True
                    tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                    werk.append(tup)

        # for
        return werk

    @staticmethod
    def _get_uitslag_url(comp: Competitie, bestand: Bestand, klasse: CompetitieIndivKlasse | CompetitieTeamKlasse):
        seizoen_url = comp.maak_seizoen_url()
        klasse_str = klasse.beschrijving

        if bestand.is_teams:
            team_type_url = klasse.team_type.afkorting.lower()
            if bestand.is_bk:
                url = maak_url_uitslag_bk_teams(seizoen_url, team_type_url, klasse_str)
            else:
                url = maak_url_uitslag_rk_teams(seizoen_url, bestand.rayon_nr, team_type_url, klasse_str)
        else:
            # indiv
            boog_type_url = klasse.boogtype.afkorting.lower()
            if bestand.is_bk:
                url = maak_url_uitslag_bk_indiv(seizoen_url, boog_type_url, klasse_str)
            else:
                url = maak_url_uitslag_rk_indiv(seizoen_url, bestand.rayon_nr, boog_type_url, klasse_str)

        return url

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        werk = self._get_werk()

        match_pk2deelkamp = dict()
        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('competitie',
                                         'rayon')
                         .prefetch_related('rk_bk_matches')):

            match_pks = list(deelkamp.rk_bk_matches.all().values_list('pk', flat=True))
            for pk in match_pks:
                match_pk2deelkamp[pk] = deelkamp
            # for
        # for
        all_match_pks = list(match_pk2deelkamp.keys())

        tup2status = dict()
        for status in (SheetStatus
                       .objects
                       .select_related('bestand')
                       .order_by('bestand__fname')):

            bestand = status.bestand
            tup = (bestand.begin_jaar, bestand.afstand, bestand.is_bk, bestand.is_teams)
            if tup[:4] in werk:
                status.url_open_wf = "https://docs.google.com/spreadsheets/d/%s/edit" % status.bestand.file_id

                pos = status.gewijzigd_door.find('@')
                if pos > 0:
                    status.gewijzigd_door = status.gewijzigd_door[:pos]

                # improve voor word break
                status.bestand.fname = status.bestand.fname.replace('_', ' ')
                status.bestand.fname = status.bestand.fname.replace('individueel-', 'individueel ')
                status.bestand.fname = status.bestand.fname.replace('-onder', ' onder')
                status.bestand.fname = status.bestand.fname.replace('-jeugd', ' jeugd')
                status.bestand.fname = status.bestand.fname.replace('-klasse', ' klasse')

                tup = (bestand.begin_jaar, bestand.afstand, bestand.is_bk, bestand.is_teams, bestand.rayon_nr, bestand.klasse_pk)
                tup2status[tup] = status
        # for

        context['matches'] = matches = list()

        prev_datum = None
        for match in (CompetitieMatch
                      .objects
                      .filter(pk__in=all_match_pks)
                      .select_related('competitie',
                                      'vereniging')
                      .prefetch_related('indiv_klassen',
                                        'team_klassen')
                      .order_by('datum_wanneer',
                                'vereniging__regio__rayon_nr',
                                'vereniging__ver_nr')):

            deelkamp = match_pk2deelkamp[match.pk]
            comp = deelkamp.competitie
            afstand = int(comp.afstand)
            is_bk = deelkamp.deel == DEEL_BK
            if is_bk:
                rayon_nr = 0
            else:
                rayon_nr = deelkamp.rayon.rayon_nr

            match.status_list = list()

            for klasse in match.indiv_klassen.select_related('boogtype'):
                tup = (comp.begin_jaar, afstand, is_bk, False, rayon_nr, klasse.pk)
                try:
                    status = tup2status[tup]
                except KeyError:
                    pass
                else:
                    print(status.uitslag_is_compleet, status.uitslag_ingelezen_op, status.gewijzigd_op,)
                    if status.uitslag_is_compleet and status.uitslag_ingelezen_op < status.gewijzigd_op:
                        status.url_importeer = reverse('CompKampioenschap:importeer-uitslag-indiv',
                                                       kwargs={'status_pk': status.pk})
                    status.url_uitslag = self._get_uitslag_url(comp, status.bestand, klasse)
                    match.status_list.append(status)
            # for

            for klasse in match.team_klassen.select_related('team_type'):
                tup = (comp.begin_jaar, afstand, is_bk, True, rayon_nr, klasse.pk)
                try:
                    # TODO: no SheetStatus records exist for teams, right now
                    status = tup2status[tup]
                except KeyError:
                    pass
                else:
                    if status.uitslag_is_compleet and status.uitslag_ingelezen_op < status.gewijzigd_op:
                        status.url_importeer = reverse('CompKampioenschap:importeer-uitslag-teams',
                                                       kwargs={'status_pk': status.pk})
                    status.url_uitslag = self._get_uitslag_url(comp, status.bestand, klasse)
                    match.status_list.append(status)
            # for

            if len(match.status_list) > 0:
                if prev_datum != match.datum_wanneer:
                    match.do_header = True
                    prev_datum = match.datum_wanneer

                matches.append(match)
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Status wedstrijdformulieren'),
        )

        return context



# end of file
