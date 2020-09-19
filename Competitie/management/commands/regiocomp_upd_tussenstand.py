# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# werk de tussenstand bij voor deelcompetities die niet afgesloten zijn
# zodra er nieuwe ScoreHist records zijn

from django.core.management.base import BaseCommand
import django.db.utils
from Competitie.models import (CompetitieTaken,
                               LAAG_REGIO, DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog)
from Score.models import ScoreHist, SCORE_WAARDE_VERWIJDERD
import datetime
import time


class Command(BaseCommand):
    help = "Competitie tussenstand bijwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.stop_at = 0

        self.taken = CompetitieTaken.objects.all()[0]

        self.pk2scores = dict()      # [RegioCompetitieSchutterBoog.pk] = [score, ..]
        self.pk2scores_alt = dict()

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--all', action='store_true')       # alles opnieuw vaststellen
        parser.add_argument('--quick', action='store_true')     # for testing

    def _vind_scores(self):

        scorehist_latest = ScoreHist.objects.latest('pk')

        # bepaal de scorehist objecten die we willen bekijken
        qset = (ScoreHist
                .objects
                .select_related('score', 'score__schutterboog')
                .all())

        if self.taken.hoogste_scorehist:
            self.stdout.write('[INFO] vorige hoogste ScoreHist pk is %s' % self.taken.hoogste_scorehist.pk)
            qset = qset.filter(pk__gt=self.taken.hoogste_scorehist.pk)

        # bepaal de schutterboog pk's die we bij moeten werken
        allowed_schutterboog_pks = qset.values_list('score__schutterboog__pk', flat=True)

        self.taken.hoogste_scorehist = scorehist_latest
        self.taken.save(update_fields=['hoogste_scorehist'])
        self.stdout.write('[INFO] nieuwe hoogste ScoreHist pk is %s' % self.taken.hoogste_scorehist.pk)

        # een deelcompetitie heeft ingeschreven schuttersboog (RegioCompetitieSchutterBoog)
        # een deelcompetitie bestaat uit rondes (RegioCompetitieRonde)
        # maar verschil tussen rondes met beschrijving "Ronde N oude programma" en zonder
        # elke ronde bevat een plan met wedstrijden
        # wedstrijden hebben een datum
        # wedstrijden hebben een uitslag met scores
        # scores refereren aan een schutterboog
        # schutters kunnen in een wedstrijd buiten hun ingeschreven rayon geschoten hebben
        for ronde in (DeelcompetitieRonde
                      .objects
                      .select_related('deelcompetitie', 'plan')
                      .filter(deelcompetitie__is_afgesloten=False,
                              deelcompetitie__laag=LAAG_REGIO)
                      .all()):
            self.stdout.write('[INFO] ronde: %s' % ronde)
            is_alt = ronde.beschrijving.startswith('Ronde ') and ronde.beschrijving.endswith(' oude programma')

            # tijdelijk: de geïmporteerde uitslagen zijn de normale
            #            de handmatig ingevoerde scores zijn het alternatief
            is_alt = not is_alt     # FUTURE: schakelaar omzetten als we geen import meer doen

            self.stdout.write('[INFO]  plan: %s' % ronde.plan)
            for wedstrijd in (ronde
                              .plan
                              .wedstrijden
                              .select_related('uitslag')
                              .order_by('datum_wanneer',
                                        'tijd_begin_wedstrijd')
                              .all()):
                self.stdout.write('[INFO]   wedstrijd: %s' % wedstrijd)
                uitslag = wedstrijd.uitslag
                if uitslag:
                    for score in (uitslag
                                  .scores
                                  .select_related('schutterboog')
                                  .all()):
                        pk = score.schutterboog.pk
                        if pk in allowed_schutterboog_pks:   # presumed better than huge __in
                            pk2scores = self.pk2scores_alt if is_alt else self.pk2scores
                            try:
                                pk2scores[pk].append(score)
                            except KeyError:
                                pk2scores[pk] = [score]
                    # for
            # for
        # for

        self.stdout.write('[INFO] Aantallen: pk2scores=%s, pk2scores_alt=%s' % (len(self.pk2scores),
                                                                                len(self.pk2scores_alt)))

    @staticmethod
    def _bepaal_laagste_nr(waardes):
        waardes.reverse()
        laagste = min(waardes)
        nr = waardes.index(laagste)     # 0..6
        return 7 - nr, laagste          # 1..7

    @staticmethod
    def _bepaal_gemiddelde_en_totaal(waardes, laagste, pijlen_per_ronde):
        aantal_niet_nul = len([waarde for waarde in waardes if waarde != 0])
        if aantal_niet_nul:
            totaal = sum(waardes) - laagste
            if laagste > 0:     # ga er vanuit dat er meer dan 1 score is
                aantal_niet_nul -= 1
            # afronden op 3 decimalen (anders gebeurt dat tijdens opslaan in database)
            gem = round(totaal / (aantal_niet_nul * pijlen_per_ronde), 3)
            return gem, totaal
        return 0.0, 0

    def _update_regiocompetitieschuttersboog(self):
        count = 0
        for deelcomp in (DeelCompetitie
                         .objects
                         .exclude(is_afgesloten=True)
                         .select_related('competitie')
                         .all()):

            if deelcomp.competitie.afstand == '18':
                pijlen_per_ronde = 30
                max_score = 300
            else:
                pijlen_per_ronde = 25
                max_score = 250

            for deelnemer in (RegioCompetitieSchutterBoog
                              .objects
                              .filter(deelcompetitie=deelcomp)
                              .select_related('schutterboog')
                              .prefetch_related('scores')
                              .all()):

                pk = deelnemer.schutterboog.pk
                scores = list()
                found = False
                try:
                    scores.extend(self.pk2scores[pk])
                    found = True
                except KeyError:
                    pass

                try:
                    scores.extend(self.pk2scores_alt[pk])
                    found = True
                except KeyError:
                    pass

                if found:
                    # tot nu toe hebben we de verwijderde scores meegenomen
                    # zodat we deze change-trigger krijgen.
                    # Nu moeten de verwijderde scores eruit
                    scores = [score for score in scores if score.waarde != SCORE_WAARDE_VERWIJDERD]

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

                    try:
                        scores = self.pk2scores[pk]
                    except KeyError:
                        waardes = list()
                    else:
                        # door waarde te filteren op max_score voorkomen we problemen met het gemiddelde
                        # die pas naar boven komen tijdens de save()
                        waardes = [score.waarde for score in scores if score.waarde <= max_score]

                    waardes.extend([0, 0, 0, 0, 0, 0, 0])
                    waardes = waardes[:7]
                    deelnemer.score1 = waardes[0]
                    deelnemer.score2 = waardes[1]
                    deelnemer.score3 = waardes[2]
                    deelnemer.score4 = waardes[3]
                    deelnemer.score5 = waardes[4]
                    deelnemer.score6 = waardes[5]
                    deelnemer.score7 = waardes[6]
                    deelnemer.laagste_score_nr, laagste = self._bepaal_laagste_nr(waardes)
                    deelnemer.gemiddelde, deelnemer.totaal = self._bepaal_gemiddelde_en_totaal(waardes, laagste, pijlen_per_ronde)

                    try:
                        scores = self.pk2scores_alt[pk]
                    except KeyError:
                        waardes = list()
                    else:
                        # door waarde te filteren op max_score voorkomen we problemen met het gemiddelde
                        # die pas naar boven komen tijdens de save()
                        waardes = [score.waarde for score in scores if score.waarde != SCORE_WAARDE_VERWIJDERD]

                    waardes.extend([0, 0, 0, 0, 0, 0, 0])
                    waardes = waardes[:7]
                    deelnemer.alt_score1 = waardes[0]
                    deelnemer.alt_score2 = waardes[1]
                    deelnemer.alt_score3 = waardes[2]
                    deelnemer.alt_score4 = waardes[3]
                    deelnemer.alt_score5 = waardes[4]
                    deelnemer.alt_score6 = waardes[5]
                    deelnemer.alt_score7 = waardes[6]
                    deelnemer.alt_laagste_score_nr, laagste = self._bepaal_laagste_nr(waardes)
                    deelnemer.alt_gemiddelde, deelnemer.alt_totaal = self._bepaal_gemiddelde_en_totaal(waardes, laagste, pijlen_per_ronde)

                    deelnemer.save()
                    count += 1
        # for
        self.stdout.write('[INFO] Scores voor %s schuttersboog bijgewerkt' % count)

    def _update_tussenstand(self):
        # stap 1: alle RegioCompetitieSchutterBoog.scores vaststellen

        begin = datetime.datetime.now()

        self.pk2scores = dict()      # [schutterboog.pk] = [score, score, ..]
        self.pk2scores_alt = dict()

        self._vind_scores()

        # stap 2: overige velden bijwerken van aangepaste RegioCompetitieSchutterBoog
        self._update_regiocompetitieschuttersboog()

        klaar = datetime.datetime.now()

        self.stdout.write('[INFO] Tussenstand bijgewerkte in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_scores(self):

        # monitor voor nieuwe ScoreHist
        hist_count = 0      # moet 0 zijn: beschermd tegen query op lege scorehist tabel
        now = datetime.datetime.now()
        while now < self.stop_at:
            new_count = ScoreHist.objects.count()
            if new_count != hist_count:
                hist_count = new_count
                self._update_tussenstand()
                now = datetime.datetime.now()

            # sleep at least 5 seconds, then check again
            secs = (self.stop_at - now).total_seconds()
            if secs > 0:
                secs = min(secs, 5.0)
                time.sleep(secs)

            now = datetime.datetime.now()
        # while

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 30 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self.stop_at = (datetime.datetime.now()
                        + datetime.timedelta(minutes=duration)
                        - datetime.timedelta(seconds=30))

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):
        self._set_stop_time(**options)

        if options['all']:
            self.taken.hoogste_scorehist = None

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_scores()
        except django.db.utils.DataError as exc:        # pragma: no coverage
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
        except KeyboardInterrupt:                       # pragma: no coverage
            pass

        self.stdout.write('Klaar')

# end of file
