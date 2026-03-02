# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.models import F, ObjectDoesNotExist
from Competitie.definities import (DEELNAME_JA, DEELNAME_NEE,
                                   MUTATIE_KAMP_RK_REINIT_TEST, MUTATIE_KAMP_CUT,
                                   MUTATIE_KAMP_AANMELDEN_RK_INDIV, MUTATIE_KAMP_AFMELDEN_RK_INDIV,
                                   MUTATIE_KAMP_AANMELDEN_BK_INDIV, MUTATIE_KAMP_AFMELDEN_BK_INDIV,
                                   MUTATIE_EXTRA_RK_DEELNEMER, MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV,
                                   MUTATIE_KAMP_RK_TEAMS_NUMMEREN, MUTATIE_KAMP_BK_TEAMS_NUMMEREN,
                                   MUTATIE_MAAK_WEDSTRIJDFORMULIEREN, MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN)
from Competitie.models import Competitie, CompetitieMatch, CompetitieMutatie, CompetitieIndivKlasse
from CompKampioenschap.operations import maak_mutatie_update_dirty_wedstrijdformulieren
from CompKampioenschap.operations import iter_indiv_wedstrijdformulieren, iter_teams_wedstrijdformulieren
from CompKampioenschap.operations.wedstrijdformulieren_indiv_update import UpdateIndivWedstrijdFormulier
from CompKampioenschap.operations.wedstrijdformulieren_teams import UpdateTeamsWedstrijdFormulier
from CompKampioenschap.operations.storage_wedstrijdformulieren import (StorageWedstrijdformulieren,
                                                                       iter_dirty_wedstrijdformulieren, zet_dirty)
from CompKampioenschap.operations.monitor_wedstrijdformulieren import MonitorGoogleSheetsWedstrijdformulieren
from CompLaagBond.models import KampBK, DeelnemerBK, TeamBK, CutBK
from CompLaagRayon.models import KampRK, DeelnemerRK, TeamRK, CutRK
from GoogleDrive.operations import StorageGoogleSheet, StorageError
import time

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField


class VerwerkCompKampMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompKampioenschap applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger
        self._achtergrond_monitor = None

    @staticmethod
    def _zet_dirty(deelkamp: KampRK | KampBK, klasse_pk: int, is_team: bool):
        comp = deelkamp.competitie

        if isinstance(deelkamp, KampBK):
            is_bk = True
            rayon_nr = 0
        else:
            is_bk = False
            rayon_nr = deelkamp.rayon.rayon_nr

        zet_dirty(comp.begin_jaar, int(comp.afstand), rayon_nr, klasse_pk, is_bk, is_team)

        maak_mutatie_update_dirty_wedstrijdformulieren(comp)

    @staticmethod
    def _get_limiet_indiv(deelkamp: KampRK | KampBK, indiv_klasse: CompetitieIndivKlasse):
        # haal de limiet uit de database, indien aanwezig
        if isinstance(deelkamp, KampRK):
            cut = CutRK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse).first()
        else:
            cut = CutBK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse).first()

        limiet = cut.limiet if cut else 24      # fallback = 24
        return limiet

    @staticmethod
    def _update_rank_nummers(deelkamp: KampRK | KampBK, klasse : CompetitieIndivKlasse):
        if isinstance(deelkamp, KampRK):
            qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp)
        else:
            qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp)

        rank = 0
        for obj in (qset_deelnemers
                    .filter(indiv_klasse=klasse)
                    .order_by('volgorde')):

            old_rank = obj.rank

            if obj.deelname == DEELNAME_NEE:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank

            if obj.rank != old_rank:
                obj.save(update_fields=['rank'])
        # for

    def _verwerk_mutatie_initieel_klasse_indiv(self,
                                               deelkamp: KampRK | KampBK,
                                               indiv_klasse: CompetitieIndivKlasse,
                                               zet_boven_cut_op_ja : bool = False):
        # Bepaal de top-X deelnemers voor een klasse van een kampioenschap
        # De kampioenen aangevuld met de sporters met hoogste gemiddelde
        # gesorteerde op gemiddelde

        self.stdout.write('[INFO] Bepaal deelnemers in indiv_klasse %s van %s' % (indiv_klasse, deelkamp))

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp, indiv_klasse.pk, is_team=False)

        limiet = self._get_limiet_indiv(deelkamp, indiv_klasse)

        if isinstance(deelkamp, KampRK):
            qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp)
        else:
            qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp)

        # kampioenen hebben deelnamegarantie
        kampioenen = (qset_deelnemers
                      .exclude(kampioen_label='')
                      .filter(indiv_klasse=indiv_klasse))

        lijst = list()
        aantal = 0
        for obj in kampioenen:
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
        # for

        # aanvullen met sporters tot aan de cut
        objs = (qset_deelnemers
                .filter(indiv_klasse=indiv_klasse,
                        kampioen_label='')          # kampioenen hebben we al gedaan
                .order_by('-gemiddelde',            # hoogste boven
                          '-gemiddelde_scores'))    # hoogste boven (gelijk gemiddelde)

        for obj in objs:
            tup = (obj.gemiddelde, len(lijst), obj)
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
                if zet_boven_cut_op_ja:
                    obj.deelname = DEELNAME_JA

            obj.save(update_fields=['rank', 'volgorde', 'deelname'])
            pks.append(obj.pk)
        # for

        # geef nu alle andere sporters (onder de cut) een nieuw volgnummer
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

    def verwerk_mutatie_initieel_deelkamp(self,
                                          deelkamp: KampRK | KampBK,
                                          zet_boven_cut_op_ja : bool = False):
        # let op: deze wordt ook aangeroepen vanuit VerwerkCompLaagRayonMutaties

        if isinstance(deelkamp, KampRK):
            qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp)
        else:
            qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp)

        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven sporters
        for deelnemer in (qset_deelnemers
                          .select_related('indiv_klasse')
                          .distinct('indiv_klasse')):

            # sorteer de lijst op gemiddelde en bepaalde volgorde
            self._verwerk_mutatie_initieel_klasse_indiv(deelkamp, deelnemer.indiv_klasse, zet_boven_cut_op_ja)
        # for

    def _verwerk_mutatie_kamp_rk_reinit_test(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: kamp rk (re-)init test' % mutatie.pk)
        competitie = mutatie.kamp_rk.competitie

        # bepaal de volgorde en rank van de deelnemers
        # in alle klassen van de RKs

        # Let op: wordt alleen gebruik vanuit test code

        for deelkamp in (KampRK
                         .objects
                         .filter(competitie=competitie)):
            self.verwerk_mutatie_initieel_deelkamp(deelkamp)
        # for

    def _opnieuw_aanmelden_indiv(self, deelnemer: DeelnemerRK | DeelnemerBK):
        # meld de deelnemer opnieuw aan door hem bij de reserves te zetten

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        # sporter wordt van zijn oude 'volgorde' weggehaald
        # iedereen schuift een plekje op
        # daarna wordt de sporter op de juiste plaats ingevoegd
        # en iedereen met een lager gemiddelde schuift weer een plekje op

        if isinstance(deelnemer, DeelnemerRK):
            deelnemer_qset = DeelnemerRK.objects.filter(kamp=deelnemer.kamp)
        else:
            deelnemer_qset = DeelnemerBK.objects.filter(kamp=deelnemer.kamp)

        indiv_klasse = deelnemer.indiv_klasse
        oude_volgorde = deelnemer.volgorde

        self.stdout.write('[INFO] Opnieuw aanmelden vanuit oude volgorde=%s: %s' % (oude_volgorde,
                                                                                    deelnemer.sporterboog))

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelnemer.kamp, indiv_klasse.pk, is_team=False)

        # verwijder de deelnemer uit de lijst op zijn oude plekje
        # en schuif de rest omhoog
        deelnemer.volgorde = VOLGORDE_PARKEER
        deelnemer.save(update_fields=['volgorde'])

        qset = (deelnemer_qset
                .filter(indiv_klasse=indiv_klasse,
                        volgorde__gt=oude_volgorde,
                        volgorde__lt=VOLGORDE_PARKEER))
        qset.update(volgorde=F('volgorde') - 1)

        limiet = self._get_limiet_indiv(deelnemer.kamp, indiv_klasse)

        # als er minder dan limiet deelnemers zijn, dan invoegen op gemiddelde
        # als er een reserve lijst is, dan invoegen in de reserve-lijst op gemiddelde
        # altijd invoegen NA sporters met gelijkwaarde gemiddelde

        deelnemers_count = (deelnemer_qset
                            .exclude(deelname=DEELNAME_NEE)
                            .filter(indiv_klasse=indiv_klasse,
                                    rank__lte=limiet,
                                    volgorde__lt=VOLGORDE_PARKEER).count())

        if deelnemers_count >= limiet:
            # er zijn genoeg sporters, dus deze her-aanmelding moet op de reserve-lijst
            self.stdout.write('[INFO] Naar de reserve-lijst')
            deelnemer.logboek += '[%s] Naar de reserve-lijst\n' % stamp_str

            # zoek een plekje in de reserve-lijst
            objs = (deelnemer_qset
                    .filter(indiv_klasse=indiv_klasse,
                            rank__gt=limiet,
                            gemiddelde__gte=deelnemer.gemiddelde)
                    .order_by('gemiddelde',
                              'gemiddelde_scores'))

            if len(objs):
                # invoegen na de reserve-sporter met gelijk of hoger gemiddelde
                self.stdout.write('[INFO] Gemiddelde=%s, limiet=%s; 1e reserve heeft rank=%s, volgorde=%s' % (
                                    deelnemer.gemiddelde, limiet, objs[0].rank, objs[0].volgorde))
                nieuwe_rank = objs[0].rank + 1
            else:
                # er zijn geen reserve-sporters met gelijk of hoger gemiddelde
                # dus deze sporter mag boven aan de reserve-lijst
                self.stdout.write('[INFO] Maak 1e reserve')
                nieuwe_rank = limiet + 1

            # maak een plekje in de lijst door andere sporters op te schuiven
            objs = (deelnemer_qset
                    .filter(indiv_klasse=indiv_klasse,
                            rank__gte=nieuwe_rank))

            if len(objs) > 0:
                obj = objs.order_by('volgorde')[0]
                nieuwe_volgorde = obj.volgorde
            else:
                # niemand om op te schuiven - zet aan het einde
                nieuwe_volgorde = (deelnemer_qset
                                   .exclude(volgorde=VOLGORDE_PARKEER)
                                   .filter(indiv_klasse=indiv_klasse)
                                   .count()) + 1
        else:
            self.stdout.write('[INFO] Naar deelnemers-lijst')
            deelnemer.logboek += '[%s] Direct naar de deelnemerslijst\n' % stamp_str

            # er is geen reserve-lijst in deze klasse
            # de sporter gaat dus meteen de deelnemers lijst in
            objs = (deelnemer_qset
                    .filter(indiv_klasse=indiv_klasse,
                            gemiddelde__gte=deelnemer.gemiddelde,
                            volgorde__lt=VOLGORDE_PARKEER)
                    .order_by('gemiddelde',
                              'gemiddelde_scores'))

            if len(objs) > 0:
                # voeg de sporter in na de laatste deelnemer
                nieuwe_volgorde = objs[0].volgorde + 1
            else:
                # geen betere sporter gevonden
                # zet deze deelnemer boven aan de lijst
                nieuwe_volgorde = 1

        self.stdout.write('[INFO] Nieuwe volgorde=%s' % nieuwe_volgorde)

        objs = (deelnemer_qset
                .filter(indiv_klasse=indiv_klasse,
                        volgorde__gte=nieuwe_volgorde))
        objs.update(volgorde=F('volgorde') + 1)

        deelnemer.volgorde = nieuwe_volgorde
        deelnemer.deelname = DEELNAME_JA
        deelnemer.logboek += '[%s] Deelname op Ja gezet\n' % stamp_str
        deelnemer.save(update_fields=['volgorde', 'deelname', 'logboek'])

        # deel de rank nummers opnieuw uit
        self._update_rank_nummers(deelnemer.kamp, indiv_klasse)

    def _verwerk_mutatie_kamp_aanmelden_indiv(self, door: str, deelnemer: DeelnemerRK | DeelnemerBK):
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        msg = '[%s] Mutatie door %s\n' % (stamp_str, door)
        deelnemer.logboek += msg
        deelnemer.save(update_fields=['logboek'])

        if deelnemer.deelname != DEELNAME_JA:
            if deelnemer.deelname == DEELNAME_NEE:
                # Nee naar Ja
                self._opnieuw_aanmelden_indiv(deelnemer)
            else:
                # Ja of Onbekend naar Ja
                deelnemer.deelname = DEELNAME_JA
                deelnemer.logboek += '[%s] Deelname op Ja gezet\n' % stamp_str
                deelnemer.save(update_fields=['deelname', 'logboek'])
                # verder hoeven we niets te doen: volgorde en rank blijft hetzelfde

                # zorg dat het google sheet bijgewerkt worden
                self._zet_dirty(deelnemer.kamp, deelnemer.indiv_klasse.pk, is_team=False)

    def _verwerk_mutatie_kamp_aanmelden_rk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden RK' % mutatie.pk)
        self._verwerk_mutatie_kamp_aanmelden_indiv(mutatie.door, mutatie.deelnemer_rk)

    def _verwerk_mutatie_kamp_aanmelden_bk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden BK' % mutatie.pk)
        self._verwerk_mutatie_kamp_aanmelden_indiv(mutatie.door, mutatie.deelnemer_bk)

    def _verwerk_mutatie_kamp_afmelden_indiv(self, door: str, deelnemer: DeelnemerRK | DeelnemerBK):
        # de deelnemer is al afgemeld en behoudt zijn 'volgorde' zodat de RKO/BKO
        # 'm in grijs kan zien in de tabel

        # bij een mutatie "boven de cut" wordt de 1e reserve tot deelnemer gepromoveerd.
        # hiervoor wordt zijn 'volgorde' aangepast en schuift iedereen met een lager gemiddelde een plekje omlaag

        # daarna wordt de 'rank' aan voor alle sporters in deze klasse opnieuw vastgesteld

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        msg = '[%s] Mutatie door %s\n' % (stamp_str, door)
        deelnemer.logboek += msg

        msg = '[%s] Deelname op Nee gezet\n' % stamp_str
        deelnemer.deelname = DEELNAME_NEE
        deelnemer.logboek += msg
        deelnemer.save(update_fields=['deelname', 'logboek'])
        self.stdout.write('[INFO] Afmelding voor (rank=%s, volgorde=%s): %s' % (
                            deelnemer.rank, deelnemer.volgorde, deelnemer.sporterboog))

        deelkamp = deelnemer.kamp
        if isinstance(deelkamp, KampRK):
            qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelnemer.kamp)
        else:
            qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelnemer.kamp)

        indiv_klasse = deelnemer.indiv_klasse

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelnemer.kamp, indiv_klasse.pk, is_team=False)

        limiet = self._get_limiet_indiv(deelnemer.kamp, indiv_klasse)

        # haal de 1e reserve op
        try:
            reserve = (qset_deelnemers
                       .get(indiv_klasse=indiv_klasse,
                            rank=limiet+1))                 # TODO: dit faalde een keer met 2 resultaten!
        except ObjectDoesNotExist:
            # zoveel sporters zijn er niet (meer)
            pass
        else:
            if reserve.volgorde > deelnemer.volgorde:
                # de afgemelde deelnemer zat binnen de cut
                # maar de 1e reserve nu deelnemer

                self.stdout.write('[INFO] Reserve (rank=%s, volgorde=%s) wordt deelnemer: %s' % (
                                    reserve.rank, reserve.volgorde, reserve.sporterboog))

                # het kan zijn dat de 1e reserve een flinke sprong gaat maken in de lijst
                # het kan zijn dat de 1e reserve op zijn plekje blijft staan

                # bepaal het nieuwe plekje op de deelnemers-lijst
                # rank = 1..limiet-1
                slechter = (qset_deelnemers
                            .filter(indiv_klasse=indiv_klasse,
                                    gemiddelde__lt=reserve.gemiddelde,
                                    rank__lte=limiet,
                                    volgorde__lt=reserve.volgorde)
                            .order_by('volgorde'))      # 10, 11, 12, etc.

                if len(slechter) > 0:

                    # zet het nieuwe plekje
                    reserve.volgorde = slechter[0].volgorde
                    reserve.logboek += '[%s] Reserve wordt deelnemer\n' % stamp_str
                    reserve.save(update_fields=['volgorde', 'logboek'])

                    self.stdout.write('[INFO] Reserve krijgt nieuwe volgorde=%s' % reserve.volgorde)

                    self.stdout.write('[INFO] %s deelnemers krijgen volgorde+1' % len(slechter))

                    # schuif de andere sporters omlaag
                    slechter.update(volgorde=F('volgorde') + 1)

                # else: geen sporters om op te schuiven

        self._update_rank_nummers(deelkamp, indiv_klasse)

    def _verwerk_mutatie_kamp_afmelden_rk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: afmelden RK' % mutatie.pk)
        self._verwerk_mutatie_kamp_afmelden_indiv(mutatie.door, mutatie.deelnemer_rk)

    def _verwerk_mutatie_kamp_afmelden_bk_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: afmelden BK' % mutatie.pk)
        self._verwerk_mutatie_kamp_afmelden_indiv(mutatie.door, mutatie.deelnemer_bk)

    @staticmethod
    def _verwerk_mutatie_kamp_indiv_verhoog_cut(deelkamp: KampRK | KampBK,
                                                klasse: CompetitieIndivKlasse,
                                                cut_nieuw: int):
        # de deelnemerslijst opnieuw sorteren op gemiddelde
        # dit is nodig omdat kampioenen naar boven geplaatst kunnen zijn bij het verlagen van de cut
        # nu plaatsen we ze weer terug op hun originele plek

        if isinstance(deelkamp, KampRK):
            qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp, indiv_klasse=klasse)
        else:
            qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp, indiv_klasse=klasse)

        lijst = list()
        for obj in (qset_deelnemers
                    .filter(rank__lte=cut_nieuw)):
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
        # for

        # sorteer de deelnemers op gemiddelde (hoogste eerst)
        # bij gelijk gemiddelde: sorteer daarna op het volgnummer (hoogste eerst) in de lijst
        #                        want sorteren op obj gaat niet
        lijst.sort(reverse=True)

        # volgorde uitdelen voor deze kandidaat-deelnemers
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
        # for

    @staticmethod
    def _verwerk_mutatie_kamp_indiv_verlaag_cut(deelkamp: KampRK | KampBK,
                                                indiv_klasse: CompetitieIndivKlasse,
                                                cut_oud: int, cut_nieuw: int):
        # zoek de kampioenen die al deel mochten nemen (dus niet op reserve lijst)

        if isinstance(deelkamp, KampRK):
            qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse)
        else:
            qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse)

        kampioenen = (qset_deelnemers
                      .exclude(kampioen_label='')
                      .filter(rank__lte=cut_oud))  # begrens tot deelnemerslijst

        aantal = 0  # telt het aantal deelnemers
        lijst = list()
        lijst_pks = list()
        for obj in kampioenen:
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
            lijst_pks.append(obj.pk)
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
        # for

        # aanvullen met sporters tot aan de cut
        if isinstance(deelkamp, KampRK):
            objs = (qset_deelnemers
                    .filter(kampioen_label='',          # kampioenen hebben we al gedaan
                            rank__lte=cut_oud)
                    .order_by('-gemiddelde',            # hoogste boven
                              '-gemiddelde_scores'))    # hoogste boven (bij gelijk gemiddelde)
        else:
            objs = (qset_deelnemers
                    .filter(kampioen_label='',          # kampioenen hebben we al gedaan
                            rank__lte=cut_oud)
                    .order_by('-gemiddelde'))           # hoogste boven

        for obj in objs:
            if obj.pk not in lijst_pks and aantal < cut_nieuw:
                # voeg deze niet-kampioen toe aan de deelnemers lijst
                tup = (obj.gemiddelde, len(lijst), obj)
                lijst.append(tup)
                lijst_pks.append(obj.pk)
                if obj.deelname != DEELNAME_NEE:
                    aantal += 1
        # for

        # sorteer de deelnemers op gemiddelde (hoogste eerst)
        # bij gelijk gemiddelde: sorteer daarna op het volgnummer (hoogste eerst) in de lijst
        #                        want sorteren op obj gaat niet
        lijst.sort(reverse=True)

        # volgorde uitdelen voor deze kandidaat-deelnemers
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
        # for

        # geef nu alle andere sporters (tot de oude cut) opnieuw een volgnummer
        # dit is nodig omdat de kampioenen er tussenuit gehaald (kunnen) zijn
        # en we willen geen dubbele volgnummers
        for obj in objs:
            if obj.pk not in lijst_pks:
                volgorde += 1
                obj.volgorde = volgorde

                if obj.deelname == DEELNAME_NEE:
                    obj.rank = 0
                else:
                    rank += 1
                    obj.rank = rank
                obj.save(update_fields=['rank', 'volgorde'])
        # for

    def _verwerk_mutatie_kamp_cut(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)

        cut_oud = mutatie.cut_oud
        cut_nieuw = mutatie.cut_nieuw

        if mutatie.kamp_rk:
            limiet = CutRK.objects.filter(kamp=mutatie.kamp_rk, indiv_klasse=mutatie.indiv_klasse).first()
            deelkamp = mutatie.kamp_rk
        else:
            limiet = CutBK.objects.filter(kamp=mutatie.kamp_bk, indiv_klasse=mutatie.indiv_klasse).first()
            deelkamp = mutatie.kamp_bk

        if limiet:
            is_nieuw = False
        else:
            # maak een nieuwe aan
            is_nieuw = True
            if mutatie.kamp_rk:
                limiet = CutRK(kamp=mutatie.kamp_rk, indiv_klasse=mutatie.indiv_klasse)
            else:
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
            self._verwerk_mutatie_kamp_indiv_verhoog_cut(deelkamp, mutatie.indiv_klasse, cut_nieuw)

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelkamp, mutatie.indiv_klasse.pk, is_team=False)

        elif cut_nieuw < cut_oud:
            # limiet is omlaag gezet
            # zorg dat de regiokampioenen er niet af vallen
            limiet.limiet = cut_nieuw
            limiet.save()

            self._verwerk_mutatie_kamp_indiv_verlaag_cut(deelkamp, mutatie.indiv_klasse, cut_oud, cut_nieuw)

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelkamp, mutatie.indiv_klasse.pk, is_team=False)

        # else: cut_oud == cut_nieuw --> doe niets
        #   (dit kan voorkomen als 2 gebruikers tegelijkertijd de cut veranderen)

    def _verwerk_mutatie_kamp_verplaats_deelnemer_naar_andere_klasse(self, mutatie: CompetitieMutatie):
        """ verplaats deelnemer van zijn huidige klasse
            naar de klasse indiv_klasse (CompetitieIndivKlasse)
            en pas daarbij de volgorde en rank aan
        """

        self.stdout.write('[INFO] Verwerk mutatie %s: kleine klassen indiv' % mutatie.pk)
        deelnemer = mutatie.deelnemer
        indiv_klasse = mutatie.indiv_klasse

        if deelnemer.indiv_klasse != indiv_klasse:
            self.stdout.write('[INFO] Verplaats deelnemer %s van kleine klasse %s naar klasse %s' % (
                                deelnemer, deelnemer.indiv_klasse, indiv_klasse))

            deelkamp = deelnemer.kamp

            # zorg dat beide google sheets bijgewerkt worden
            self._zet_dirty(deelkamp, indiv_klasse.pk, is_team=False)
            self._zet_dirty(deelkamp, deelnemer.indiv_klasse.pk, is_team=False)

            deelnemer.indiv_klasse = indiv_klasse
            deelnemer.save(update_fields=['indiv_klasse'])

            # stel de deelnemerslijst van de nieuwe klasse opnieuw op
            self._verwerk_mutatie_initieel_klasse_indiv(deelkamp, deelnemer.indiv_klasse)

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

        for team in (TeamBK
                     .objects
                     .filter(kamp=deelkamp,
                             team_klasse=team_klasse)
                     .exclude(deelname=DEELNAME_JA)
                     .order_by('vereniging__regio__rayon_nr',    # rayon 1,2,3,4
                               '-aanvangsgemiddelde',            # hoogste eerst
                               'volgorde')):                     # originele volgorde aanhouden

            rank += 1
            if team.rank != rank:
                team.rank = rank
                team.save(update_fields=['rank'])
        # for

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp, team_klasse.pk, is_team=True)

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
                     .order_by('-aanvangsgemiddelde',       # hoogste eerst
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

    def _verwerk_mutatie_extra_rk_deelnemer(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: extra RK deelnemer' % mutatie.pk)
        deelnemer = mutatie.deelnemer_rk

        # gebruik de methode van opnieuw aanmelden om deze sporter op de reserve-lijst te krijgen
        self._opnieuw_aanmelden_indiv(deelnemer)

    def _verwerk_mutatie_maak_wedstrijdformulieren(self, mutatie):
        """ maak alle Google Sheet wedstrijdformulieren aan in de gedeelde Google Drive folders
            deze mutatie wordt opgestart zodra de toestemming binnen is.
        """
        comp = mutatie.competitie
        self.stdout.write('[INFO] Maak wedstrijdformulieren voor %s' % comp.beschrijving)

        try:
            storage = StorageWedstrijdformulieren(self.stdout, comp.begin_jaar, settings.GOOGLE_DRIVE_SHARE_WITH)
            storage.check_access()

            is_teams = False
            for afstand, is_bk, klasse_pk, rayon_nr, fname in iter_indiv_wedstrijdformulieren(comp):
                self.stdout.write('[INFO] Maak %s' % fname)
                storage.maak_sheet_van_template(afstand, is_teams, is_bk, klasse_pk, rayon_nr, fname)
            # for

            is_teams = True
            for afstand, is_bk, klasse_pk, rayon_nr, fname in iter_teams_wedstrijdformulieren(comp):
                self.stdout.write('[INFO] Maak %s' % fname)
                storage.maak_sheet_van_template(afstand, is_teams, is_bk, klasse_pk, rayon_nr, fname)
            # for

            # laat alle formulieren vullen
            maak_mutatie_update_dirty_wedstrijdformulieren(comp)

        except StorageError as err:
            msg = 'Onverwachte fout in verwerk_mutatie_maak_wedstrijdformulieren:\n'
            msg += '   %s\n' % str(err)
            self.stdout.write('[ERROR] {CompKampioenschap.verwerk_mutaties} ' + msg)

    def _verwerk_mutatie_update_dirty_wedstrijdformulieren(self, mutatie):
        begin_jaar = mutatie.competitie.begin_jaar
        self.stdout.write('[INFO] Update dirty wedstrijdformulieren')
        sheet = None

        # note: Indoor en 25m1pijl hebben aparte klassen, maar BK+elk RK hebben dezelfde klasse_pk, dus index nodig
        indiv_klasse_pk_index2match = dict[tuple[int, int], CompetitieMatch]()
        team_klasse_pk_index2match = dict[tuple[int, int], CompetitieMatch]()

        # doorloop alle wedstrijden
        for deelkamp in (KampRK
                         .objects
                         .filter(competitie__begin_jaar=begin_jaar)
                         .select_related('rayon')
                         .prefetch_related('matches')):

            index = deelkamp.rayon.rayon_nr

            for match in (deelkamp.matches
                          .prefetch_related('indiv_klassen',
                                            'team_klassen')
                          .select_related('vereniging',
                                          'locatie')):

                for klasse in match.indiv_klassen.all():
                    indiv_klasse_pk_index2match[(klasse.pk, index)] = match
                # for

                for klasse in match.team_klassen.all():
                    team_klasse_pk_index2match[(klasse.pk, index)] = match
                # for
        # for

        for deelkamp in (KampBK
                         .objects
                         .filter(competitie__begin_jaar=begin_jaar)
                         .prefetch_related('matches')):
            index = 0

            for match in (deelkamp.matches
                          .prefetch_related('indiv_klassen',
                                            'team_klassen')
                          .select_related('vereniging',
                                          'locatie')):

                for klasse in match.indiv_klassen.all():
                    indiv_klasse_pk_index2match[(klasse.pk, index)] = match
                # for

                for klasse in match.team_klassen.all():
                    team_klasse_pk_index2match[(klasse.pk, index)] = match
                # for
        # for

        for bestand in iter_dirty_wedstrijdformulieren(begin_jaar):
            self.stdout.write('[INFO] Update bestand pk=%s' % bestand.pk)

            # om te voorkomen dat we over de quota van 60 per minuut heen gaan
            # altijd 1 seconden vertragen
            time.sleep(1.0)

            if not sheet:
                sheet = StorageGoogleSheet(self.stdout)
            sheet.selecteer_file(bestand.file_id)

            if bestand.is_bk:
                index = 0
            else:
                index = bestand.rayon_nr

            res = ''
            if bestand.is_teams:
                # teams
                updater = UpdateTeamsWedstrijdFormulier(self.stdout, sheet)
                match = team_klasse_pk_index2match.get((bestand.klasse_pk, index), None)
            else:
                # individueel
                updater = UpdateIndivWedstrijdFormulier(self.stdout, sheet)
                match = indiv_klasse_pk_index2match.get((bestand.klasse_pk, index), None)

            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

            if match:
                res = updater.update_wedstrijdformulier(bestand, match)
                msg = '[%s] Bijgewerkt met resultaat %s\n' % (stamp_str, res)
            else:
                msg = '[%s] ERROR: kan CompetitieMatch niet vinden voor Bestand pk=%s\n' % (stamp_str, bestand.pk)

            bestand.is_dirty = False
            # newline toevoegen na handmatige edit in admin interface
            bestand.log = bestand.log.strip() + '\n'
            bestand.log += msg
            bestand.save(update_fields=['is_dirty', 'log'])
        # for

    HANDLERS = {
        MUTATIE_KAMP_RK_REINIT_TEST: _verwerk_mutatie_kamp_rk_reinit_test,
        MUTATIE_KAMP_CUT: _verwerk_mutatie_kamp_cut,
        MUTATIE_KAMP_AANMELDEN_RK_INDIV: _verwerk_mutatie_kamp_aanmelden_rk_indiv,
        MUTATIE_KAMP_AFMELDEN_RK_INDIV: _verwerk_mutatie_kamp_afmelden_rk_indiv,
        MUTATIE_KAMP_AANMELDEN_BK_INDIV: _verwerk_mutatie_kamp_aanmelden_bk_indiv,
        MUTATIE_KAMP_AFMELDEN_BK_INDIV: _verwerk_mutatie_kamp_afmelden_bk_indiv,
        MUTATIE_EXTRA_RK_DEELNEMER: _verwerk_mutatie_extra_rk_deelnemer,
        MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV: _verwerk_mutatie_kamp_verplaats_deelnemer_naar_andere_klasse,
        MUTATIE_KAMP_RK_TEAMS_NUMMEREN: _verwerk_mutatie_rk_teams_opnieuw_nummeren,
        MUTATIE_KAMP_BK_TEAMS_NUMMEREN: _verwerk_mutatie_bk_teams_opnieuw_nummeren,
        MUTATIE_MAAK_WEDSTRIJDFORMULIEREN: _verwerk_mutatie_maak_wedstrijdformulieren,
        MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN: _verwerk_mutatie_update_dirty_wedstrijdformulieren,
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
        if not self._achtergrond_monitor:
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

                if False:       # teams are Excel, for now
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

            self._achtergrond_monitor = MonitorGoogleSheetsWedstrijdformulieren(self.stdout, werk)

        self._achtergrond_monitor.doe_beetje_werk()


# end of file
