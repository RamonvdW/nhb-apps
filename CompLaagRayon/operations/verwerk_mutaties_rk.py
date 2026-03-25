# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import (DEELNAME_JA, DEELNAME_NEE, MUTATIE_KAMP_RK_REINIT_TEST,
                                   MUTATIE_KAMP_RK_WIJZIG_INDIV_CUT, MUTATIE_KAMP_RK_WIJZIG_TEAMS_CUT,
                                   MUTATIE_KAMP_AANMELDEN_RK_INDIV, MUTATIE_KAMP_AFMELDEN_RK_INDIV,
                                   MUTATIE_EXTRA_RK_DEELNEMER, MUTATIE_KAMP_RK_TEAMS_NUMMEREN)
from Competitie.models import CompetitieMutatie, RegiocompetitieSporterBoog
from CompKampioenschap.operations import (VerwerkCompKampMutaties, bepaal_kamp_indiv_deelnemerslijst,
                                          kamp_deelnemer_afmelden, kamp_deelnemer_opnieuw_aanmelden,
                                          _indiv_verlaag_cut, _indiv_verhoog_cut,
                                          maak_mutatie_update_dirty_wedstrijdformulieren, zet_dirty)
from CompLaagRayon.models import KampRK, DeelnemerRK, TeamRK, CutRK, CutTeamRK


