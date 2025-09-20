# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.models import F
from Competitie.definities import (DEELNAME_JA, DEELNAME_NEE,
                                   MUTATIE_KAMP_REINIT_TEST, MUTATIE_KAMP_CUT,
                                   MUTATIE_KAMP_AANMELDEN_INDIV, MUTATIE_KAMP_AFMELDEN_INDIV,
                                   MUTATIE_EXTRA_RK_DEELNEMER, MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV,
                                   MUTATIE_KAMP_TEAMS_NUMMEREN,
                                   MUTATIE_MAAK_WEDSTRIJDFORMULIEREN, MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN)
from Competitie.models import (Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam, CompetitieMatch,
                               KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet,
                               Competitie, CompetitieMutatie, CompetitieIndivKlasse, CompetitieTeamKlasse)
from CompKamp.operations.wedstrijdformulieren_indiv import (iter_indiv_wedstrijdformulieren,
                                                            UpdateIndivWedstrijdFormulier)
from CompKamp.operations.wedstrijdformulieren_teams import (iter_teams_wedstrijdformulieren,
                                                            UpdateTeamsWedstrijdFormulier)
from CompKamp.operations.storage_wedstrijdformulieren import (StorageWedstrijdformulieren, StorageError,
                                                              iter_dirty_wedstrijdformulieren, zet_dirty)
from GoogleDrive.operations.google_sheets import GoogleSheet
import time

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField
QUOTA_PER_MINUTE = 45           # standard limit is 60 per minute


class VerwerkCompKampMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompKamp applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger

    @staticmethod
    def _zet_dirty(comp: Competitie, klasse_pk: int, is_bk: bool, is_team: bool):
        zet_dirty(comp.begin_jaar, int(comp.afstand), klasse_pk, is_bk, is_team)

        CompetitieMutatie.objects.create(
                            mutatie=MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN,
                            competitie=comp)      # alleen nodig voor begin_jaar

    @staticmethod
    def _get_limiet_indiv(deelkamp, indiv_klasse):
        # bepaal de limiet
        try:
            limiet = (KampioenschapIndivKlasseLimiet
                      .objects
                      .get(kampioenschap=deelkamp,
                           indiv_klasse=indiv_klasse)
                      ).limiet
        except KampioenschapIndivKlasseLimiet.DoesNotExist:
            limiet = 24

        return limiet

    @staticmethod
    def _update_rank_nummers(deelkamp, klasse):
        rank = 0
        for obj in (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap=deelkamp,
                            indiv_klasse=klasse)
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

    def _verwerk_mutatie_initieel_klasse_indiv(self, deelkamp, indiv_klasse, zet_boven_cut_op_ja=False):
        # Bepaal de top-X deelnemers voor een klasse van een kampioenschap
        # De kampioenen aangevuld met de sporters met hoogste gemiddelde
        # gesorteerde op gemiddelde

        self.stdout.write('[INFO] Bepaal deelnemers in indiv_klasse %s van %s' % (indiv_klasse, deelkamp))

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp.competitie, indiv_klasse.pk, is_bk=deelkamp.is_bk(), is_team=False)

        limiet = self._get_limiet_indiv(deelkamp, indiv_klasse)

        # kampioenen hebben deelnamegarantie
        kampioenen = (KampioenschapSporterBoog
                      .objects
                      .exclude(kampioen_label='')
                      .filter(kampioenschap=deelkamp,
                              indiv_klasse=indiv_klasse))

        lijst = list()
        aantal = 0
        for obj in kampioenen:
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
        # for

        # aanvullen met sporters tot aan de cut
        objs = (KampioenschapSporterBoog
                .objects
                .filter(kampioenschap=deelkamp,
                        indiv_klasse=indiv_klasse,
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

    def verwerk_mutatie_initieel_deelkamp(self, deelkamp, zet_boven_cut_op_ja=False):
        # let op: deze wordt ook aangeroepen vanuit VerwerkCompLaagRayonMutaties

        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven sporters
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=deelkamp)
                          .distinct('indiv_klasse')):

            # sorteer de lijst op gemiddelde en bepaalde volgorde
            self._verwerk_mutatie_initieel_klasse_indiv(deelkamp, deelnemer.indiv_klasse, zet_boven_cut_op_ja)
        # for

    def _verwerk_mutatie_kamp_reinit_test(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: kamp (re-)init test' % mutatie.pk)
        competitie = mutatie.kampioenschap.competitie
        deel = mutatie.kampioenschap.deel

        # bepaal de volgorde en rank van de deelnemers
        # in alle klassen van de RK of BK deelcompetities

        # Let op: wordt alleen gebruik vanuit test code

        for deelkamp in (Kampioenschap
                         .objects
                         .filter(competitie=competitie,
                                 deel=deel)):
            self.verwerk_mutatie_initieel_deelkamp(deelkamp)
        # for

    def _opnieuw_aanmelden_indiv(self, deelnemer):
        # meld de deelnemer opnieuw aan door hem bij de reserves te zetten

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        # sporter wordt van zijn oude 'volgorde' weggehaald
        # iedereen schuift een plekje op
        # daarna wordt de sporter op de juiste plaats ingevoegd
        # en iedereen met een lager gemiddelde schuift weer een plekje op

        deelkamp = deelnemer.kampioenschap
        indiv_klasse = deelnemer.indiv_klasse
        oude_volgorde = deelnemer.volgorde

        self.stdout.write('[INFO] Opnieuw aanmelden vanuit oude volgorde=%s: %s' % (oude_volgorde,
                                                                                    deelnemer.sporterboog))

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp.competitie, indiv_klasse.pk, deelkamp.is_bk(), is_team=False)

        # verwijder de deelnemer uit de lijst op zijn oude plekje
        # en schuif de rest omhoog
        deelnemer.volgorde = VOLGORDE_PARKEER
        deelnemer.save(update_fields=['volgorde'])

        qset = (KampioenschapSporterBoog
                .objects
                .filter(kampioenschap=deelkamp,
                        indiv_klasse=indiv_klasse,
                        volgorde__gt=oude_volgorde,
                        volgorde__lt=VOLGORDE_PARKEER))
        qset.update(volgorde=F('volgorde') - 1)

        limiet = self._get_limiet_indiv(deelkamp, indiv_klasse)

        # als er minder dan limiet deelnemers zijn, dan invoegen op gemiddelde
        # als er een reserve lijst is, dan invoegen in de reserve-lijst op gemiddelde
        # altijd invoegen NA sporters met gelijkwaarde gemiddelde

        deelnemers_count = (KampioenschapSporterBoog
                            .objects
                            .exclude(deelname=DEELNAME_NEE)
                            .filter(kampioenschap=deelkamp,
                                    indiv_klasse=indiv_klasse,
                                    rank__lte=limiet,
                                    volgorde__lt=VOLGORDE_PARKEER).count())

        if deelnemers_count >= limiet:
            # er zijn genoeg sporters, dus deze her-aanmelding moet op de reserve-lijst
            self.stdout.write('[INFO] Naar de reserve-lijst')
            deelnemer.logboek += '[%s] Naar de reserve-lijst\n' % stamp_str

            # zoek een plekje in de reserve-lijst
            objs = (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap=deelkamp,
                            indiv_klasse=indiv_klasse,
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
            objs = (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap=deelkamp,
                            indiv_klasse=indiv_klasse,
                            rank__gte=nieuwe_rank))

            if len(objs) > 0:
                obj = objs.order_by('volgorde')[0]
                nieuwe_volgorde = obj.volgorde
            else:
                # niemand om op te schuiven - zet aan het einde
                nieuwe_volgorde = (KampioenschapSporterBoog
                                   .objects
                                   .exclude(volgorde=VOLGORDE_PARKEER)
                                   .filter(kampioenschap=deelkamp,
                                           indiv_klasse=indiv_klasse)
                                   .count()) + 1
        else:
            self.stdout.write('[INFO] Naar deelnemers-lijst')
            deelnemer.logboek += '[%s] Direct naar de deelnemerslijst\n' % stamp_str

            # er is geen reserve-lijst in deze klasse
            # de sporter gaat dus meteen de deelnemers lijst in
            objs = (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap=deelkamp,
                            indiv_klasse=indiv_klasse,
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

        objs = (KampioenschapSporterBoog
                .objects
                .filter(kampioenschap=deelkamp,
                        indiv_klasse=indiv_klasse,
                        volgorde__gte=nieuwe_volgorde))
        objs.update(volgorde=F('volgorde') + 1)

        deelnemer.volgorde = nieuwe_volgorde
        deelnemer.deelname = DEELNAME_JA
        deelnemer.logboek += '[%s] Deelname op Ja gezet\n' % stamp_str
        deelnemer.save(update_fields=['volgorde', 'deelname', 'logboek'])

        # deel de rank nummers opnieuw uit
        self._update_rank_nummers(deelkamp, indiv_klasse)

    def _verwerk_mutatie_kamp_aanmelden_indiv(self, mutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden' % mutatie.pk)
        door = mutatie.door
        deelnemer = mutatie.deelnemer

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

    def _verwerk_mutatie_kamp_afmelden_indiv(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: afmelden' % mutatie.pk)
        door = mutatie.door
        deelnemer = mutatie.deelnemer

        # de deelnemer is al afgemeld en behoudt zijn 'volgorde' zodat de RKO/BKO
        # 'm in grijs kan zien in de tabel

        # bij een mutatie "boven de cut" wordt de 1e reserve tot deelnemer gepromoveerd.
        # hiervoor wordt zijn 'volgorde' aangepast en schuift iedereen met een lager gemiddelde een plekje omlaag

        # daarna wordt de 'rank' aan voor alle sporters in deze klasse opnieuw vastgesteld

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = '[%s] Deelname op Nee gezet want afmelding ontvangen van  %s\n' % (stamp_str, door)

        deelnemer.deelname = DEELNAME_NEE
        deelnemer.logboek += msg
        deelnemer.save(update_fields=['deelname', 'logboek'])
        self.stdout.write('[INFO] Afmelding voor (rank=%s, volgorde=%s): %s' % (
                            deelnemer.rank, deelnemer.volgorde, deelnemer.sporterboog))

        deelkamp = deelnemer.kampioenschap
        indiv_klasse = deelnemer.indiv_klasse

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp.competitie, indiv_klasse.pk, deelkamp.is_bk(), is_team=False)

        limiet = self._get_limiet_indiv(deelkamp, indiv_klasse)

        # haal de 1e reserve op
        try:
            reserve = (KampioenschapSporterBoog
                       .objects
                       .get(kampioenschap=deelkamp,
                            indiv_klasse=indiv_klasse,
                            rank=limiet+1))                 # TODO: dit faalde een keer met 2 resultaten!
        except KampioenschapSporterBoog.DoesNotExist:
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
                slechter = (KampioenschapSporterBoog
                            .objects
                            .filter(kampioenschap=deelkamp,
                                    indiv_klasse=indiv_klasse,
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

    @staticmethod
    def _verwerk_mutatie_kamp_indiv_verhoog_cut(deelkamp, klasse, cut_nieuw):
        # de deelnemerslijst opnieuw sorteren op gemiddelde
        # dit is nodig omdat kampioenen naar boven geplaatst kunnen zijn bij het verlagen van de cut
        # nu plaatsen we ze weer terug op hun originele plek
        lijst = list()
        for obj in (KampioenschapSporterBoog
                    .objects
                    .filter(kampioenschap=deelkamp,
                            indiv_klasse=klasse,
                            rank__lte=cut_nieuw)):
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
    def _verwerk_mutatie_kamp_indiv_verlaag_cut(deelkamp, indiv_klasse, cut_oud, cut_nieuw):
        # zoek de kampioenen die al deel mochten nemen (dus niet op reserve lijst)
        kampioenen = (KampioenschapSporterBoog
                      .objects
                      .exclude(kampioen_label='')
                      .filter(kampioenschap=deelkamp,
                              indiv_klasse=indiv_klasse,
                              rank__lte=cut_oud))  # begrens tot deelnemerslijst

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
        objs = (KampioenschapSporterBoog
                .objects
                .filter(kampioenschap=deelkamp,
                        indiv_klasse=indiv_klasse,
                        kampioen_label='',          # kampioenen hebben we al gedaan
                        rank__lte=cut_oud)
                .order_by('-gemiddelde',            # hoogste boven
                          '-gemiddelde_scores'))    # hoogste boven (bij gelijk gemiddelde)

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

    def _verwerk_mutatie_kamp_cut_indiv(self, deelkamp: Kampioenschap, indiv_klasse: CompetitieIndivKlasse,
                                        cut_oud: int, cut_nieuw: int):
        try:
            is_nieuw = False
            limiet = (KampioenschapIndivKlasseLimiet
                      .objects
                      .get(kampioenschap=deelkamp,
                           indiv_klasse=indiv_klasse))
        except KampioenschapIndivKlasseLimiet.DoesNotExist:
            # maak een nieuwe aan
            is_nieuw = True
            limiet = KampioenschapIndivKlasseLimiet(kampioenschap=deelkamp,
                                                    indiv_klasse=indiv_klasse)

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
            self._verwerk_mutatie_kamp_indiv_verhoog_cut(deelkamp, indiv_klasse, cut_nieuw)

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelkamp.competitie, indiv_klasse.pk, deelkamp.is_bk(), is_team=False)

        elif cut_nieuw < cut_oud:
            # limiet is omlaag gezet
            # zorg dat de regiokampioenen er niet af vallen
            limiet.limiet = cut_nieuw
            limiet.save()

            self._verwerk_mutatie_kamp_indiv_verlaag_cut(deelkamp, indiv_klasse, cut_oud, cut_nieuw)

            # zorg dat het google sheet bijgewerkt worden
            self._zet_dirty(deelkamp.competitie, indiv_klasse.pk, deelkamp.is_bk(), is_team=False)

        # else: cut_oud == cut_nieuw --> doe niets
        #   (dit kan voorkomen als 2 gebruikers tegelijkertijd de cut veranderen)

    @staticmethod
    def _verwerk_mutatie_kamp_cut_team(deelkamp: Kampioenschap, team_klasse: CompetitieTeamKlasse,
                                       cut_oud: int, cut_nieuw: int):
        try:
            is_nieuw = False
            limiet = (KampioenschapTeamKlasseLimiet
                      .objects
                      .get(kampioenschap=deelkamp,
                           team_klasse=team_klasse))
        except KampioenschapTeamKlasseLimiet.DoesNotExist:
            # maak een nieuwe aan
            is_nieuw = True
            limiet = KampioenschapTeamKlasseLimiet(kampioenschap=deelkamp,
                                                   team_klasse=team_klasse)

        if cut_nieuw > cut_oud:
            # limiet verhogen is simpel, want deelnemers blijven deelnemers
            if cut_nieuw == 24:
                # verwijder het limiet record
                if not is_nieuw:
                    limiet.delete()
            else:
                limiet.limiet = cut_nieuw
                limiet.save()

            # de team lijst opnieuw sorteren op gemiddelde
            # TODO: mutatie op team deelnemers lijst
            # self._verwerk_mutatie_verhoog_cut(deelcomp, team_klasse, cut_nieuw)

        elif cut_nieuw < cut_oud:
            # limiet is omlaag gezet
            # zorg dat de regiokampioenen er niet af vallen
            limiet.limiet = cut_nieuw
            limiet.save()

            # TODO: mutatie op team deelnemers lijst
            # self._verwerk_mutatie_verlaag_cut(deelcomp, team_klasse, cut_oud, cut_nieuw)

        # else: cut_oud == cut_nieuw --> doe niets
        #   (dit kan voorkomen als 2 gebruikers tegelijkertijd de cut veranderen)

    def _verwerk_mutatie_kamp_cut(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)
        if mutatie.indiv_klasse:
            self._verwerk_mutatie_kamp_cut_indiv(mutatie.kampioenschap, mutatie.indiv_klasse,
                                                 mutatie.cut_oud, mutatie.cut_nieuw)
        else:
            self._verwerk_mutatie_kamp_cut_team(mutatie.kampioenschap, mutatie.team_klasse,
                                                mutatie.cut_oud, mutatie.cut_nieuw)

    def _verwerk_mutatie_kamp_verplaats_deelnemer_naar_andere_klasse(self, mutatie: CompetitieMutatie):
        """ verplaats deelnemer (KampioenschapSporterBoog) van zijn huidige klasse
            naar de klasse indiv_klasse (CompetitieIndivKlasse)
            en pas daarbij de volgorde en rank aan
        """

        self.stdout.write('[INFO] Verwerk mutatie %s: kleine klassen indiv' % mutatie.pk)
        deelnemer = mutatie.deelnemer
        indiv_klasse = mutatie.indiv_klasse

        if deelnemer.indiv_klasse != indiv_klasse:
            self.stdout.write('[INFO] Verplaats deelnemer %s van kleine klasse %s naar klasse %s' % (
                                deelnemer, deelnemer.indiv_klasse, indiv_klasse))

            deelkamp = deelnemer.kampioenschap

            # zorg dat beide google sheets bijgewerkt worden
            self._zet_dirty(deelkamp.competitie, indiv_klasse.pk, deelkamp.is_bk(), is_team=False)
            self._zet_dirty(deelkamp.competitie, deelnemer.indiv_klasse.pk, deelkamp.is_bk(), is_team=False)

            deelnemer.indiv_klasse = indiv_klasse
            deelnemer.save(update_fields=['indiv_klasse'])

            # stel de deelnemerslijst van de nieuwe klasse opnieuw op
            self._verwerk_mutatie_initieel_klasse_indiv(deelkamp, deelnemer.indiv_klasse)

    def _verwerk_mutatie_teams_opnieuw_nummeren(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: teams opnieuw nummeren' % mutatie.pk)
        deelkamp = mutatie.kampioenschap
        team_klasse = mutatie.team_klasse

        self.stdout.write('[INFO] Teams opnieuw nummeren voor kampioenschap %s team klasse %s' % (deelkamp,
                                                                                                  team_klasse))

        # zorg dat het google sheet bijgewerkt worden
        self._zet_dirty(deelkamp.competitie, team_klasse.pk, deelkamp.is_bk(), is_team=True)

        # alleen de rank aanpassen
        rank = 0
        for team in (KampioenschapTeam
                     .objects
                     .filter(kampioenschap=deelkamp,
                             team_klasse=team_klasse)
                     .order_by('volgorde')):           # originele volgorde aanhouden

            if team.deelname == DEELNAME_NEE:
                team.rank = 0
            else:
                rank += 1
                team.rank = rank
            team.save(update_fields=['rank'])
        # for

    def _verwerk_mutatie_extra_rk_deelnemer(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: extra RK deelnemer' % mutatie.pk)
        deelnemer = mutatie.deelnemer

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

        except StorageError as err:
            self.stdout.write('[ERROR] StorageError: %s' % str(err))

    def _verwerk_mutatie_update_dirty_wedstrijdformulieren(self, mutatie):
        begin_jaar = mutatie.competitie.begin_jaar
        self.stdout.write('[INFO] Update dirty wedstrijdformulieren')
        sheet = None

        # note: Indoor en 25m1pijl hebben aparte klassen
        indiv_klasse_pk2match = dict()
        team_klasse_pk2match = dict()

        for match in (CompetitieMatch
                      .objects
                      .filter(competitie__begin_jaar=begin_jaar)
                      .prefetch_related('indiv_klassen',
                                        'team_klassen')
                      .select_related('vereniging',
                                      'locatie')):

            for klasse in match.indiv_klassen.all():
                indiv_klasse_pk2match[klasse.pk] = match
            # for
            for klasse in match.team_klassen.all():
                team_klasse_pk2match[klasse.pk] = match
            # for
        # for

        quota = QUOTA_PER_MINUTE
        start_time = time.time()
        for bestand in iter_dirty_wedstrijdformulieren(begin_jaar):
            self.stdout.write('[INFO] Update bestand pk=%s' % bestand.pk)

            if not sheet:
                sheet = GoogleSheet(self.stdout)
            sheet.selecteer_file(bestand.file_id)

            if bestand.is_teams:
                # teams
                match = team_klasse_pk2match[bestand.klasse_pk]
                updater = UpdateTeamsWedstrijdFormulier(self.stdout, sheet)
                res = updater.update_wedstrijdformulier(bestand, match)
            else:
                # individueel
                match = indiv_klasse_pk2match[bestand.klasse_pk]
                updater = UpdateIndivWedstrijdFormulier(self.stdout, sheet)
                res = updater.update_wedstrijdformulier(bestand, match)

            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            msg = '[%s] Bijgewerkt met resultaat %s\n' % (stamp_str, res)
            bestand.is_dirty = False
            bestand.log += msg
            bestand.save(update_fields=['is_dirty', 'log'])

            quota -= 1
            if quota == 0:
                # sleep until the next minute
                pause = time.time() - start_time        # difference between two floats
                if pause > 0:
                    self.stdout.write('[INFO] Pause for %.2f seconds due to quota' % pause)
                    time.sleep(pause)
                quota = QUOTA_PER_MINUTE
        # for

    HANDLERS = {
        MUTATIE_KAMP_REINIT_TEST: _verwerk_mutatie_kamp_reinit_test,
        MUTATIE_KAMP_CUT: _verwerk_mutatie_kamp_cut,
        MUTATIE_KAMP_AANMELDEN_INDIV: _verwerk_mutatie_kamp_aanmelden_indiv,
        MUTATIE_KAMP_AFMELDEN_INDIV: _verwerk_mutatie_kamp_afmelden_indiv,
        MUTATIE_EXTRA_RK_DEELNEMER: _verwerk_mutatie_extra_rk_deelnemer,
        MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV: _verwerk_mutatie_kamp_verplaats_deelnemer_naar_andere_klasse,
        MUTATIE_KAMP_TEAMS_NUMMEREN: _verwerk_mutatie_teams_opnieuw_nummeren,
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


# end of file
