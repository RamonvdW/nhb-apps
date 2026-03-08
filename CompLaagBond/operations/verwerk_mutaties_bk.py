# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import (DEELNAME_JA, DEELNAME_NEE,
                                   MUTATIE_KAMP_AANMELDEN_BK_INDIV, MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                   MUTATIE_KAMP_BK_VERPLAATS_KLASSE_INDIV, MUTATIE_KAMP_BK_TEAMS_NUMMEREN,
                                   MUTATIE_KAMP_BK_WIJZIG_CUT)
from Competitie.models import CompetitieMutatie
from CompKampioenschap.operations import (maak_mutatie_update_dirty_wedstrijdformulieren, zet_dirty,
                                          bepaal_kamp_indiv_deelnemerslijst,
                                          kamp_deelnemer_afmelden, kamp_deelnemer_opnieuw_aanmelden,
                                          _indiv_verlaag_cut, _indiv_verhoog_cut)
from CompLaagBond.models import KampBK, TeamBK, CutBK


class VerwerkMutatiesBond:

    """
        Afhandeling van de mutatie verzoeken voor de CompLaagRegio applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    @staticmethod
    def _zet_dirty(deelkamp: KampBK, klasse_pk: int, is_team: bool):
        comp = deelkamp.competitie

        is_bk = True
        rayon_nr = 0

        zet_dirty(comp.begin_jaar, int(comp.afstand), rayon_nr, klasse_pk, is_bk, is_team)

        maak_mutatie_update_dirty_wedstrijdformulieren(comp)

    def _verwerk_mutatie_bk_teams_opnieuw_nummeren(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: BK teams opnieuw nummeren' % mutatie.pk)
        deelkamp = mutatie.kamp_bk
        team_klasse = mutatie.team_klasse

        self.stdout.write('[INFO] BK teams opnieuw nummeren voor kampioenschap %s team klasse %s' % (deelkamp,
                                                                                                     team_klasse))

        # alleen de rank aanpassen
        rank = 0
        for team in (TeamBK
                     .objects
                     .filter(kamp=deelkamp,
                             team_klasse=team_klasse,
                             deelname=DEELNAME_JA)
                     .order_by('-rk_score',                 # hoogste eerst
                               'volgorde')):                # originele volgorde aanhouden

            rank += 1
            if rank != team.rank:
                team.rank = rank
                team.save(update_fields=['rank'])
        # for

        for team in (TeamBK
                     .objects
                     .filter(kamp=deelkamp,
                             team_klasse=team_klasse)
                     .exclude(deelname=DEELNAME_JA)
                     .order_by('vereniging__regio__rayon_nr',    # rayon 1,2,3,4
                               '-rk_score',                      # hoogste eerst
                               'volgorde')):                     # originele volgorde aanhouden

            rank += 1
            if team.rank != rank:
                team.rank = rank
                team.save(update_fields=['rank'])
        # for

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp, team_klasse.pk, is_team=True)

    def _verwerk_mutatie_kamp_aanmelden_bk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden BK' % mutatie.pk)

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = '[%s] Mutatie door %s\n' % (stamp_str, mutatie.door)

        deelnemer = mutatie.deelnemer_bk
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

    def _verwerk_mutatie_kamp_afmelden_bk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: afmelden BK' % mutatie.pk)
        deelnemer_bk = mutatie.deelnemer_bk

        kamp_deelnemer_afmelden(self.stdout, mutatie.door, deelnemer_bk)

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelnemer_bk.kamp, deelnemer_bk.indiv_klasse.pk, is_team=False)

    def _verwerk_mutatie_kamp_bk_verplaats_deelnemer_naar_andere_klasse(self, mutatie: CompetitieMutatie):
        """ verplaats deelnemer van zijn huidige klasse
            naar de klasse indiv_klasse (CompetitieIndivKlasse)
            en pas daarbij de volgorde en rank aan
        """

        self.stdout.write('[INFO] Verwerk mutatie %s: kleine klassen indiv' % mutatie.pk)
        deelnemer = mutatie.deelnemer_bk
        indiv_klasse = mutatie.indiv_klasse

        if deelnemer.indiv_klasse != indiv_klasse:
            self.stdout.write('[INFO] Verplaats BK deelnemer %s van kleine klasse %s naar klasse %s' % (
                                deelnemer, deelnemer.indiv_klasse, indiv_klasse))

            deelkamp = deelnemer.kamp

            # zorg dat beide google sheets bijgewerkt worden
            self._zet_dirty(deelkamp, indiv_klasse.pk, is_team=False)
            self._zet_dirty(deelkamp, deelnemer.indiv_klasse.pk, is_team=False)

            deelnemer.indiv_klasse = indiv_klasse
            deelnemer.save(update_fields=['indiv_klasse'])

            # stel de deelnemerslijst van de nieuwe klasse opnieuw op
            bepaal_kamp_indiv_deelnemerslijst(deelkamp, indiv_klasse)

    def _verwerk_mutatie_kamp_bk_wijzig_cut(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)

        cut_oud = mutatie.cut_oud
        cut_nieuw = mutatie.cut_nieuw

        limiet = CutBK.objects.filter(kamp=mutatie.kamp_bk, indiv_klasse=mutatie.indiv_klasse).first()
        deelkamp = mutatie.kamp_bk

        if limiet:
            is_nieuw = False
        else:
            # maak een nieuwe aan
            is_nieuw = True
            limiet = CutBK(kamp=mutatie.kamp_bk, indiv_klasse=mutatie.indiv_klasse)

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

    HANDLERS = {
        MUTATIE_KAMP_BK_WIJZIG_CUT: _verwerk_mutatie_kamp_bk_wijzig_cut,
        MUTATIE_KAMP_AANMELDEN_BK_INDIV: _verwerk_mutatie_kamp_aanmelden_bk_indiv,
        MUTATIE_KAMP_AFMELDEN_BK_INDIV: _verwerk_mutatie_kamp_afmelden_bk_indiv,
        MUTATIE_KAMP_BK_VERPLAATS_KLASSE_INDIV: _verwerk_mutatie_kamp_bk_verplaats_deelnemer_naar_andere_klasse,
        MUTATIE_KAMP_BK_TEAMS_NUMMEREN: _verwerk_mutatie_bk_teams_opnieuw_nummeren,
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