class VerwerkMutatiesRayon:

    """
        Afhandeling van de mutatie verzoeken voor de CompLaagRegio applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    @staticmethod
    def _zet_dirty(deelkamp: KampRK, klasse_pk: int, is_team: bool):
        comp = deelkamp.competitie

        is_bk = False
        rayon_nr = deelkamp.rayon.rayon_nr

        zet_dirty(comp.begin_jaar, int(comp.afstand), rayon_nr, klasse_pk, is_bk, is_team)

        maak_mutatie_update_dirty_wedstrijdformulieren(comp)

    def _converteer_rk_teams(self, comp):
        """ converteer de sporters die gekoppeld zijn aan de RK teams
            de RK teams zijn die tijdens de regiocompetitie al aangemaakt door de verenigingen
            en er zijn regiocompetitie sporters aan gekoppeld welke misschien niet gerechtigd zijn.

            controleer ook meteen de vereniging van de deelnemer
            als laatste wordt de team sterkte opnieuw berekend

            het vaststellen van de wedstrijdklasse voor de RK teams volgt later
        """

        # maak een look-up tabel van RegioCompetitieSporterBoog naar KampioenschapSporterBoog
        sporterboog_pk2regiocompetitiesporterboog = dict()
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('bij_vereniging')
                          .filter(regiocompetitie__competitie=comp)):
            sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk] = deelnemer
        # for

        regiocompetitiesporterboog_pk2kampioenschapsporterboog = dict()
        for deelnemer in (DeelnemerRK
                          .objects
                          .select_related('bij_vereniging')
                          .filter(kamp__competitie=comp)):
            try:
                regio_deelnemer = sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk]
            except KeyError:
                self.stdout.write(
                    '[WARNING] Kan regio deelnemer niet vinden voor kampioenschapsporterboog met pk=%s' %
                    deelnemer.pk)
            else:
                regiocompetitiesporterboog_pk2kampioenschapsporterboog[regio_deelnemer.pk] = deelnemer
        # for

        # sporters mogen maar aan 1 team gekoppeld worden
        gekoppelde_deelnemer_pks = list()

        for team in (TeamRK
                     .objects
                     .filter(kamp__competitie=comp)
                     .select_related('vereniging')
                     .prefetch_related('tijdelijke_leden')):

            team_ver_nr = team.vereniging.ver_nr
            deelnemer_pks = list()

            ags = list()

            for pk in team.tijdelijke_leden.values_list('pk', flat=True):
                try:
                    deelnemer = regiocompetitiesporterboog_pk2kampioenschapsporterboog[pk]
                except KeyError:
                    # regio sporter is niet doorgekomen naar het RK en valt dus af
                    pass
                else:
                    # controleer de vereniging
                    if deelnemer.bij_vereniging.ver_nr == team_ver_nr:
                        # controleer dat de deelnemer nog niet aan een RK team gekoppeld is
                        if deelnemer.pk not in gekoppelde_deelnemer_pks:
                            gekoppelde_deelnemer_pks.append(deelnemer.pk)

                            deelnemer_pks.append(deelnemer.pk)
                            ags.append(deelnemer.gemiddelde)
            # for

            team.gekoppelde_leden.set(deelnemer_pks)

            # bepaal de team sterkte
            ags.sort(reverse=True)
            if len(ags) >= 3:
                team.aanvangsgemiddelde = sum(ags[:3])
            else:
                team.aanvangsgemiddelde = 0.0

            # de klasse wordt later bepaald als de klassengrenzen vastgesteld zijn
            team.team_klasse = None

            team.save(update_fields=['aanvangsgemiddelde', 'team_klasse'])
        # for

        # FUTURE: maak een taak aan voor de HWL's om de RK teams te herzien (eerst functionaliteit voor HWL maken)

    def _verwerk_mutatie_rk_teams_opnieuw_nummeren(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: RK teams opnieuw nummeren' % mutatie.pk)
        deelkamp = mutatie.kamp_rk
        team_klasse = mutatie.team_klasse

        self.stdout.write('[INFO] RK teams opnieuw nummeren voor kampioenschap %s team klasse %s' % (deelkamp,
                                                                                                     team_klasse))

        # alleen de rank aanpassen
        rank = 0
        for team in (TeamRK
                     .objects
                     .filter(kamp=deelkamp,
                             team_klasse=team_klasse,
                             deelname=DEELNAME_JA)
                     .order_by('-aanvangsgemiddelde',       # hoogste eerst
                               'volgorde')):                # originele volgorde aanhouden

            rank += 1
            if rank != team.rank:
                team.rank = rank
                team.save(update_fields=['rank'])
        # for

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp, team_klasse.pk, is_team=True)

    def _verwerk_mutatie_extra_rk_deelnemer(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: extra RK deelnemer' % mutatie.pk)
        deelnemer = mutatie.deelnemer_rk

        # gebruik de methode van opnieuw aanmelden om deze sporter op de reserve-lijst te krijgen
        kamp_deelnemer_opnieuw_aanmelden(self.stdout, deelnemer)

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelnemer.kamp, deelnemer.indiv_klasse.pk, is_team=False)

    def _verwerk_mutatie_kamp_aanmelden_rk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden RK' % mutatie.pk)

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = '[%s] Mutatie door %s\n' % (stamp_str, mutatie.door)

        deelnemer = mutatie.deelnemer_rk
        deelnemer.logboek += msg
        deelnemer.save(update_fields=['logboek'])

        if deelnemer.deelname != DEELNAME_JA:
            if deelnemer.deelname == DEELNAME_NEE:
                # Nee naar Ja
                kamp_deelnemer_opnieuw_aanmelden(self.stdout, deelnemer)
            else:
                # Ja of Onbekend naar Ja
                deelnemer.deelname = DEELNAME_JA
                deelnemer.logboek += '[%s] Deelname op Ja gezet\n' % stamp_str
                deelnemer.save(update_fields=['deelname', 'logboek'])
                # verder hoeven we niets te doen: volgorde en rank blijft hetzelfde

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelnemer.kamp, deelnemer.indiv_klasse.pk, is_team=False)

    def _verwerk_mutatie_kamp_afmelden_rk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: afmelden RK' % mutatie.pk)
        deelnemer_rk = mutatie.deelnemer_rk

        kamp_deelnemer_afmelden(self.stdout, mutatie.door, deelnemer_rk)

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelnemer_rk.kamp, deelnemer_rk.indiv_klasse.pk, is_team=False)

    def _verwerk_mutatie_kamp_rk_reinit_test(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: kamp rk (re-)init test' % mutatie.pk)

        # Let op: wordt alleen gebruik vanuit test code

        deelkamp = mutatie.kamp_rk

        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven sporters
        for deelnemer in (DeelnemerRK
                          .objects
                          .filter(kamp=deelkamp)
                          .select_related('indiv_klasse')
                          .distinct('indiv_klasse')):

            bepaal_kamp_indiv_deelnemerslijst(deelkamp, deelnemer.indiv_klasse, zet_boven_cut_op_ja=False)
        # for

    def _verwerk_mutatie_kamp_rk_wijzig_indiv_cut(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste indiv cut' % mutatie.pk)

        cut_oud = mutatie.cut_oud
        cut_nieuw = mutatie.cut_nieuw

        limiet = CutRK.objects.filter(kamp=mutatie.kamp_rk, indiv_klasse=mutatie.indiv_klasse).first()
        deelkamp = mutatie.kamp_rk

        if limiet:
            is_nieuw = False
        else:
            # maak een nieuwe aan
            is_nieuw = True
            limiet = CutRK(kamp=mutatie.kamp_rk, indiv_klasse=mutatie.indiv_klasse)

        if cut_nieuw > cut_oud:
            # limiet verhogen is simpel, want deelnemers blijven deelnemers
            if cut_nieuw == 24:
                # verwijder het limiet record
                if not is_nieuw:
                    limiet.delete()
            else:
                limiet.limiet = cut_nieuw
                limiet.save()

            # de deelnemerslijst opnieuw sorteren op gemiddelde
            _indiv_verhoog_cut(deelkamp, mutatie.indiv_klasse, cut_nieuw)

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelkamp, mutatie.indiv_klasse.pk, is_team=False)

        elif cut_nieuw < cut_oud:
            # limiet is omlaag gezet
            # zorg dat de regiokampioenen er niet af vallen
            limiet.limiet = cut_nieuw
            limiet.save()

            _indiv_verlaag_cut(deelkamp, mutatie.indiv_klasse, cut_oud, cut_nieuw)

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelkamp, mutatie.indiv_klasse.pk, is_team=False)

        # else: cut_oud == cut_nieuw --> doe niets
        #   (dit kan voorkomen als 2 gebruikers tegelijkertijd de cut veranderen)

    def _verwerk_mutatie_kamp_rk_wijzig_teams_cut(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: RK teams cut aanpassen' % mutatie.pk)

        limiet, _ = CutTeamRK.objects.get_or_create(kamp=mutatie.kamp_rk, team_klasse=mutatie.team_klasse)

        if mutatie.cut_nieuw in (4, 8):
            limiet.limiet = mutatie.cut_nieuw
            limiet.save()

        self.stdout.write('[INFO] RK teams limiet is nu %s voor klasse %s' % (limiet.limiet,
                                                                              limiet.team_klasse.beschrijving))

    HANDLERS = {
        MUTATIE_KAMP_RK_WIJZIG_INDIV_CUT: _verwerk_mutatie_kamp_rk_wijzig_indiv_cut,
        MUTATIE_KAMP_RK_WIJZIG_TEAMS_CUT: _verwerk_mutatie_kamp_rk_wijzig_teams_cut,
        MUTATIE_EXTRA_RK_DEELNEMER: _verwerk_mutatie_extra_rk_deelnemer,
        MUTATIE_KAMP_RK_TEAMS_NUMMEREN: _verwerk_mutatie_rk_teams_opnieuw_nummeren,
        MUTATIE_KAMP_AANMELDEN_RK_INDIV: _verwerk_mutatie_kamp_aanmelden_rk_indiv,
        MUTATIE_KAMP_AFMELDEN_RK_INDIV: _verwerk_mutatie_kamp_afmelden_rk_indiv,
        MUTATIE_KAMP_RK_REINIT_TEST: _verwerk_mutatie_kamp_rk_reinit_test,
    }

    def verwerk(self, mutatie: CompetitieMutatie) -> bool:
        """ Verwerk een mutatie die via de database tabel ontvangen is """

        code = mutatie.mutatie
        try:
            mutatie_code_verwerk_functie = self.HANDLERS[code]
        except KeyError:
            # code niet ondersteund door deze plugin
            return False

        mutatie_code_verwerk_functie(self, mutatie)  # noqa
        return True

    def verwerk_in_achtergrond(self):
        # doe een klein beetje werk
        pass


# end of file
