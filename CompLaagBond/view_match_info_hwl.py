# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.definities import DEEL_BK, DEELNAME_NEE
from Competitie.models import CompetitieMatch, KampioenschapSporterBoog, KampioenschapTeam
from CompKampioenschap.operations import get_url_wedstrijdformulier
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Scheidsrechter.models import MatchScheidsrechters
from Sporter.models import SporterVoorkeuren
import textwrap

TEMPLATE_HWL_BK_MATCH_INFORMATIE = 'complaagbond/hwl-bk-match-info.dtl'


class BkMatchInfoView(UserPassesTestMixin, TemplateView):

    """ Toon de HWL/WL informatie over de BK wedstrijd, inclusief deelnemerslijst en download knoppen """

    # class variables shared by all instances
    template_name = TEMPLATE_HWL_BK_MATCH_INFORMATIE
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft
    permission_denied_message = 'Geen toegang'
    geef_teams = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.functie_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and rol_nu in (Rol.ROL_HWL, Rol.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            match_pk = int(kwargs['match_pk'][:6])      # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .select_related('vereniging',
                                     'locatie')
                     .prefetch_related('indiv_klassen',
                                       'team_klassen')
                     .get(pk=match_pk))
        except (ValueError, CompetitieMatch.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if match.vereniging != self.functie_nu.vereniging:
            raise Http404('Niet de beheerder')

        context['wedstrijd'] = match
        context['vereniging'] = match.vereniging        # als we hier komen is dit altijd bekend
        context['locatie'] = match.locatie

        comp = match.competitie
        comp.bepaal_fase()
        # TODO: begrens toegang ahv de fase
        context['comp'] = comp

        deelkamps = match.kampioenschap_set.filter(deel=DEEL_BK)
        if len(deelkamps) == 0:
            raise Http404('Geen kampioenschap')
        deelkamp = deelkamps[0]
        context['deelkamp'] = deelkamp

        if comp.is_indoor():
            aantal_pijlen = 30
            if match.locatie:
                context['aantal_banen'] = match.locatie.banen_18m
        else:
            aantal_pijlen = 25
            if match.locatie:
                context['aantal_banen'] = match.locatie.banen_25m

        heeft_indiv = heeft_teams = False
        beschr = list()

        klasse_indiv_pks = list()
        klasse_team_pks = list()
        match.klassen_lijst = klassen_lijst = list()
        for klasse in match.indiv_klassen.select_related('boogtype').all():
            klassen_lijst.append(str(klasse))
            klasse_indiv_pks.append(klasse.pk)
            if not heeft_indiv:
                heeft_indiv = True
                beschr.append('Individueel')
        # for
        for klasse in match.team_klassen.all():
            klassen_lijst.append(klasse.beschrijving)
            klasse_team_pks.append(klasse.pk)
            if not heeft_teams:
                heeft_teams = True
                beschr.append('Teams')
        # for

        lid2voorkeuren = dict()  # [lid_nr] = (SporterVoorkeuren: .para_voorwerpen, .opmerking_para_sporter)
        for tup in SporterVoorkeuren.objects.select_related('sporter').values_list('sporter__lid_nr',
                                                                                   'para_voorwerpen',
                                                                                   'opmerking_para_sporter'):
            lid_nr, para_voorwerpen, opmerking_para_sporter = tup
            lid2voorkeuren[lid_nr] = (para_voorwerpen, opmerking_para_sporter)
        # for

        vastgesteld = timezone.localtime(timezone.now())
        context['vastgesteld'] = vastgesteld

        context['heeft_indiv'] = heeft_indiv
        context['heeft_teams'] = heeft_teams
        context['beschrijving'] = "Bondskampioenschappen %s" % " en ".join(beschr)

        # zoek de deelnemers erbij
        if heeft_indiv:
            deelnemers = (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=deelkamp,
                                  indiv_klasse__pk__in=klasse_indiv_pks)
                          .exclude(deelname=DEELNAME_NEE)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'bij_vereniging',
                                          'indiv_klasse')
                          .order_by('indiv_klasse',
                                    'rank'))
            context['deelnemers_indiv'] = deelnemers

            prev_klasse = None
            for deelnemer in deelnemers:
                if deelnemer.indiv_klasse != prev_klasse:
                    deelnemer.break_before = True
                    deelnemer.url_open_indiv = get_url_wedstrijdformulier(comp.begin_jaar, int(comp.afstand),
                                                                          0,        # rayon_nr n.v.t.
                                                                          deelnemer.indiv_klasse.pk,
                                                                          is_bk=True, is_teams=False)
                    prev_klasse = deelnemer.indiv_klasse

                deelnemer.ver_nr = deelnemer.bij_vereniging.ver_nr
                deelnemer.ver_naam = deelnemer.bij_vereniging.naam
                deelnemer.lid_nr = deelnemer.sporterboog.sporter.lid_nr
                deelnemer.volledige_naam = deelnemer.sporterboog.sporter.volledige_naam()
                deelnemer.gemiddelde_str = "%.3f" % deelnemer.gemiddelde
                deelnemer.gemiddelde_str = deelnemer.gemiddelde_str.replace('.', ',')

                try:
                    voorkeuren_para_voorwerpen, voorkeuren_opmerking_para_sporter = lid2voorkeuren[deelnemer.lid_nr]
                except KeyError:        # pragma: no cover
                    pass
                else:
                    if voorkeuren_para_voorwerpen:
                        if deelnemer.kampioen_label != '':
                            deelnemer.kampioen_label += ';\n'
                        deelnemer.kampioen_label += 'Sporter laat voorwerpen\nop de schietlijn staan'

                    if voorkeuren_opmerking_para_sporter:
                        if deelnemer.kampioen_label != '':
                            deelnemer.kampioen_label += ';\n'
                        deelnemer.kampioen_label += textwrap.fill(voorkeuren_opmerking_para_sporter, 30)

                # if 'J' <= comp.fase_indiv <= 'K':
                #     deelnemer.url_wijzig = reverse('CompLaagRayon:wijzig-status-rk-deelnemer',
                #                                    kwargs={'deelnemer_pk': deelnemer.pk})
            # for

        if heeft_teams:
            teams = (KampioenschapTeam
                     .objects
                     .filter(kampioenschap=deelkamp,
                             team_klasse__pk__in=klasse_team_pks,
                             rank__lte=8)
                     .exclude(deelname=DEELNAME_NEE)
                     .select_related('vereniging',
                                     'team_klasse')
                     .prefetch_related('gekoppelde_leden')
                     .order_by('team_klasse__volgorde',
                               'rank'))
            context['deelnemers_teams'] = teams

            if not comp.klassengrenzen_vastgesteld_rk_bk:
                context['geen_klassengrenzen'] = True

            volg_nr = 0
            prev_klasse = None
            for team in teams:
                if team.team_klasse != prev_klasse:
                    team.break_before = True
                    team.url_download_teams = reverse('CompLaagBond:formulier-teams-als-bestand',
                                                      kwargs={'match_pk': match.pk,
                                                              'klasse_pk': team.team_klasse.pk})

                    prev_klasse = team.team_klasse
                    volg_nr = 0

                volg_nr += 1
                team.volg_nr = volg_nr
                team.ver_nr = team.vereniging.ver_nr
                team.ver_naam = team.vereniging.naam
                team.sterkte_str = str(round(team.aanvangsgemiddelde))      # RK score

                team.gekoppelde_leden_lijst = list()
                for lid in team.gekoppelde_leden.select_related('sporterboog__sporter').order_by('-gemiddelde'):
                    sporter = lid.sporterboog.sporter
                    lid.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                    lid.gem_str = '%.3f' % lid.gemiddelde

                    try:
                        voorkeuren_para_voorwerpen, voorkeuren_opmerking_para_sporter = lid2voorkeuren[sporter.lid_nr]
                    except KeyError:        # pragma: no cover
                        pass
                    else:
                        if voorkeuren_para_voorwerpen or len(voorkeuren_opmerking_para_sporter) > 1:
                            lid.is_para = True

                    team.gekoppelde_leden_lijst.append(lid)
                # for
            # for

        if match.aantal_scheids > 0:
            match_sr = MatchScheidsrechters.objects.filter(match=match).select_related('gekozen_hoofd_sr', 'gekozen_sr1', 'gekozen_sr2').first()
            if match_sr:
                aantal = 0
                for sr in (match_sr.gekozen_hoofd_sr, match_sr.gekozen_sr1, match_sr.gekozen_sr2):
                    if sr:
                        aantal += 1
                # for
                if aantal > 0:              # pragma: no branch
                    context['aantal_sr_str'] = "%s scheidsrechter" % aantal
                    if aantal > 1:
                        context['aantal_sr_str'] += 's'

                    context['url_sr_contact'] = reverse('Scheidsrechter:match-hwl-contact',
                                                        kwargs={'match_pk': match.pk})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('CompScores:wedstrijden'), 'Competitiewedstrijden'),
            (None, "BK programma's")
        )

        return context


# end of file
