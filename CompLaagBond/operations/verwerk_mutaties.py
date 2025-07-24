# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEEL_RK, DEEL_BK, DEELNAME_JA, DEELNAME_NEE, KAMP_RANK_BLANCO
from Competitie.models import (Competitie, CompetitieTeamKlasse, KampioenschapTeamKlasseLimiet,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from CompKamp.operations.verwerk_mutaties import VerwerkCompKampMutaties


class VerwerkCompLaagBondMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompLaagRegio applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger

    def maak_deelnemerslijst_bk_indiv(self, comp: Competitie):
        # let op: deze methode wordt rechtstreeks aangeroepen vanuit VerwerkCompBeheerMutaties
        """ bepaal de individuele deelnemers van het BK
            per klasse zijn dit de rayonkampioenen (4x) aangevuld met de sporters met de hoogste kwalificatie scores
            iedereen die scores neergezet heeft in het RK komt in de lijst
        """

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan de BK indiv deelnemerslijst\n" % stamp_str

        if comp.is_indoor():
            aantal_pijlen = 2.0 * 30
        else:
            aantal_pijlen = 2.0 * 25

        deelkamp_bk = Kampioenschap.objects.get(deel=DEEL_BK, competitie=comp)

        # verwijder alle deelnemers van een voorgaande run
        KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp_bk).delete()

        bulk = list()
        for kampioen in (KampioenschapSporterBoog
                         .objects
                         .filter(kampioenschap__competitie=comp,
                                 kampioenschap__deel=DEEL_RK,
                                 result_rank__lte=KAMP_RANK_BLANCO)
                         .exclude(deelname=DEELNAME_NEE)
                         .exclude(result_rank=0)
                         .select_related('kampioenschap',
                                         'kampioenschap__rayon',
                                         'indiv_klasse_volgende_ronde',
                                         'bij_vereniging',
                                         'sporterboog')):

            som_scores = kampioen.result_score_1 + kampioen.result_score_2
            gemiddelde = som_scores / aantal_pijlen

            if kampioen.result_score_1 > kampioen.result_score_2:
                gemiddelde_scores = "%03d%03d" % (kampioen.result_score_1, kampioen.result_score_2)
            else:
                gemiddelde_scores = "%03d%03d" % (kampioen.result_score_2, kampioen.result_score_1)

            # print('kampioen:', kampioen.result_rank, som_scores, gemiddelde_scores, "%.3f" % gemiddelde, kampioen)

            nieuw = KampioenschapSporterBoog(
                        kampioenschap=deelkamp_bk,
                        sporterboog=kampioen.sporterboog,
                        indiv_klasse=kampioen.indiv_klasse_volgende_ronde,
                        indiv_klasse_volgende_ronde=kampioen.indiv_klasse_volgende_ronde,
                        bij_vereniging=kampioen.bij_vereniging,
                        gemiddelde=gemiddelde,
                        gemiddelde_scores=gemiddelde_scores,
                        logboek=msg)

            if kampioen.result_rank == 1:
                nieuw.kampioen_label = 'Kampioen %s' % kampioen.kampioenschap.rayon.naam
                nieuw.deelname = DEELNAME_JA
                nieuw.logboek += '[%s] Deelname op Ja gezet, want kampioen RK\n' % stamp_str

            bulk.append(nieuw)

            if len(bulk) >= 250:
                KampioenschapSporterBoog.objects.bulk_create(bulk)
                bulk = list()
        # for

        if len(bulk):
            KampioenschapSporterBoog.objects.bulk_create(bulk)
        del bulk

        deelkamp_bk.heeft_deelnemerslijst = True
        deelkamp_bk.save(update_fields=['heeft_deelnemerslijst'])

        # bepaal nu voor elke klasse de volgorde van de deelnemers
        # en zit iedereen boven de cut op deelname=ja
        kamp_mutaties = VerwerkCompKampMutaties(self.stdout, self.my_logger)
        kamp_mutaties.verwerk_mutatie_initieel_deelkamp(deelkamp_bk, zet_boven_cut_op_ja=True)

        # TODO: verstuur uitnodigingen per e-mail

        # behoud maximaal 48 sporters in elke klasse: 24 deelnemers en 24 reserves
        qset = KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp_bk, volgorde__gt=48)
        qset.delete()

    @staticmethod
    def _get_limiet_teams(deelkamp, team_klasse):
        # bepaal de limiet
        try:
            limiet = (KampioenschapTeamKlasseLimiet
                      .objects
                      .get(kampioenschap=deelkamp,
                           team_klasse=team_klasse)
                      ).limiet
        except KampioenschapTeamKlasseLimiet.DoesNotExist:
            limiet = 8
            if "ERE" in team_klasse.beschrijving:
                limiet = 12

        return limiet

    def _verwerk_mutatie_initieel_klasse_bk_teams(self, deelkamp, team_klasse):
        # Bepaal de top-X teams voor een klasse van een kampioenschap
        # De kampioenen aangevuld met de teams met hoogste gemiddelde
        # gesorteerde op gemiddelde

        self.stdout.write('[INFO] Bepaal teams voor team_klasse %s van %s' % (team_klasse, deelkamp))

        limiet = self._get_limiet_teams(deelkamp, team_klasse)

        # kampioenen hebben deelnamegarantie
        kampioenen = (KampioenschapTeam
                      .objects
                      .exclude(rk_kampioen_label='')
                      .filter(kampioenschap=deelkamp,
                              team_klasse=team_klasse))

        lijst = list()
        aantal = 0
        for obj in kampioenen:
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
            tup = (obj.aanvangsgemiddelde, len(lijst), obj)
            lijst.append(tup)
        # for

        # aanvullen met teams tot aan de cut
        objs = (KampioenschapTeam
                .objects
                .filter(kampioenschap=deelkamp,
                        team_klasse=team_klasse,
                        rk_kampioen_label='')       # kampioenen hebben we al gedaan
                .order_by('-aanvangsgemiddelde'))   # hoogste boven

        for obj in objs:
            tup = (obj.aanvangsgemiddelde, len(lijst), obj)
            lijst.append(tup)
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
                if aantal >= limiet:
                    break       # uit de for
        # for

        # sorteer op gemiddelde en daarna op de positie in de lijst (want sorteren op obj gaat niet)
        lijst.sort(reverse=True)

        # volgorde uitdelen voor deze kandidaat-deelnemers
        pks = list()
        volgorde = 0
        rank = 0
        for _, _, obj in lijst:
            volgorde += 1
            obj.volgorde = volgorde

            if obj.deelname == DEELNAME_NEE:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank
            obj.save(update_fields=['rank', 'volgorde'])
            pks.append(obj.pk)
        # for

        # geef nu alle andere teams een nieuw volgnummer
        # dit voorkomt dubbele volgnummers als de cut omlaag gezet is
        for obj in objs:
            if obj.pk not in pks:
                volgorde += 1
                obj.volgorde = volgorde

                if obj.deelname == DEELNAME_NEE:
                    obj.rank = 0
                else:
                    rank += 1
                    obj.rank = rank
                obj.save(update_fields=['rank', 'volgorde'])
        # for

    def maak_deelnemerslijst_bk_teams(self, comp):
        # deelfactor om van RK uitslag (60 of 50 pijlen) naar gemiddelde te gaan
        if comp.is_indoor():
            aantal_pijlen = 2.0 * 30
        else:
            aantal_pijlen = 2.0 * 25

        # zoek het BK erbij
        deelkamp_bk = Kampioenschap.objects.select_related('competitie').get(deel=DEEL_BK, competitie=comp)

        # verwijder de al aangemaakte teams
        qset = KampioenschapTeam.objects.filter(kampioenschap=deelkamp_bk).all()
        aantal = qset.count()
        if aantal > 0:
            self.stdout.write('[INFO] Alle %s bestaande BK teams worden verwijderd' % aantal)
            qset.delete()

        # maak een vertaal tabel voor de individuele klassen voor seizoen 2022/2023
        # 141 TR klasse ERE --> 131 BB klasse ERE
        temp_klassen_map = dict()
        # self.stdout.write('[WARNING] TR teams worden aan BB teams toegevoegd')
        # temp_klassen_map[141] = CompetitieTeamKlasse.objects.get(competitie=comp, volgorde=131)

        for klasse in (CompetitieTeamKlasse
                       .objects
                       .filter(competitie=comp,
                               is_voor_teams_rk_bk=True)
                       .order_by('volgorde')):

            is_verplaatst = False
            try:
                team_klasse = temp_klassen_map[klasse.volgorde]
                is_verplaatst = True
            except KeyError:
                # behoud oude klasse
                team_klasse = klasse

            self.stdout.write('[INFO] Team klasse: %s' % klasse)

            if is_verplaatst:
                self.stdout.write('[WARNING] Teams worden samengevoegd met klasse %s' % team_klasse)

            teams_per_ver = dict()  # [ver_nr] = count

            # TODO: volgens reglement Indoor doorzetten:
            #   ERE=2 finalisten per rayon + 4 landelijk resultaat;
            #   rest=1 finalist per rayon + 4 landelijke resultaat
            # TODO: volgens reglement 25m1pijl doorzetten:
            #   ERE=max 32 teams,
            #   B=max 16 teams,
            #   C+D samen max 16 teams.
            #   Alle volgens landelijk resultaat.

            # haal alle teams uit de RK op
            for rk_team in (KampioenschapTeam
                            .objects
                            .filter(kampioenschap__deel=DEEL_RK,
                                    kampioenschap__competitie=comp,
                                    team_klasse_volgende_ronde=klasse,
                                    result_rank__gte=1)
                            .select_related('vereniging',
                                            'team_type')
                            .prefetch_related('gekoppelde_leden')
                            .order_by('-result_teamscore')):        # hoogste resultaat eerst

                ver_nr = rk_team.vereniging.ver_nr
                skip = False
                try:
                    teams_per_ver[ver_nr] += 1
                except KeyError:
                    teams_per_ver[ver_nr] = 1
                else:
                    if teams_per_ver[ver_nr] > 2:
                        self.stdout.write(
                            '[WARNING] Vereniging %s heeft maximum bereikt. Team %s wordt niet opgenomen.' % (
                                ver_nr, rk_team.team_naam))
                        skip = True

                if not skip:
                    ag = rk_team.result_teamscore / aantal_pijlen

                    bk_team = KampioenschapTeam(
                                    kampioenschap=deelkamp_bk,
                                    vereniging=rk_team.vereniging,
                                    volg_nr=rk_team.volg_nr,
                                    team_type=rk_team.team_type,
                                    team_naam=rk_team.team_naam,
                                    team_klasse=team_klasse,
                                    team_klasse_volgende_ronde=team_klasse,
                                    aanvangsgemiddelde=ag)

                    if rk_team.result_rank == 1 and not is_verplaatst:
                        bk_team.rk_kampioen_label = 'Kampioen %s' % rk_team.kampioenschap.rayon.naam
                        bk_team.deelname = DEELNAME_JA

                    bk_team.save()
                    self.stdout.write('[INFO] Maak BK team %s.%s (%s)' % (
                                        rk_team.vereniging.ver_nr, rk_team.volg_nr, rk_team.team_naam))

                    # koppel de RK deelnemers aan het BK team
                    pks = rk_team.gekoppelde_leden.values_list('pk', flat=True)
                    bk_team.gekoppelde_leden.set(pks)
            # for
        # for

        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven teams
        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap=deelkamp_bk)
                     .distinct('team_klasse')):
            # sorteer de lijst op gemiddelde en bepaalde volgorde
            self._verwerk_mutatie_initieel_klasse_bk_teams(deelkamp_bk, team.team_klasse)
        # for


# end of file
