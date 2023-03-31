# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via CompetitieMutatie
"""

from django.conf import settings
from django.utils import timezone
from django.db.models import F
from django.db.utils import DataError, OperationalError, IntegrityError
from django.core.management.base import BaseCommand
from BasisTypen.definities import ORGANISATIE_NHB
from BasisTypen.operations import get_organisatie_teamtypen
from Competitie.definities import (DEEL_RK, DEEL_BK, DEELNAME_JA, DEELNAME_NEE, DEELNAME_ONBEKEND,
                                   MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M, MUTATIE_COMPETITIE_OPSTARTEN,
                                   MUTATIE_INITIEEL, MUTATIE_KAMP_CUT, MUTATIE_KAMP_AANMELDEN, MUTATIE_KAMP_AFMELDEN,
                                   MUTATIE_REGIO_TEAM_RONDE, MUTATIE_EXTRA_RK_DEELNEMER,
                                   MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                                   MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK, MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                                   MUTATIE_KLEINE_KLASSE_INDIV)
from Competitie.models import (CompetitieMutatie, Competitie, CompetitieIndivKlasse, CompetitieTaken,
                               Regiocompetitie, KampioenschapIndivKlasseLimiet, KampioenschapTeamKlasseLimiet,
                               RegiocompetitieSporterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from Competitie.operations import (competities_aanmaken, bepaal_startjaar_nieuwe_competitie,
                                   aanvangsgemiddelden_vaststellen_voor_afstand)
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_notify_internal_error
from Overig.background_sync import BackgroundSync
from Taken.operations import maak_taak
import traceback
import datetime
import logging
import sys

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField

my_logger = logging.getLogger('NHBApps.RegiocompMutaties')

# TODO: opsplitsen naar CompLaag*/operations/xxx


class Command(BaseCommand):
    help = "Competitie mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._boogtypen = list()        # [boog_type.pk, ..]
        self._team_boogtypen = dict()   # [team_type.pk] = [boog_type.pk, ..]
        self._team_volgorde = list()    # [team_type.pk, ..]

        self.stop_at = datetime.datetime.now()

        self.taken = CompetitieTaken.objects.all()[0]

        self.pk2scores = dict()         # [RegioCompetitieSporterBoog.pk] = [tup, ..] with tup = (afstand, score)
        self.pk2scores_alt = dict()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__REGIOCOMP_MUTATIES)
        self._count_ping = 0

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--all', action='store_true')       # alles opnieuw vaststellen
        parser.add_argument('--quick', action='store_true')     # for testing

    def _bepaal_boog2team(self):
        """ bepaalde boog typen mogen meedoen in bepaalde team types
            straks als we de team leden gaan verdelen over de teams moeten dat in een slimme volgorde
            zodat de sporters in toegestane teams en alle team typen gevuld worden.
            Voorbeeld: LB mag meedoen in LB, TR, BB en R teams terwijl C alleen in C team mag.
                       we moeten dus niet beginnen met de LB sporter in een R team te stoppen en daarna
                       geen sporters meer over hebben voor het LB team.
        """

        for team_type in get_organisatie_teamtypen(ORGANISATIE_NHB):

            self._team_boogtypen[team_type.pk] = boog_lijst = list()

            for boog_type in team_type.boog_typen.all():
                boog_lijst.append(boog_type.pk)

                if boog_type.pk not in self._boogtypen:
                    self._boogtypen.append(boog_type.pk)
            # for
        # for

        team_aantal = [(len(boog_typen), team_type_pk) for team_type_pk, boog_typen in self._team_boogtypen.items()]
        team_aantal.sort()
        self._team_volgorde = [team_type_pk for _, team_type_pk in team_aantal]

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

    def _verstuur_uitnodigingen(self):
        """ deze taak wordt bij elke start van dit commando uitgevoerd om e-mails te sturen naar de sporters
            (typisch 1x per uur)

            uitnodiging deelname RK + verzoek bevestigen / afmelden deelname
            herinnering bevestigen / afmelden deelname
        """
        # TODO: implementeren

    def _verwerk_mutatie_initieel_klasse_indiv(self, deelkamp, indiv_klasse):
        # Bepaal de top-X deelnemers voor een klasse van een kampioenschap
        # De kampioenen aangevuld met de sporters met hoogste gemiddelde
        # gesorteerde op gemiddelde

        self.stdout.write('[INFO] Bepaal deelnemers in indiv_klasse %s van %s' % (indiv_klasse, deelkamp))

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
            obj.save(update_fields=['rank', 'volgorde'])
            pks.append(obj.pk)
        # for

        # geef nu alle andere sporters een nieuw volgnummer
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

    def _verwerk_mutatie_initieel_deelkamp(self, deelkamp):
        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven sporters
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=deelkamp)
                          .distinct('indiv_klasse')):

            # sorteer de lijst op gemiddelde en bepaalde volgorde
            self._verwerk_mutatie_initieel_klasse_indiv(deelkamp, deelnemer.indiv_klasse)
        # for

    def _verwerk_mutatie_initieel(self, competitie, deel):
        # bepaal de volgorde en rank van de deelnemers
        # in alle klassen van de RK of BK deelcompetities

        # via deelnemer kunnen we bepalen over welke kampioenschappen dit gaat
        for deelkamp in (Kampioenschap
                         .objects
                         .filter(competitie=competitie,
                                 deel=deel)):
            self._verwerk_mutatie_initieel_deelkamp(deelkamp)
        # for

    def _verwerk_mutatie_afmelden_indiv(self, deelnemer):
        # de deelnemer is al afgemeld en behoudt zijn 'volgorde' zodat de RKO/BKO
        # 'm in grijs kan zien in de tabel

        # bij een mutatie "boven de cut" wordt de 1e reserve tot deelnemer gepromoveerd.
        # hiervoor wordt zijn 'volgorde' aangepast en schuift iedereen met een lager gemiddelde een plekje omlaag

        # daarna wordt de 'rank' aan voor alle sporters in deze klasse opnieuw vastgesteld

        deelnemer.deelname = DEELNAME_NEE
        deelnemer.save(update_fields=['deelname'])
        self.stdout.write('[INFO] Afmelding voor (rank=%s, volgorde=%s): %s' % (
                            deelnemer.rank, deelnemer.volgorde, deelnemer.sporterboog))

        deelkamp = deelnemer.kampioenschap
        indiv_klasse = deelnemer.indiv_klasse

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
                    reserve.save(update_fields=['volgorde'])

                    self.stdout.write('[INFO] Reserve krijgt nieuwe volgorde=%s' % reserve.volgorde)

                    self.stdout.write('[INFO] %s deelnemers krijgen volgorde+1' % len(slechter))

                    # schuif de andere sporters omlaag
                    slechter.update(volgorde=F('volgorde') + 1)

                # else: geen sporters om op te schuiven

        self._update_rank_nummers(deelkamp, indiv_klasse)

    def _opnieuw_aanmelden_indiv(self, deelnemer):
        # meld de deelnemer opnieuw aan door hem bij de reserves te zetten

        # sporter wordt van zijn oude 'volgorde' weggehaald
        # iedereen schuift een plekje op
        # daarna wordt de sporter op de juiste plaats ingevoegd
        # en iedereen met een lager gemiddelde schuift weer een plekje op

        deelkamp = deelnemer.kampioenschap
        indiv_klasse = deelnemer.indiv_klasse
        oude_volgorde = deelnemer.volgorde

        self.stdout.write('[INFO] Opnieuw aanmelden vanuit oude volgorde=%s: %s' % (oude_volgorde,
                                                                                    deelnemer.sporterboog))

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
                self.stdout.write('[INFO] Gemiddelde=%s, limiet=%s; 1e reserve heeft rank=%s, volgorde=%s' % (deelnemer.gemiddelde, limiet, objs[0].rank, objs[0].volgorde))
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
        deelnemer.save(update_fields=['volgorde', 'deelname'])

        # deel de rank nummers opnieuw uit
        self._update_rank_nummers(deelkamp, indiv_klasse)

    def _verwerk_mutatie_kamp_aanmelden(self, deelnemer):
        if deelnemer.deelname != DEELNAME_JA:
            if deelnemer.deelname == DEELNAME_NEE:
                self._opnieuw_aanmelden_indiv(deelnemer)
            else:
                deelnemer.deelname = DEELNAME_JA
                deelnemer.save(update_fields=['deelname'])
                # verder hoeven we niets te doen: volgorde en rank blijft hetzelfde

    @staticmethod
    def _verwerk_mutatie_kamp_verhoog_cut(deelkamp, klasse, cut_nieuw):
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
    def _verwerk_mutatie_kamp_verlaag_cut(deelkamp, indiv_klasse, cut_oud, cut_nieuw):
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

    def _verwerk_mutatie_kamp_cut_indiv(self, deelkamp, indiv_klasse, cut_oud, cut_nieuw):
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
            self._verwerk_mutatie_kamp_verhoog_cut(deelkamp, indiv_klasse, cut_nieuw)

        elif cut_nieuw < cut_oud:
            # limiet is omlaag gezet
            # zorg dat de regiokampioenen er niet af vallen
            limiet.limiet = cut_nieuw
            limiet.save()

            self._verwerk_mutatie_kamp_verlaag_cut(deelkamp, indiv_klasse, cut_oud, cut_nieuw)

        # else: cut_oud == cut_nieuw --> doe niets
        #   (dit kan voorkomen als 2 gebruikers tegelijkertijd de cut veranderen)

    @staticmethod
    def _verwerk_mutatie_kamp_cut_team(deelkamp, team_klasse, cut_oud, cut_nieuw):
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

    @staticmethod
    def _verwerk_mutatie_competitie_opstarten():
        jaar = bepaal_startjaar_nieuwe_competitie()
        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() == 0:
            competities_aanmaken(jaar)

    def _verwerk_mutatie_regio_team_ronde(self, deelcomp):
        # bepaal de volgende ronde
        if deelcomp.huidige_team_ronde > 7:
            # alle rondes al gehad - silently ignore
            return

        if deelcomp.huidige_team_ronde == 7:
            # afsluiten van de laatste ronde
            deelcomp.huidige_team_ronde = 99
            deelcomp.save(update_fields=['huidige_team_ronde'])
            return

        ronde_nr = deelcomp.huidige_team_ronde + 1

        if ronde_nr == 1:
            teams = (RegiocompetitieTeam
                     .objects
                     .filter(regiocompetitie=deelcomp))

            if teams.count() == 0:
                self.stdout.write('[WARNING] Team ronde doorzetten voor regio %s geweigerd want 0 teams' % deelcomp)
                return
        else:
            ronde_teams = (RegiocompetitieRondeTeam
                           .objects
                           .filter(team__regiocompetitie=deelcomp,
                                   ronde_nr=deelcomp.huidige_team_ronde))
            if ronde_teams.count() == 0:
                self.stdout.write('[WARNING] Team ronde doorzetten voor regio %s geweigerd want 0 ronde teams' % deelcomp)
                return

            aantal_scores = ronde_teams.filter(team_score__gt=0).count()
            if aantal_scores == 0:
                self.stdout.write('[WARNING] Team ronde doorzetten voor regio %s geweigerd want alle team_scores zijn 0' % deelcomp)
                return

        now = timezone.now()
        now = timezone.localtime(now)
        now_str = now.strftime("%Y-%m-%d %H:%M")

        ver_dict = dict()       # [ver_nr] = list(vsg, deelnemer_pk, boog_type_pk)

        # voor elke deelnemer het gemiddelde_begin_team_ronde invullen
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('bij_vereniging',
                                          'sporterboog',
                                          'sporterboog__boogtype')
                          .filter(regiocompetitie=deelcomp,
                                  inschrijf_voorkeur_team=True)):

            # bij vaste teams altijd het AG gebruiken (anders kan invaller op een gegeven moment niet meer invallen)
            if deelnemer.aantal_scores == 0 or deelcomp.regio_heeft_vaste_teams or ronde_nr == 1:
                vsg = deelnemer.ag_voor_team
            else:
                vsg = deelnemer.gemiddelde  # individuele voortschrijdend gemiddelde

            deelnemer.gemiddelde_begin_team_ronde = vsg
            deelnemer.save(update_fields=['gemiddelde_begin_team_ronde'])

            ver_nr = deelnemer.bij_vereniging.ver_nr
            tup = (-vsg, deelnemer.pk, deelnemer.sporterboog.boogtype.pk)
            try:
                ver_dict[ver_nr].append(tup)
            except KeyError:
                ver_dict[ver_nr] = [tup]
        # for

        for team_lid in ver_dict.values():
            team_lid.sort()
        # for

        # maak voor elk team een 'ronde instantie' aan waarin de invallers en score bijgehouden worden
        # verdeel ook de sporters volgens VSG
        for team_type_pk in self._team_volgorde:

            team_boogtypen = self._team_boogtypen[team_type_pk]

            for team in (RegiocompetitieTeam
                         .objects
                         .select_related('vereniging')
                         .prefetch_related('leden')
                         .filter(regiocompetitie=deelcomp,
                                 team_type__pk=team_type_pk)
                         .order_by('-aanvangsgemiddelde')):     # hoogste eerst

                ronde_team = RegiocompetitieRondeTeam(
                                team=team,
                                ronde_nr=ronde_nr,
                                logboek="[%s] Aangemaakt bij opstarten ronde %s\n" % (now_str, ronde_nr))
                ronde_team.save()

                # koppel de leden
                if deelcomp.regio_heeft_vaste_teams:
                    # vaste team begint elke keer met de vaste leden
                    sporter_pks = team.leden.values_list('pk', flat=True)
                else:
                    # voortschrijdend gemiddelde: pak de volgende 4 beste sporters van de vereniging
                    sporter_pks = list()
                    ver_nr = team.vereniging.ver_nr
                    ver_leden = ver_dict[ver_nr]
                    gebruikt = list()
                    for tup in ver_leden:
                        _, deelnemer_pk, boogtype_pk = tup
                        if boogtype_pk in team_boogtypen:
                            sporter_pks.append(deelnemer_pk)
                            gebruikt.append(tup)

                        if len(sporter_pks) == 4:
                            break
                    # for

                    for tup in gebruikt:
                        ver_leden.remove(tup)
                    # for

                ronde_team.deelnemers_geselecteerd.set(sporter_pks)
                ronde_team.deelnemers_feitelijk.set(sporter_pks)

                # schrijf de namen van de leden in het logboek
                ronde_team.logboek += '[%s] Geselecteerde leden:\n' % now_str
                for deelnemer in (RegiocompetitieSporterBoog
                                  .objects
                                  .select_related('sporterboog__sporter')
                                  .filter(pk__in=sporter_pks)):
                    ronde_team.logboek += '   ' + str(deelnemer.sporterboog.sporter) + '\n'
                # for
                ronde_team.save(update_fields=['logboek'])
            # for
        # for

        deelcomp.huidige_team_ronde = ronde_nr
        deelcomp.save(update_fields=['huidige_team_ronde'])

    @staticmethod
    def _eindstand_regio_indiv_naar_histcomp(comp):
        """ maak de HistComp aan vanuit een regiocompetitie eindstand """

        seizoen = "%s/%s" % (comp.begin_jaar, comp.begin_jaar + 1)
        try:
            objs = HistCompetitie.objects.filter(seizoen=seizoen,
                                                 comp_type=comp.afstand,
                                                 is_team=False)
        except HistCompetitieIndividueel.DoesNotExist:
            pass
        else:
            # er bestaat al een uitslag - verwijder deze eerst
            # dit verwijderd ook alle gekoppelde scores (individueel en team)
            # elk 'klasse' heeft een eigen instantie - typisch Recurve, Compound, etc.
            objs.delete()

        bulk = list()
        for boogtype in comp.boogtypen.all():
            histcomp = HistCompetitie(seizoen=seizoen,
                                      comp_type=comp.afstand,
                                      boog_str=boogtype.beschrijving,   # 'Recurve'
                                      is_team=False,
                                      is_openbaar=False)                # nog niet laten zien
            histcomp.save()

            klassen_pks = (CompetitieIndivKlasse
                           .objects
                           .filter(competitie=comp,
                                   boogtype=boogtype)
                           .values_list('pk', flat=True))

            deelnemers = (RegiocompetitieSporterBoog
                          .objects
                          .select_related('sporterboog__sporter',
                                          'bij_vereniging')
                          .filter(regiocompetitie__competitie=comp,
                                  indiv_klasse__in=klassen_pks)
                          .order_by('-gemiddelde'))     # hoogste boven

            rank = 0
            for deelnemer in deelnemers:
                # skip sporters met helemaal geen scores
                if deelnemer.totaal > 0:
                    rank += 1
                    sporter = deelnemer.sporterboog.sporter
                    ver = deelnemer.bij_vereniging
                    hist = HistCompetitieIndividueel(
                                histcompetitie=histcomp,
                                rank=rank,
                                sporter_lid_nr=sporter.lid_nr,
                                sporter_naam=sporter.volledige_naam(),
                                boogtype=boogtype.afkorting,
                                vereniging_nr=ver.ver_nr,
                                vereniging_naam=ver.naam,
                                score1=deelnemer.score1,
                                score2=deelnemer.score2,
                                score3=deelnemer.score3,
                                score4=deelnemer.score4,
                                score5=deelnemer.score5,
                                score6=deelnemer.score6,
                                score7=deelnemer.score7,
                                laagste_score_nr=deelnemer.laagste_score_nr,
                                totaal=deelnemer.totaal,
                                gemiddelde=deelnemer.gemiddelde)

                    bulk.append(hist)
                    if len(bulk) >= 500:
                        HistCompetitieIndividueel.objects.bulk_create(bulk)
                        bulk = list()
            # for

        # for

        if len(bulk):
            HistCompetitieIndividueel.objects.bulk_create(bulk)

    @staticmethod
    def _get_regio_sporters_rayon(competitie, rayon_nr):
        """ geeft een lijst met deelnemers terug
            en een totaal-status van de onderliggende regiocompetities: alles afgesloten?
        """

        # sporter komen uit de 4 regio's van het rayon
        pks = list()
        for deelcomp in (Regiocompetitie
                         .objects
                         .filter(competitie=competitie,
                                 nhb_regio__rayon__rayon_nr=rayon_nr)):
            pks.append(deelcomp.pk)
        # for

        # TODO: sorteren en kampioenen eerst zetten kan allemaal weg
        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('indiv_klasse',
                                      'bij_vereniging__regio',
                                      'sporterboog__sporter',
                                      'sporterboog__sporter__bij_vereniging',
                                      'sporterboog__sporter__bij_vereniging__regio__rayon')
                      .filter(regiocompetitie__in=pks,
                              aantal_scores__gte=competitie.aantal_scores_voor_rk_deelname,
                              indiv_klasse__is_ook_voor_rk_bk=True)     # skip aspiranten
                      .order_by('indiv_klasse__volgorde',               # groepeer per klasse
                                '-gemiddelde'))                         # aflopend gemiddelde

        # markeer de regiokampioenen
        klasse = -1
        regios = list()     # bijhouden welke kampioenen we al gemarkeerd hebben
        kampioenen = list()
        deelnemers = list(deelnemers)
        nr = 0
        insert_at = 0
        rank = 0
        while nr < len(deelnemers):
            deelnemer = deelnemers[nr]

            if klasse != deelnemer.indiv_klasse.volgorde:
                klasse = deelnemer.indiv_klasse.volgorde
                if len(kampioenen):
                    kampioenen.sort()
                    for _, kampioen in kampioenen:
                        deelnemers.insert(insert_at, kampioen)
                        insert_at += 1
                        nr += 1
                    # for
                kampioenen = list()
                regios = list()
                insert_at = nr
                rank = 0

            # fake een paar velden uit KampioenschapSchutterBoog
            rank += 1
            deelnemer.volgorde = rank
            deelnemer.deelname = DEELNAME_ONBEKEND

            scores = [deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4,
                      deelnemer.score5, deelnemer.score6, deelnemer.score7]
            scores.sort(reverse=True)      # beste score eerst
            deelnemer.regio_scores = "%03d%03d%03d%03d%03d%03d%03d" % tuple(scores)

            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            if regio_nr not in regios:
                regios.append(regio_nr)
                deelnemer.kampioen_label = "Kampioen regio %s" % regio_nr
                tup = (regio_nr, deelnemer)
                kampioenen.append(tup)
                deelnemers.pop(nr)
            else:
                # alle sporters overnemen als potentiële reserve-sporter
                deelnemer.kampioen_label = ""
                nr += 1
        # while

        if len(kampioenen):
            kampioenen.sort(reverse=True)       # hoogste regionummer bovenaan
            for _, kampioen in kampioenen:
                deelnemers.insert(insert_at, kampioen)
                insert_at += 1
            # for

        return deelnemers

    def _maak_deelnemerslijst_rks(self, comp):
        """ stel de deelnemerslijsten voor de kampioenschappen op aan de hand van gerechtigde deelnemers uit de regiocompetitie.
            ook wordt hier de vereniging van de sporter bevroren.
        """

        # sporters moeten in het rayon van hun huidige vereniging geplaatst worden
        rayon_nr2deelkamp = dict()
        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('nhb_rayon')
                         .filter(competitie=comp,
                                 deel=DEEL_RK)):
            rayon_nr2deelkamp[deelkamp.nhb_rayon.rayon_nr] = deelkamp
        # for

        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('nhb_rayon')
                         .filter(competitie=comp,
                                 deel=DEEL_RK)):

            deelnemers = self._get_regio_sporters_rayon(comp, deelkamp.nhb_rayon.rayon_nr)

            # schrijf all deze sporters in voor het RK
            # kampioenen als eerste in de lijst, daarna aflopend gesorteerd op gemiddelde
            bulk_lijst = list()
            for deelnemer in deelnemers:

                # sporter moet nu lid zijn bij een vereniging
                ver = deelnemer.sporterboog.sporter.bij_vereniging
                if ver:
                    # schrijf de sporter in het juiste rayon in
                    deelkamp = rayon_nr2deelkamp[ver.regio.rayon.rayon_nr]

                    kampioen = KampioenschapSporterBoog(
                                    kampioenschap=deelkamp,
                                    sporterboog=deelnemer.sporterboog,
                                    indiv_klasse=deelnemer.indiv_klasse,
                                    bij_vereniging=ver,             # bevries vereniging
                                    kampioen_label=deelnemer.kampioen_label,
                                    gemiddelde=deelnemer.gemiddelde,
                                    gemiddelde_scores=deelnemer.regio_scores)

                    if not deelnemer.inschrijf_voorkeur_rk_bk:
                        # bij inschrijven al afgemeld voor RK/BK
                        kampioen.deelname = DEELNAME_NEE

                    bulk_lijst.append(kampioen)
                    if len(bulk_lijst) > 150:       # pragma: no cover
                        KampioenschapSporterBoog.objects.bulk_create(bulk_lijst)
                        bulk_lijst = list()
                else:
                    self.stdout.write('[WARNING] Sporter %s is geen RK deelnemer want heeft geen vereniging' % deelnemer.sporterboog)
            # for

            if len(bulk_lijst) > 0:
                KampioenschapSporterBoog.objects.bulk_create(bulk_lijst)
            del bulk_lijst
        # for

        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('nhb_rayon')
                         .filter(competitie=comp,
                                 deel=DEEL_RK)
                         .order_by('nhb_rayon__rayon_nr')):

            deelkamp.heeft_deelnemerslijst = True
            deelkamp.save(update_fields=['heeft_deelnemerslijst'])

            # laat de lijsten sorteren en de volgorde bepalen
            self._verwerk_mutatie_initieel_deelkamp(deelkamp)

            # stuur de RKO een taak ('ter info')
            functie_rko = deelkamp.functie
            now = timezone.now()
            taak_deadline = now
            taak_tekst = "Ter info: De deelnemerslijst voor jouw Rayonkampioenschappen zijn zojuist vastgesteld door de BKO"
            taak_log = "[%s] Taak aangemaakt" % now

            # maak een taak aan voor deze BKO
            maak_taak(toegekend_aan_functie=functie_rko,
                      deadline=taak_deadline,
                      aangemaakt_door=None,         # systeem
                      beschrijving=taak_tekst,
                      log=taak_log)

            # schrijf in het logboek
            msg = "De deelnemerslijst voor de Rayonkampioenschappen in %s is zojuist vastgesteld." % str(deelkamp.nhb_rayon)
            msg += '\nDe %s is geïnformeerd via een taak' % functie_rko
            schrijf_in_logboek(None, "Competitie", msg)
        # for

    def _converteer_rk_teams(self, comp):
        """ converteer de sporters die gekoppeld zijn aan de RK teams
            de RK teams zijn die tijdens de regiocompetitie al aangemaakt door de verenigingen
            en er zijn regiocompetitie sporters aan gekoppeld welke misschien niet gerechtigd zijn.

            controleer ook meteen de vereniging van de deelnemer
            als laatste wordt de team sterkte opnieuw berekend

            het vaststellen van de wedstrijdklasse voor de RK teams volgt later
        """

        # maak een look-up tabel van RegioCompetitieSporterBoog naar KampioenschapSchutterBoog
        sporterboog_pk2regiocompetitiesporterboog = dict()
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('bij_vereniging')
                          .filter(regiocompetitie__competitie=comp)):
            sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk] = deelnemer
        # for

        regiocompetitiesporterboog_pk2kampioenschapsporterboog = dict()
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .select_related('bij_vereniging')
                          .filter(kampioenschap__competitie=comp)):
            try:
                regio_deelnemer = sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk]
            except KeyError:
                self.stderr.write(
                    '[WARNING] Kan regio deelnemer niet vinden voor kampioenschapsporterboog met pk=%s' %
                    deelnemer.pk)
            else:
                regiocompetitiesporterboog_pk2kampioenschapsporterboog[regio_deelnemer.pk] = deelnemer
        # for

        # sporters mogen maar aan 1 team gekoppeld worden
        gekoppelde_deelnemer_pks = list()

        for team in (KampioenschapTeam
                     .objects
                     .select_related('vereniging')
                     .prefetch_related('tijdelijke_leden')
                     .filter(kampioenschap__competitie=comp)):

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

    def _verwerk_mutatie_regio_afsluiten(self, comp):
        """ de BKO heeft gevraagd de regiocompetitie af te sluiten en alles klaar te maken voor het RK """

        # TODO: verplaats naar CompLaagRegio/operations/...

        # controleer dat de competitie in fase G is
        if not comp.regiocompetitie_is_afgesloten:
            # ga door naar fase J
            comp.regiocompetitie_is_afgesloten = True
            comp.save(update_fields=['regiocompetitie_is_afgesloten'])

            # verwijder alle eerder aangemaakte KampioenschapSchutterBoog
            # verwijder eerst alle eerder gekoppelde team leden
            for team in KampioenschapTeam.objects.filter(kampioenschap__competitie=comp):
                team.gekoppelde_leden.clear()
            # for
            KampioenschapSporterBoog.objects.filter(kampioenschap__competitie=comp).all().delete()

            # gerechtigde RK deelnemers aanmaken
            self._maak_deelnemerslijst_rks(comp)

            # RK teams opzetten en RK deelnemers koppelen
            self._converteer_rk_teams(comp)

            # eindstand regio in historische uitslag zetten (nodig voor AG's nieuwe competitie)
            self._eindstand_regio_indiv_naar_histcomp(comp)

            # maak taken aan voor de HWL's om deelname RK voor sporters van eigen vereniging door te geven

            # versturen e-mails uitnodigingen naar de deelnemers gebeurt tijdens opstarten elk uur

    def _maak_deelnemerslijst_bk_indiv(self, comp):
        """ bepaal de individuele deelnemers van het BK
            per klasse zijn dit de rayonkampioenen (4x) aangevuld met de sporters met de hoogste kwalificatie scores
            iedereen die scores neergezet heeft in het RK komt in de lijst
        """

        if comp.afstand == '18':
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
                                 result_rank__lt=100)
                         .exclude(deelname=DEELNAME_NEE)
                         .exclude(result_rank=0)
                         .select_related('kampioenschap',
                                         'kampioenschap__nhb_rayon',
                                         'indiv_klasse',
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
                        indiv_klasse=kampioen.indiv_klasse,
                        bij_vereniging=kampioen.bij_vereniging,
                        gemiddelde=gemiddelde,
                        gemiddelde_scores=gemiddelde_scores)

            if kampioen.result_rank == 1:
                nieuw.kampioen_label = 'Kampioen %s' % kampioen.kampioenschap.nhb_rayon.naam
                nieuw.deelname = DEELNAME_JA

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
        self._verwerk_mutatie_initieel_deelkamp(deelkamp_bk)

        # behoud maximaal 48 sporters in elke klasse: 24 deelnemers en 24 reserven
        qset = KampioenschapSporterBoog.objects.filter(kampioenschap=deelkamp_bk, volgorde__gt=48)
        qset.delete()

    def _verwerk_mutatie_opstarten_bk_indiv(self, comp):
        """ de BKO heeft gevraagd alles klaar te maken voor het BK individueel """

        # controleer dat de competitie in fase N is
        if not comp.rk_indiv_afgesloten:

            # individuele deelnemers vaststellen
            self._maak_deelnemerslijst_bk_indiv(comp)

            # ga door naar fase N
            comp.rk_indiv_afgesloten = True
            comp.save(update_fields=['rk_indiv_afgesloten'])

    def _maak_deelnemerslijst_bk_teams(self, comp):
        # TODO: integreer CompLaagBond/management/commands/maak_bk_teams_lijst
        # stop deze in CompLaagBonds/operations/...
        pass

    def _verwerk_mutatie_opstarten_bk_teams(self, comp):
        """ de BKO heeft gevraagd alles klaar te maken voor het BK teams """

        # controleer dat de competitie in fase N is
        if not comp.rk_teams_afgesloten:

            # individuele deelnemers vaststellen
            self._maak_deelnemerslijst_bk_teams(comp)

            # ga door naar fase N
            comp.rk_teams_afgesloten = True
            comp.save(update_fields=['rk_teams_afgesloten'])

    def _verwerk_mutatie_extra_rk_deelnemer(self, deelnemer):
        # gebruik de methode van opnieuw aanmelden om deze sporter op de reserve-lijst te krijgen
        self._opnieuw_aanmelden_indiv(deelnemer)

    def _verwerk_mutatie_klein_klassen_indiv(self, deelnemer, indiv_klasse):
        """ verplaats deelnemer (KampioenschapSporterBoog) van zijn huidige klasse
            naar de klasse indiv_klasse (CompetitieIndivKlasse)
            en pas daarbij de volgorde en rank aan
        """
        if deelnemer.indiv_klasse != indiv_klasse:

            self.stdout.write('[INFO] Verplaats deelnemer %s van kleine klasse %s naar klasse %s' % (
                                deelnemer, deelnemer.indiv_klasse, indiv_klasse))

            deelnemer.indiv_klasse = indiv_klasse
            deelnemer.save(update_fields=['indiv_klasse'])

            # stel de deelnemerslijst van de nieuwe klasse opnieuw op
            deelkamp = deelnemer.kampioenschap
            self._verwerk_mutatie_initieel_klasse_indiv(deelkamp, deelnemer.indiv_klasse)

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.mutatie

        if code == MUTATIE_COMPETITIE_OPSTARTEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Competitie opstarten' % mutatie.pk)
            self._verwerk_mutatie_competitie_opstarten()

        elif code == MUTATIE_AG_VASTSTELLEN_18M:
            self.stdout.write('[INFO] Verwerk mutatie %s: AG vaststellen 18m' % mutatie.pk)
            aanvangsgemiddelden_vaststellen_voor_afstand(18)

        elif code == MUTATIE_AG_VASTSTELLEN_25M:
            self.stdout.write('[INFO] Verwerk mutatie %s: AG vaststellen 25m' % mutatie.pk)
            aanvangsgemiddelden_vaststellen_voor_afstand(25)

        elif code == MUTATIE_INITIEEL:
            # let op: wordt alleen gebruik vanuit test code
            self.stdout.write('[INFO] Verwerk mutatie %s: initieel' % mutatie.pk)
            self._verwerk_mutatie_initieel(mutatie.kampioenschap.competitie, mutatie.kampioenschap.deel)

        elif code == MUTATIE_KAMP_CUT:
            self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)
            if mutatie.indiv_klasse:
                self._verwerk_mutatie_kamp_cut_indiv(mutatie.kampioenschap, mutatie.indiv_klasse,
                                                     mutatie.cut_oud, mutatie.cut_nieuw)
            else:
                self._verwerk_mutatie_kamp_cut_team(mutatie.kampioenschap, mutatie.team_klasse,
                                                    mutatie.cut_oud, mutatie.cut_nieuw)

        elif code == MUTATIE_KAMP_AANMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden' % mutatie.pk)
            self._verwerk_mutatie_kamp_aanmelden(mutatie.deelnemer)

        elif code == MUTATIE_KAMP_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden' % mutatie.pk)
            self._verwerk_mutatie_afmelden_indiv(mutatie.deelnemer)

        elif code == MUTATIE_REGIO_TEAM_RONDE:
            self.stdout.write('[INFO] Verwerk mutatie %s: regio team ronde' % mutatie.pk)
            self._verwerk_mutatie_regio_team_ronde(mutatie.regiocompetitie)

        elif code == MUTATIE_DOORZETTEN_REGIO_NAAR_RK:
            self.stdout.write('[INFO] Verwerk mutatie %s: afsluiten regiocompetitie' % mutatie.pk)
            self._verwerk_mutatie_regio_afsluiten(mutatie.competitie)

        elif code == MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK:
            self.stdout.write('[INFO] Verwerk mutatie %s: indiv doorzetten van RK naar BK' % mutatie.pk)
            self._verwerk_mutatie_opstarten_bk_indiv(mutatie.competitie)

        elif code == MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK:
            self.stdout.write('[INFO] Verwerk mutatie %s: teams doorzetten van RK naar BK' % mutatie.pk)
            self._verwerk_mutatie_opstarten_bk_teams(mutatie.competitie)

        elif code == MUTATIE_EXTRA_RK_DEELNEMER:
            self.stdout.write('[INFO] Verwerk mutatie %s: extra RK deelnemer' % mutatie.pk)
            self._verwerk_mutatie_extra_rk_deelnemer(mutatie.deelnemer)

        elif code == MUTATIE_KLEINE_KLASSE_INDIV:
            self.stdout.write('[INFO] Verwerk mutatie %s: kleine klassen indiv' % mutatie.pk)
            self._verwerk_mutatie_klein_klassen_indiv(mutatie.deelnemer, mutatie.indiv_klasse)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s door %s (pk=%s)' % (code, mutatie.door, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = CompetitieMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self.taken.hoogste_mutatie:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste CompetitieMutatie pk is %s' % self.taken.hoogste_mutatie.pk)
            qset = (CompetitieMutatie
                    .objects
                    .filter(pk__gt=self.taken.hoogste_mutatie.pk))
        else:
            qset = (CompetitieMutatie
                    .objects
                    .all())

        qset = qset.filter(is_verwerkt=False)
        mutatie_pks = qset.values_list('pk', flat=True)

        self.taken.hoogste_mutatie = mutatie_latest
        self.taken.save(update_fields=['hoogste_mutatie'])

        did_useful_work = False
        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            mutatie = (CompetitieMutatie
                       .objects
                       .select_related('competitie',
                                       'regiocompetitie',
                                       'kampioenschap',
                                       'indiv_klasse',
                                       'team_klasse',
                                       'deelnemer',
                                       'deelnemer__kampioenschap',
                                       'deelnemer__sporterboog__sporter',
                                       'deelnemer__indiv_klasse')
                       .get(pk=pk))
            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste KampioenschapMutatie pk is %s' % self.taken.hoogste_mutatie.pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = CompetitieMutatie.objects.count()
            if new_count != mutatie_count:
                mutatie_count = new_count
                self._verwerk_nieuwe_mutaties()
                now = datetime.datetime.now()

            # wacht 5 seconden voordat we opnieuw in de database kijken
            # het wachten kan onderbroken worden door een ping, als er een nieuwe mutatie toegevoegd is
            secs = (self.stop_at - now).total_seconds()
            if secs > 1:                                    # pragma: no branch
                timeout = min(5.0, secs)
                if self._sync.wait_for_ping(timeout):       # pragma: no branch
                    self._count_ping += 1                   # pragma: no cover
            else:
                # near the end
                break       # from the while                # pragma: no cover

            now = datetime.datetime.now()
        # while

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 15 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self.stop_at = (datetime.datetime.now()
                        + datetime.timedelta(minutes=duration)
                        - datetime.timedelta(seconds=15))

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):

        self._bepaal_boog2team()
        self._set_stop_time(**options)

        if options['all']:
            self.taken.hoogste_mutatie = None

        # verstuur uitnodigingen naar de sporters
        self._verstuur_uitnodigingen()

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except (DataError, OperationalError, IntegrityError) as exc:  # pragma: no cover
            # OperationalError treed op bij system shutdown, als database gesloten wordt
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

        except KeyboardInterrupt:                       # pragma: no cover
            pass

        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Onverwachte fout tijdens regiocomp_mutaties\n'
            tb_msg_start += '\n'
            tb_msg = tb_msg_start + '\n'.join(tb)

            # full traceback to syslog
            my_logger.error(tb_msg)

            self.stderr.write('[ERROR] Onverwachte fout tijdens regiocomp_mutaties: ' + str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            mailer_notify_internal_error(tb_msg)

        self.stdout.write('[DEBUG] Aantal pings ontvangen: %s' % self._count_ping)

        self.stdout.write('Klaar')


"""
    performance debug helper:

    from django.db import connection

        q_begin = len(connection.queries)

        # queries here

        print('queries: %s' % (len(connection.queries) - q_begin))
        for obj in connection.queries[q_begin:]:
            print('%10s %s' % (obj['time'], obj['sql'][:200]))
        # for
        sys.exit(1)

    test uitvoeren met --debug-mode anders wordt er niets bijgehouden
"""

# end of file
