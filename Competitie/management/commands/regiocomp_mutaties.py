# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# werk de tussenstand bij voor deelcompetities die niet afgesloten zijn zodra er nieuwe ScoreHist records zijn
# verwerkt ook een aantal opdrachten die concurrency protection nodig hebben

from django.conf import settings
from django.utils import timezone
from django.db.models import F
from django.core.management.base import BaseCommand
from BasisTypen.models import TeamType
from Competitie.models import (Competitie, CompetitieTaken, DeelCompetitie, DeelcompetitieKlasseLimiet,
                               RegioCompetitieSchutterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               KampioenschapSchutterBoog, DEELNAME_JA, DEELNAME_NEE,
                               CompetitieMutatie,
                               MUTATIE_AG_VASTSTELLEN_18M, MUTATIE_AG_VASTSTELLEN_25M, MUTATIE_COMPETITIE_OPSTARTEN,
                               MUTATIE_INITIEEL, MUTATIE_CUT, MUTATIE_AANMELDEN, MUTATIE_AFMELDEN, MUTATIE_TEAM_RONDE)
from Competitie.operations import (competities_aanmaken, bepaal_startjaar_nieuwe_competitie,
                                   aanvangsgemiddelden_vaststellen_voor_afstand)
from Overig.background_sync import BackgroundSync
import django.db.utils
import datetime

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField


class Command(BaseCommand):
    help = "Competitie mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._boogtypen = list()        # [boog_type.pk, ..]
        self._team_boogtypen = dict()   # [team_type.pk] = [boog_type.pk, ..]
        self._team_volgorde = list()    # [team_type.pk, ..]

        self.stop_at = datetime.datetime.now()

        self.taken = CompetitieTaken.objects.all()[0]

        self.pk2scores = dict()         # [RegioCompetitieSchutterBoog.pk] = [tup, ..] with tup = (afstand, score)
        self.pk2scores_alt = dict()

        self._onbekend2beter = dict()   # [competitieklasse.pk] = [klasse, ..] met oplopend AG

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
            straks als we de team schutters gaan verdelen over de teams moeten dat in een slimme volgorde
            zodat de sporters in toegestane teams en alle team typen gevuld worden.
            Voorbeeld: LB mag meedoen in LB, IB, BB en R teams terwijl C alleen in C team mag.
                       we moeten dus niet beginnen met de LB schutter in een R team te stoppen en daarna
                       geen sporters meer over hebben voor het LB team.
        """

        for team_type in (TeamType
                          .objects
                          .prefetch_related('boog_typen')
                          .all()):

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
    def _get_limiet(deelcomp, klasse):
        # bepaal de limiet
        try:
            limiet = (DeelcompetitieKlasseLimiet
                      .objects
                      .get(deelcompetitie=deelcomp,
                           klasse=klasse)
                      ).limiet
        except DeelcompetitieKlasseLimiet.DoesNotExist:
            limiet = 24

        return limiet

    @staticmethod
    def _update_rank_nummers(deelcomp, klasse):
        rank = 0
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse)
                    .order_by('volgorde')):
            if obj.deelname == DEELNAME_NEE:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank
            obj.save(update_fields=['rank', 'volgorde'])
        # for

    def _verwerk_mutatie_initieel_klasse(self, deelcomp, klasse):
        # Bepaal de top-X deelnemers voor een klasse van een kampioenschap
        # De kampioenen aangevuld met de schutters met hoogste gemiddelde
        # gesorteerde op gemiddelde

        self.stdout.write('[INFO] Bepaal deelnemers in klasse %s van %s' % (klasse, deelcomp))

        limiet = self._get_limiet(deelcomp, klasse)

        # kampioenen hebben deelnamegarantie
        kampioenen = (KampioenschapSchutterBoog
                      .objects
                      .exclude(kampioen_label='')
                      .filter(deelcompetitie=deelcomp,
                              klasse=klasse))

        lijst = list()
        aantal = 0
        for obj in kampioenen:
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
        # for

        # aanvullen met schutters tot aan de cut
        objs = (KampioenschapSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        klasse=klasse,
                        kampioen_label='')      # kampioenen hebben we al gedaan
                .order_by('-gemiddelde'))       # hoogste boven

        for obj in objs:
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
                if aantal >= limiet:
                    break       # uit de for
        # for

        # sorteer op gemiddelde en daarna op het volgnummer in de lijst
        # want sorteren op obj gaat niet
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

        # geef nu alle andere schutters en nieuw volgnummer
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

    def _verwerk_mutatie_initieel_deelcomp(self, deelcomp):
        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven schutters
        for deelnemer in (KampioenschapSchutterBoog
                          .objects
                          .filter(deelcompetitie=deelcomp)
                          .distinct('klasse')):

            # sorteer de lijst op gemiddelde en bepaalde volgorde
            self._verwerk_mutatie_initieel_klasse(deelcomp, deelnemer.klasse)
        # for

    def _verwerk_mutatie_initieel(self, competitie, laag):
        # bepaal de volgorde en rank van de deelnemers
        # in alle klassen van de RK of BK deelcompetities

        # via deelnemer kunnen we bepalen over welke kampioenschappen dit gaat
        for deelcomp in (DeelCompetitie
                         .objects
                         .filter(competitie=competitie,
                                 laag=laag)):
            self._verwerk_mutatie_initieel_deelcomp(deelcomp)
        # for

    def _verwerk_mutatie_afmelden(self, deelnemer):
        # pas alleen de ranking aan voor alle schutters in deze klasse
        # de deelnemer is al afgemeld en behoudt zijn volgorde zodat de RKO/BKO
        # 'm in grijs kan zien in de tabel

        # bij een mutatie "boven de cut" wordt de schutter bovenaan de lijst van reserve schutters
        # tot deelnemer gepromoveerd. Zijn gemiddelde bepaalt de volgorde

        deelnemer.deelname = DEELNAME_NEE
        deelnemer.save(update_fields=['deelname'])

        deelcomp = deelnemer.deelcompetitie
        klasse = deelnemer.klasse

        limiet = self._get_limiet(deelcomp, klasse)

        # haal de reserve schutter op
        try:
            reserve = (KampioenschapSchutterBoog
                       .objects
                       .get(deelcompetitie=deelcomp,
                            klasse=klasse,
                            rank=limiet+1))
        except KampioenschapSchutterBoog.DoesNotExist:
            # zoveel schutter zijn er niet (meer)
            pass
        else:
            if reserve.volgorde > deelnemer.volgorde:
                # de afgemelde deelnemer zit boven de cut

                # bepaal het nieuwe plekje van de reserve-schutter
                slechter = (KampioenschapSchutterBoog
                            .objects
                            .filter(deelcompetitie=deelcomp,
                                    klasse=klasse,
                                    gemiddelde__lt=reserve.gemiddelde,
                                    rank__lte=limiet)
                            .order_by('volgorde'))

                if len(slechter) > 0:
                    # zet het nieuwe plekje
                    reserve.volgorde = slechter[0].volgorde
                    reserve.save(update_fields=['volgorde'])

                    # schuif de andere schutters omlaag
                    slechter.update(volgorde=F('volgorde') + 1)
                # else: geen schutters om op te schuiven

        self._update_rank_nummers(deelcomp, klasse)

    def _opnieuw_aanmelden(self, deelnemer):
        # meld de deelnemer opnieuw aan door hem bij de reserves te zetten

        deelcomp = deelnemer.deelcompetitie
        klasse = deelnemer.klasse
        oude_volgorde = deelnemer.volgorde

        # verwijder de deelnemer uit de lijst op zijn oude plekje
        # en schuif de rest omhoog
        deelnemer.volgorde = VOLGORDE_PARKEER
        deelnemer.save(update_fields=['volgorde'])

        qset = (KampioenschapSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        klasse=klasse,
                        volgorde__gt=oude_volgorde,
                        volgorde__lt=VOLGORDE_PARKEER))
        qset.update(volgorde=F('volgorde') - 1)

        limiet = self._get_limiet(deelcomp, klasse)

        # als er minder dan limiet deelnemers zijn, dan invoegen op gemiddelde
        # als er een reserve lijst is, dan invoegen in de reserve-lijst op gemiddelde
        # altijd invoegen NA schutters met gelijkwaarde gemiddelde

        deelnemers_count = (KampioenschapSchutterBoog
                            .objects
                            .exclude(deelname=DEELNAME_NEE)
                            .filter(deelcompetitie=deelcomp,
                                    klasse=klasse,
                                    rank__lte=limiet,
                                    volgorde__lt=VOLGORDE_PARKEER).count())

        if deelnemers_count >= limiet:
            # er zijn genoeg schutters, dus deze her-aanmelding moet op de reserve-lijst

            # zoek een plekje in de reserve-lijst
            objs = (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
                            rank__gt=limiet,
                            gemiddelde__gte=deelnemer.gemiddelde)
                    .order_by('gemiddelde'))

            if len(objs):
                # invoegen na de reserve-schutter met gelijk of hoger gemiddelde
                nieuwe_rank = objs[0].rank + 1
            else:
                # er zijn geen reserve-schutters met gelijk of hoger gemiddelde
                # dus deze schutter mag boven aan de reserve-lijst
                nieuwe_rank = limiet + 1

            # maak een plekje in de lijst door andere schutters op te schuiven
            objs = (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
                            rank__gte=nieuwe_rank))

            if len(objs) > 0:
                obj = objs.order_by('volgorde')[0]
                nieuwe_volgorde = obj.volgorde
            else:
                # niemand om op te schuiven - zet aan het einde
                nieuwe_volgorde = (KampioenschapSchutterBoog
                                   .objects
                                   .exclude(volgorde=VOLGORDE_PARKEER)
                                   .filter(deelcompetitie=deelcomp,
                                           klasse=klasse)
                                   .count()) + 1
        else:
            # er is geen reserve-lijst in deze klasse
            # de schutter gaat dus meteen de deelnemers lijst in
            objs = (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
                            gemiddelde__gte=deelnemer.gemiddelde,
                            volgorde__lt=VOLGORDE_PARKEER)
                    .order_by('gemiddelde'))

            if len(objs) > 0:
                # voeg de schutter in na de laatste deelnemer
                nieuwe_volgorde = objs[0].volgorde + 1
            else:
                # geen betere schutter gevonden
                # zet deze deelnemer boven aan de lijst
                nieuwe_volgorde = 1

        objs = (KampioenschapSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        klasse=klasse,
                        volgorde__gte=nieuwe_volgorde))
        objs.update(volgorde=F('volgorde') + 1)

        deelnemer.volgorde = nieuwe_volgorde
        deelnemer.deelname = DEELNAME_JA
        deelnemer.save(update_fields=['volgorde', 'deelname'])

        # deel de rank nummers opnieuw uit
        self._update_rank_nummers(deelcomp, klasse)

    def _verwerk_mutatie_aanmelden(self, deelnemer):
        if deelnemer.deelname != DEELNAME_JA:
            if deelnemer.deelname == DEELNAME_NEE:
                self._opnieuw_aanmelden(deelnemer)
            else:
                deelnemer.deelname = DEELNAME_JA
                deelnemer.save(update_fields=['deelname'])
                # verder hoeven we niets te doen: volgorde en rank blijft hetzelfde

    @staticmethod
    def _verwerk_mutatie_verhoog_cut(deelcomp, klasse, cut_nieuw):
        # de deelnemerslijst opnieuw sorteren op gemiddelde
        # dit is nodig omdat kampioenen naar boven geplaatst kunnen zijn bij het verlagen van de cut
        # nu plaatsen we ze weer terug op hun originele plek
        lijst = list()
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
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
    def _verwerk_mutatie_verlaag_cut(deelcomp, klasse, cut_oud, cut_nieuw):
        # zoek de kampioenen die al deel mochten nemen (dus niet op reserve lijst)
        kampioenen = (KampioenschapSchutterBoog
                      .objects
                      .exclude(kampioen_label='')
                      .filter(deelcompetitie=deelcomp,
                              klasse=klasse,
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

        # aanvullen met schutters tot aan de cut
        objs = (KampioenschapSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        klasse=klasse,
                        kampioen_label='',  # kampioenen hebben we al gedaan
                        rank__lte=cut_oud)
                .order_by('-gemiddelde'))  # hoogste boven

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

        # geef nu alle andere schutters (tot de oude cut) opnieuw een volgnummer
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

    def _verwerk_mutatie_cut(self, deelcomp, klasse, cut_oud, cut_nieuw):
        try:
            is_nieuw = False
            limiet = (DeelcompetitieKlasseLimiet
                      .objects
                      .get(deelcompetitie=deelcomp,
                           klasse=klasse))
        except DeelcompetitieKlasseLimiet.DoesNotExist:
            # maak een nieuwe aan
            is_nieuw = True
            limiet = DeelcompetitieKlasseLimiet(deelcompetitie=deelcomp,
                                                klasse=klasse)

        if cut_nieuw > cut_oud:
            # limiet verhogen is simpel, want deelnemers blijven deelnemers
            if cut_nieuw == 24:
                # verwijder het limiet record
                if not is_nieuw:
                    limiet.delete()
            else:
                limiet.limiet = cut_nieuw
                limiet.save()

            # toch even de deelnemerslijst opnieuw sorteren op gemiddelde
            self._verwerk_mutatie_verhoog_cut(deelcomp, klasse, cut_nieuw)

        elif cut_nieuw < cut_oud:
            # limiet is omlaag gezet
            # zorg dat de regiokampioenen er niet af vallen
            limiet.limiet = cut_nieuw
            limiet.save()

            self._verwerk_mutatie_verlaag_cut(deelcomp, klasse, cut_oud, cut_nieuw)

        # else: cut_oud == cut_nieuw --> doe niets
        #   (dit kan voorkomen als 2 gebruikers tegelijkertijd de cut veranderen)

    @staticmethod
    def _verwerk_mutatie_competitie_opstarten():
        jaar = bepaal_startjaar_nieuwe_competitie()
        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() == 0:
            competities_aanmaken(jaar)

    def _verwerk_mutatie_team_ronde(self, deelcomp):

        # TODO: sanity check voordat we doorzetten: alle team wedstrijdpunten toegekend?

        ronde_nr = deelcomp.huidige_team_ronde + 1

        if ronde_nr <= 7:
            now = timezone.now()
            now = timezone.localtime(now)
            now_str = now.strftime("%Y-%m-%d %H:%M")

            ver_dict = dict()       # [ver_nr] = list(vsg, deelnemer_pk, boog_type_pk)

            # voor elke deelnemer het gemiddelde_begin_team_ronde invullen
            for deelnemer in (RegioCompetitieSchutterBoog
                              .objects
                              .select_related('bij_vereniging',
                                              'schutterboog',
                                              'schutterboog__boogtype')
                              .filter(deelcompetitie=deelcomp,
                                      inschrijf_voorkeur_team=True)):

                if deelnemer.aantal_scores == 0:
                    vsg = deelnemer.ag_voor_team
                else:
                    vsg = deelnemer.gemiddelde  # individuele voortschrijdend gemiddelde

                deelnemer.gemiddelde_begin_team_ronde = vsg
                deelnemer.save(update_fields=['gemiddelde_begin_team_ronde'])

                ver_nr = deelnemer.bij_vereniging.ver_nr
                tup = (-vsg, deelnemer.pk, deelnemer.schutterboog.boogtype.pk)
                try:
                    ver_dict[ver_nr].append(tup)
                except KeyError:
                    ver_dict[ver_nr] = [tup]
            # for

            for team_schutters in ver_dict.values():
                team_schutters.sort()
            # for

            # maak voor elk team een 'ronde instantie' aan waarin de invallers en score bijgehouden worden
            # verdeel ook de sporters volgens VSG
            for team_type_pk in self._team_volgorde:

                team_boogtypen = self._team_boogtypen[team_type_pk]

                for team in (RegiocompetitieTeam
                             .objects
                             .select_related('vereniging')
                             .prefetch_related('gekoppelde_schutters')
                             .filter(deelcompetitie=deelcomp,
                                     team_type__pk=team_type_pk)
                             .order_by('-aanvangsgemiddelde')):     # hoogste eerst

                    ronde_team = RegiocompetitieRondeTeam(
                                    team=team,
                                    ronde_nr=ronde_nr,
                                    logboek="[%s] Aangemaakt bij opstarten ronde %s\n" % (now_str, ronde_nr))
                    ronde_team.save()

                    # koppel de schutters
                    if deelcomp.regio_heeft_vaste_teams:
                        # vaste team begint elke keer met de vaste schutters
                        schutter_pks = team.gekoppelde_schutters.values_list('pk', flat=True)
                    else:
                        # voortschrijdend gemiddelde: pak de volgende 4 beste sporters van de vereniging
                        schutter_pks = list()
                        ver_nr = team.vereniging.ver_nr
                        ver_schutters = ver_dict[ver_nr]
                        gebruikt = list()
                        for tup in ver_schutters:
                            _, deelnemer_pk, boogtype_pk = tup
                            if boogtype_pk in team_boogtypen:
                                schutter_pks.append(deelnemer_pk)
                                gebruikt.append(tup)

                            if len(schutter_pks) == 4:
                                break
                        # for

                        for tup in gebruikt:
                            ver_schutters.remove(tup)
                        # for

                    ronde_team.deelnemers_geselecteerd.set(schutter_pks)
                    ronde_team.deelnemers_feitelijk.set(schutter_pks)

                    # schrijf de namen van de leden in het logboek
                    ronde_team.logboek += '[%s] Geselecteerde schutters:\n' % now_str
                    for deelnemer in (RegioCompetitieSchutterBoog
                                      .objects
                                      .select_related('schutterboog__nhblid')
                                      .filter(pk__in=schutter_pks)):
                        ronde_team.logboek += '   ' + str(deelnemer.schutterboog.nhblid) + '\n'
                    # for
                    ronde_team.save(update_fields=['logboek'])
                # for
            # for

            deelcomp.huidige_team_ronde = ronde_nr
            deelcomp.save(update_fields=['huidige_team_ronde'])

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
            self.stdout.write('[INFO] Verwerk mutatie %s: initieel' % mutatie.pk)
            self._verwerk_mutatie_initieel(mutatie.deelcompetitie.competitie, mutatie.deelcompetitie.laag)

        elif code == MUTATIE_CUT:
            self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)
            self._verwerk_mutatie_cut(mutatie.deelcompetitie, mutatie.klasse, mutatie.cut_oud, mutatie.cut_nieuw)

        elif code == MUTATIE_AANMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden' % mutatie.pk)
            self._verwerk_mutatie_aanmelden(mutatie.deelnemer)

        elif code == MUTATIE_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden' % mutatie.pk)
            self._verwerk_mutatie_afmelden(mutatie.deelnemer)

        elif code == MUTATIE_TEAM_RONDE:
            self.stdout.write('[INFO] Verwerk mutatie %s: team ronde' % mutatie.pk)
            self._verwerk_mutatie_team_ronde(mutatie.deelcompetitie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s door %s (pk=%s)' % (code, mutatie.door, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = CompetitieMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self.taken.hoogste_mutatie:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste KampioenschapMutatie pk is %s' % self.taken.hoogste_mutatie.pk)
            qset = (CompetitieMutatie
                    .objects
                    .filter(pk__gt=self.taken.hoogste_mutatie.pk))
        else:
            qset = (CompetitieMutatie
                    .objects
                    .all())

        mutatie_pks = qset.values_list('pk', flat=True)

        self.taken.hoogste_mutatie = mutatie_latest
        self.taken.save(update_fields=['hoogste_mutatie'])

        did_useful_work = False
        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            mutatie = (CompetitieMutatie
                       .objects
                       .select_related('deelnemer',
                                       'deelnemer__deelcompetitie',
                                       'deelnemer__schutterboog__nhblid',
                                       'deelnemer__klasse')
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
        # monitor voor nieuwe ScoreHist
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
                break       # from the while

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

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except django.db.utils.DataError as exc:        # pragma: no coverage
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
        except KeyboardInterrupt:                       # pragma: no coverage
            pass

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
