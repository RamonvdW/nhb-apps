# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# zodra er nieuwe ScoreHist records zijn, de tussenstand bijwerken voor deelcompetities die niet afgesloten zijn
# voor zowel individueel als team score aspecten

from django.core.management.base import BaseCommand
from django.db.models import F, Q
import django.db.utils
from Competitie.models import (CompetitieTaken, CompetitieKlasse,
                               LAAG_REGIO, Competitie, DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam)
from Score.models import ScoreHist, SCORE_WAARDE_VERWIJDERD
import datetime
import time


class Command(BaseCommand):
    help = "Competitie tussenstand bijwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.stop_at = datetime.datetime(2000, 1, 1)

        self.taken = CompetitieTaken.objects.all()[0]

        self.index2scores = dict()      # [(DeelCompetitie.pk, RegioCompetitieSchutterBoog.pk)] = [(afstand, score), ..]

        self._onbekend2beter = dict()   # [competitieklasse.pk] = [klasse, ..] met oplopend AG

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--all', action='store_true')       # alles opnieuw vaststellen
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_overstappers_regio(self, regio_comp_pks):
        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('bij_vereniging',
                                'bij_vereniging__regio',
                                'sporterboog__sporter',
                                'sporterboog__sporter__bij_vereniging',
                                'sporterboog__sporter__bij_vereniging__regio')
                .filter(deelcompetitie__competitie__pk__in=regio_comp_pks)
                .filter((~Q(bij_vereniging=F('sporterboog__sporter__bij_vereniging')) |     # bevat geen uitstappers
                         Q(sporterboog__sporter__bij_vereniging=None))))                    # bevat de uitstappers
        for obj in objs:
            sporter = obj.sporterboog.sporter
            if sporter.bij_vereniging:
                self.stdout.write('[INFO] Verwerk overstap %s: [%s] %s --> [%s] %s' % (
                                  sporter.lid_nr,
                                  obj.bij_vereniging.regio.regio_nr, obj.bij_vereniging,
                                  sporter.bij_vereniging.regio.regio_nr, sporter.bij_vereniging))

                # overschrijven naar andere deelcompetitie
                if obj.bij_vereniging.regio != sporter.bij_vereniging.regio:
                    obj.deelcompetitie = DeelCompetitie.objects.get(competitie=obj.deelcompetitie.competitie,
                                                                    nhb_regio=sporter.bij_vereniging.regio)
                obj.bij_vereniging = sporter.bij_vereniging
                obj.save()
        # for

    def _verwerk_overstappers(self):
        """ Deze functie verwerkt schutters die overgestapt zijn naar een andere vereniging
            Deze worden overgeschreven naar een andere deelcompetitie (regio/RK/BK).
        """

        # 1. Sporter.bij_vereniging komt overeen met informatie uit CRM

        # 2. Schutters in regiocompetitie kunnen elk moment overstappen
        #    RegioCompetitieSchutterBoog.bij_vereniging
        # FUTURE: voor de teamcompetitie moet dit pas gebeuren nadat de teamscores vastgesteld zijn

        # 3. Bij vaststellen RK/BK deelname/reserve wordt vereniging bevroren (afsluiten fase G)
        #    KampioenschapSchutterBoog.bij_vereniging
        #    overstappen is daarna niet meer mogelijk

        regio_comp_pks = list()
        rk_comp_pks = list()
        for comp in Competitie.objects.filter(is_afgesloten=False):
            comp.bepaal_fase()
            if comp.fase <= 'F':
                # in fase van de regiocompetitie
                regio_comp_pks.append(comp.pk)
        # for

        self._verwerk_overstappers_regio(regio_comp_pks)

    def _prep_caches(self):
        # maak een structuur om gerelateerde IndivWedstrijdklassen te vinden
        indiv_alike = dict()     # [(boogtype.pk, leeftijdsklasse.pk, ...)] = [indiv, ..]
        klassen_qset = (CompetitieKlasse
                        .objects
                        .select_related('competitie', 'indiv', 'indiv__boogtype')
                        .prefetch_related('indiv__leeftijdsklassen')
                        .filter(team=None))
        for obj in klassen_qset:
            indiv = obj.indiv
            if not indiv.is_onbekend:
                tup = (indiv.boogtype.pk,)
                tup += tuple(indiv.leeftijdsklassen.values_list('pk', flat=True))       # TODO: avoid database hit
                try:
                    if indiv not in indiv_alike[tup]:
                        indiv_alike[tup].append(indiv)
                except KeyError:
                    indiv_alike[tup] = [indiv]
        # for

        # maak een datastructuur waarmee we snel kunnen bepalen naar welke nieuwe
        # wedstrijdklasse een schutter verplaatst kan worden vanuit klasse onbekend
        for klasse in klassen_qset:
            if klasse.indiv.is_onbekend:
                tup = (klasse.indiv.boogtype.pk,)
                tup += tuple(klasse.indiv.leeftijdsklassen.values_list('pk', flat=True))    # TODO: avoid database hit

                for indiv in indiv_alike[tup]:
                    # zoek klassen met deze indiv
                    for klasse2 in klassen_qset:
                        if klasse2.indiv == indiv and klasse2.competitie == klasse.competitie:
                            try:
                                self._onbekend2beter[klasse.pk].append(klasse2)
                            except KeyError:
                                self._onbekend2beter[klasse.pk] = [klasse2]
                # for
        # for

        # sorteer de 'alike' klassen op aflopend AG
        for klasse_pk in self._onbekend2beter.keys():
            self._onbekend2beter[klasse_pk].sort(key=lambda x: x.min_ag, reverse=True)
        # for

    def _vind_scores(self):
        """ zoek alle recent ingevoerde scores en bepaal van welke schuttersboog
            de tussenstand bijgewerkt moet worden.
            Vult index2scores.
        """
        self.index2scores = dict()

        scorehist_latest = ScoreHist.objects.latest('pk')
        # als hierna een extra ScoreHist aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        # bepaal de scorehist objecten die we willen bekijken
        qset = (ScoreHist
                .objects
                .select_related('score',
                                'score__sporterboog')
                .all())

        if self.taken.hoogste_scorehist:
            self.stdout.write('[INFO] vorige hoogste ScoreHist pk is %s' % self.taken.hoogste_scorehist.pk)
            qset = qset.filter(pk__gt=self.taken.hoogste_scorehist.pk)

        # bepaal de sporterboog pk's die we bij moeten werken
        allowed_sporterboog_pks = qset.values_list('score__sporterboog__pk', flat=True)

        self.taken.hoogste_scorehist = scorehist_latest
        self.taken.save(update_fields=['hoogste_scorehist'])
        self.stdout.write('[INFO] nieuwe hoogste ScoreHist pk is %s' % self.taken.hoogste_scorehist.pk)

        # een deelcompetitie heeft ingeschreven schuttersboog (RegioCompetitieSchutterBoog)
        # een deelcompetitie bestaat uit rondes (RegioCompetitieRonde)
        # maar verschil tussen rondes met beschrijving "Ronde N oude programma" en zonder
        # elke ronde bevat een plan met wedstrijden
        # wedstrijden hebben een datum
        # wedstrijden hebben een uitslag met scores
        # scores refereren aan een sporterboog
        # schutters kunnen in een wedstrijd buiten hun ingeschreven rayon geschoten hebben
        rondes = list()
        for ronde in (DeelcompetitieRonde
                      .objects
                      .select_related('deelcompetitie', 'plan')
                      .filter(deelcompetitie__is_afgesloten=False,
                              deelcompetitie__laag=LAAG_REGIO)
                      .all()):

            week_nr = ronde.week_nr
            if week_nr < 26:
                week_nr += 100

            tup = (week_nr, ronde.pk, ronde)
            rondes.append(tup)
        # for

        # sorteer op weeknummer, anders raken de scores door de war en berekenen we
        # een verkeerd gemiddelde en verplaatsen we de schutter naar de verkeerde klasse
        rondes.sort()

        for _, _, ronde in rondes:
            # sorteer de beschikbare scores op het moment van de wedstrijd
            for wedstrijd in (ronde
                              .plan
                              .wedstrijden
                              .select_related('uitslag')
                              .order_by('datum_wanneer',
                                        'tijd_begin_wedstrijd',
                                        'pk')
                              .all()):

                uitslag = wedstrijd.uitslag
                if uitslag:
                    for score in (uitslag
                                  .scores
                                  .select_related('sporterboog')
                                  .exclude(waarde=0)                # 0 scores zijn voor team competitie only
                                  .all()):
                        tup = (uitslag.afstand_meter, score)
                        pk = score.sporterboog.pk
                        index = (ronde.deelcompetitie.pk, score.sporterboog.pk)
                        if pk in allowed_sporterboog_pks:   # presumed better than huge __in
                            try:
                                self.index2scores[index].append(tup)
                            except KeyError:
                                self.index2scores[index] = [tup]
                    # for
            # for
        # for

        self.stdout.write('[INFO] Aantal unieke (deelcomp + sporterboog) in index2scores: %s' % len(self.index2scores))

    @staticmethod
    def _bepaal_laagste_nr(waardes):
        # bepaalde het schrap-resultaat pas bij 7 scores
        # dus als er 7 niet-nul scores zijn, dan vervalt er 1
        if len(waardes) <= 6 or waardes.count(0) > 0:
            # minder dan 7 scores
            return 0, 0

        # zoek de laagste score, van achteren
        waardes = waardes[:]            # maak kopie
        waardes.reverse()
        laagste = min(waardes)
        nr = waardes.index(laagste)     # 0..6
        return 7 - nr, laagste          # 1..7

    @staticmethod
    def _bepaal_gemiddelde_en_totaal(waardes_in, aantal_voor_gem, pijlen_per_ronde):
        # only consider non-zero values as scores
        scores = [waarde for waarde in waardes_in if waarde != 0]

        # limit number of scores evaluated
        scores.sort(reverse=True)
        scores = scores[:aantal_voor_gem]

        if len(scores) < 1:
            # kan geen gemiddelde berekenen
            return 0.0, 0

        # bereken het gemiddelde
        totaal = sum(scores)
        gem = totaal / (len(scores) * pijlen_per_ronde)

        # afronden op 3 decimalen (anders gebeurt dat tijdens opslaan in database)
        gem = round(gem, 3)

        return gem, totaal

    def _update_regiocompetitieschuttersboog(self):
        count = 0
        for deelcomp in (DeelCompetitie
                         .objects
                         .exclude(is_afgesloten=True)
                         .select_related('competitie')
                         .all()):

            comp = deelcomp.competitie

            if comp.afstand == '18':
                pijlen_per_ronde = 30
                max_score = 300
                comp_afstand = 18
            else:
                pijlen_per_ronde = 25
                max_score = 250
                comp_afstand = 25

            for deelnemer in (RegioCompetitieSchutterBoog
                              .objects
                              .filter(deelcompetitie=deelcomp)
                              .select_related('sporterboog')
                              .prefetch_related('scores')
                              .all()):

                index = (deelcomp.pk, deelnemer.sporterboog.pk)
                try:
                    tups = self.index2scores[index]
                except KeyError:
                    pass
                else:
                    # tot nu toe hebben we de verwijderde scores meegenomen zodat we deze
                    # change-trigger krijgen. Nu moeten de verwijderde scores eruit
                    scores = [score for afstand, score in tups if score.waarde != SCORE_WAARDE_VERWIJDERD and afstand == comp_afstand]

                    # nieuwe scores toevoegen
                    curr_scores = deelnemer.scores.all()
                    for score in scores:
                        if score not in curr_scores:
                            deelnemer.scores.add(score)
                    # for

                    # verwijderde scores doorvoeren
                    for score in curr_scores:
                        if score not in scores:
                            deelnemer.scores.remove(score)
                    # for

                    # door waarde te filteren op max_score voorkomen we problemen
                    # die anders pas naar boven komen tijdens de save()
                    waardes = [score.waarde for afstand, score in tups if score.waarde <= max_score and afstand == comp_afstand]

                    waardes.extend([0, 0, 0, 0, 0, 0, 0])
                    waardes = waardes[:7]
                    deelnemer.score1 = waardes[0]
                    deelnemer.score2 = waardes[1]
                    deelnemer.score3 = waardes[2]
                    deelnemer.score4 = waardes[3]
                    deelnemer.score5 = waardes[4]
                    deelnemer.score6 = waardes[5]
                    deelnemer.score7 = waardes[6]
                    deelnemer.aantal_scores = len(waardes) - waardes.count(0)
                    deelnemer.laagste_score_nr, laagste = self._bepaal_laagste_nr(waardes)
                    deelnemer.gemiddelde, deelnemer.totaal = self._bepaal_gemiddelde_en_totaal(waardes, comp.aantal_scores_voor_rk_deelname, pijlen_per_ronde)

                    # kijk of verplaatsing uit klasse onbekend van toepassing is
                    if deelnemer.ag_voor_indiv < 0.001:
                        try:
                            betere_klassen = self._onbekend2beter[deelnemer.klasse.pk]
                        except KeyError:
                            # overslaan, want niet meer in een klasse onbekend
                            pass
                        else:
                            # kijk of 3 scores ingevuld zijn
                            # dit hoeven niet de eerste drie scores te zijn!
                            waardes_niet_nul = [waarde for waarde in waardes if waarde > 0]
                            if len(waardes_niet_nul) >= 3:
                                totaal = sum(waardes_niet_nul[:3])      # max 3 scores meenemen
                                # afronden op 3 decimalen (anders gebeurt dat tijdens opslaan in database)
                                new_ag = round(totaal / (3 * pijlen_per_ronde), 3)

                                # de betere klassen zijn gesorteerd op AG, hoogste eerst
                                for klasse in betere_klassen:       # pragma: no branch
                                    if new_ag >= klasse.min_ag:
                                        # dit is de nieuwe klasse
                                        self.stdout.write(
                                            '[INFO] Verplaats %s (%sm) met nieuw AG %.3f naar klasse %s' % (
                                                deelnemer.sporterboog.sporter.lid_nr, klasse.competitie.afstand, new_ag, klasse))
                                        deelnemer.klasse = klasse
                                        break
                                # for

                    deelnemer.save()
                    count += 1
        # for
        self.stdout.write('[INFO] Scores voor %s deelnemers bijgewerkt' % count)

    @staticmethod
    def _update_team_scores():
        """ Update alle team scores aan de hand van wie er in de teams zitten en de door de RCL geselecteerde scores
        """
        for deelcomp in DeelCompetitie.objects.filter(laag=LAAG_REGIO, is_afgesloten=False):
            ronde_nr = deelcomp.huidige_team_ronde
            if 1 <= ronde_nr <= 7:
                # pak alle teams in deze deelcompetitie erbij
                teams = RegiocompetitieTeam.objects.filter(deelcompetitie=deelcomp).values_list('pk', flat=True)

                # doorloop alle ronde-teams voor de huidige ronde van de deelcompetitie
                for ronde_team in (RegiocompetitieRondeTeam
                                   .objects
                                   .prefetch_related('scores_feitelijk')
                                   .filter(team__in=teams,
                                           ronde_nr=ronde_nr)):

                    team_scores = list()
                    score_pks = list()
                    for score in ronde_team.scores_feitelijk.all():
                        team_scores.append(score.waarde)
                        score_pks.append(score.pk)
                    # for
                    team_scores.sort(reverse=True)      # hoogste eerst

                    # ScoreHist erbij zoeken
                    hist_pks = list()
                    for scorehist in (ScoreHist
                                      .objects
                                      .select_related('score')
                                      .filter(score__in=score_pks)
                                      .order_by('-when')):      # nieuwste eerst
                        if scorehist.score.pk in score_pks:
                            hist_pks.append(scorehist.pk)
                            score_pks.remove(scorehist.score.pk)

                        if len(score_pks) == 0:
                            # no more scores for which to find a ScoreHist
                            break       # from the for
                    # for

                    # sla de ScoreHist op
                    ronde_team.scorehist_feitelijk.set(hist_pks)

                    # de hoogste 3 scores maken de team score
                    team_score = 0
                    for score in team_scores[:3]:
                        team_score += score
                    # for

                    # is de team score aangepast?
                    if ronde_team.team_score != team_score:
                        # print('nieuwe team_score voor team %s: %s --> %s' % (team, team.team_score, team_score))
                        ronde_team.team_score = team_score
                        ronde_team.save(update_fields=['team_score'])

                # for (ronde team)
        # for (deelcomp)

    def _update_tussenstand(self):
        begin = datetime.datetime.now()

        # stap 1: alle RegioCompetitieSchutterBoog.scores vaststellen
        self._vind_scores()

        # stap 2: overige velden bijwerken van aangepaste RegioCompetitieSchutterBoog
        self._update_regiocompetitieschuttersboog()

        # stap 3: teams scores bijwerken
        self._update_team_scores()

        klaar = datetime.datetime.now()
        self.stdout.write('[INFO] Tussenstand bijgewerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_scores(self):
        # monitor voor nieuwe ScoreHist
        hist_count = 0      # moet 0 zijn: beschermd tegen query op lege scorehist tabel
        now = datetime.datetime.now()
        while now < self.stop_at:               # pragma: no branch
            new_count = ScoreHist.objects.count()
            if new_count != hist_count:
                # verwijder eventuele 'fake records' die gebruikt zijn als trigger van deze dienst
                fake_objs = ScoreHist.objects.filter(score=None)
                fake_count = fake_objs.count()
                if fake_count > 0:
                    self.stdout.write('[DEBUG] Verwijder %s fake ScoreHist records' % fake_count)
                    fake_objs.delete()
                    new_count = ScoreHist.objects.count()

                hist_count = new_count
                self._update_tussenstand()
                now = datetime.datetime.now()

            # sleep at least 2 seconds, then check again
            secs = (self.stop_at - now).total_seconds()
            if secs > 2:                          # pragma: no branch
                secs = min(secs, 2.0)
                time.sleep(secs)
            else:
                break       # from the while      # pragma: no cover

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
        self._set_stop_time(**options)

        if options['all']:
            self.taken.hoogste_scorehist = None

        self._verwerk_overstappers()

        self._prep_caches()

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_scores()
        except django.db.utils.DataError as exc:        # pragma: no cover
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
        except KeyboardInterrupt:                       # pragma: no cover
            pass

        self.stdout.write('Klaar')

# end of file
