# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# werk de tussenstand bij voor deelcompetities die niet afgesloten zijn
# zodra er nieuwe ScoreHist records zijn

from django.core.management.base import BaseCommand
from django.db.models import F
import django.db.utils
from Competitie.models import (CompetitieTaken, CompetitieKlasse,
                               LAAG_REGIO, Competitie, DeelCompetitie, DeelcompetitieRonde,
                               RegioCompetitieSchutterBoog, KampioenschapSchutterBoog)
from Score.models import ScoreHist, SCORE_WAARDE_VERWIJDERD
import datetime
import time


class Command(BaseCommand):
    help = "Competitie tussenstand bijwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.stop_at = 0

        self.taken = CompetitieTaken.objects.all()[0]

        self.pk2scores = dict()         # [RegioCompetitieSchutterBoog.pk] = [tup, ..] with tup = (afstand, score)
        self.pk2scores_alt = dict()

        self._onbekend2beter = dict()   # [competitieklasse.pk] = [klasse, ..] met oplopend AG

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--all', action='store_true')       # alles opnieuw vaststellen
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_overstappers_regio(self, comp):
        objs = (RegioCompetitieSchutterBoog
                .objects
                .select_related('bij_vereniging',
                                'bij_vereniging__regio',
                                'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging',
                                'schutterboog__nhblid__bij_vereniging__regio')
                .exclude(bij_vereniging=F('schutterboog__nhblid__bij_vereniging')))   # bevat geen uitstappers
        for obj in objs:
            lid = obj.schutterboog.nhblid
            # het lijkt erop dat lid.bij_vereniging == None niet voor kan komen
            self.stdout.write('[INFO] Verwerk overstap %s: [%s] %s --> [%s] %s' % (
                              lid.nhb_nr,
                              obj.bij_vereniging.regio.regio_nr, obj.bij_vereniging,
                              lid.bij_vereniging.regio.regio_nr, lid.bij_vereniging))
            if obj.bij_vereniging.regio != lid.bij_vereniging.regio:
                # overschrijven naar andere deelcompetitie
                obj.deelcompetitie = DeelCompetitie.objects.get(competitie=obj.deelcompetitie.competitie,
                                                                nhb_regio=lid.bij_vereniging.regio)
            obj.bij_vereniging = lid.bij_vereniging
            obj.save()
        # for

    def _verwerk_overstappers_rk(self, comp):
        # ondersteuning om een overschrijving af te ronden
        # schutters die eerder geen vereniging hebben en wel een vereniging
        objs = (KampioenschapSchutterBoog
                .objects
                .select_related('deelcompetitie__nhb_rayon',
                                'schutterboog__nhblid',
                                'schutterboog__nhblid__bij_vereniging',
                                'schutterboog__nhblid__bij_vereniging__regio__rayon')
                .filter(bij_vereniging__isnull=True))
        for obj in objs:
            # schutter had geen vereniging; nu wel
            # alleen overnemen als de nieuwe vereniging in het juiste rayon zit
            ver = obj.schutterboog.nhblid.bij_vereniging
            if ver:
                if ver.regio.rayon.rayon_nr != obj.deelcompetitie.nhb_rayon.rayon_nr:
                    self.stdout.write('[WARNING] Verwerk overstap naar ander rayon niet mogelijk voor %s in RK voor rayon %s: GEEN VERENIGING --> [%s] %s' % (
                                      obj.schutterboog.nhblid.nhb_nr,
                                      obj.deelcompetitie.nhb_rayon.rayon_nr,
                                      ver.regio.regio_nr, ver))
                else:
                    # pas de 'bij_vereniging' aan
                    self.stdout.write('[INFO] Verwerk overstap %s: GEEN VERENIGING --> [%s] %s' % (
                                      obj.schutterboog.nhblid.nhb_nr,
                                      ver.regio.regio_nr, ver))
                    obj.bij_vereniging = ver
                    obj.save()
        # for

    def _verwerk_overstappers(self):
        """ Deze functie verwerkt schutters die overgestapt zijn naar een andere vereniging
            Deze worden overgeschreven naar een andere deelcompetitie (regio/RK/BK).
        """

        # 1. NhbLid.bij_vereniging komt overeen met informatie uit CRM

        # 2. Schutters in regiocompetitie kunnen elk moment overstappen
        #    RegioCompetitieSchutterBoog.bij_vereniging
        # TODO: voor de teamcompetitie moet dit pas gebeuren nadat de teamscores vastgesteld zijn

        # 3. Bij vaststellen RK/BK deelname/reserve wordt vereniging bevroren
        #    KampioenschapSchutterBoog.bij_vereniging

        for comp in Competitie.objects.filter(is_afgesloten=False):
            comp.bepaal_fase()
            if comp.fase <= 'F':        # Regiocompetitie
                self._verwerk_overstappers_regio(comp)
                # uitstappers kijken we niet meer naar -> gewoon op oude vereniging houden
            elif comp.fase == 'K':      # RK
                self._verwerk_overstappers_rk(comp)
        # for

    def _prep_caches(self):
        # maak een structuur om gerelateerde IndivWedstrijdklassen te vinden
        indiv_alike = dict()     # [(boogtype.pk, leeftijdsklasse.pk, ...)] = [indiv, ..]
        klassen_qset = (CompetitieKlasse
                        .objects
                        .select_related('competitie', 'indiv', 'indiv__boogtype')
                        .prefetch_related('indiv__leeftijdsklassen')
                        .filter(team=None)
                        .exclude(indiv__buiten_gebruik=True))

        for obj in klassen_qset:
            indiv = obj.indiv
            if not indiv.is_onbekend:
                tup = (indiv.boogtype.pk,)
                tup += tuple(indiv.leeftijdsklassen.values_list('pk', flat=True))
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
                tup += tuple(klasse.indiv.leeftijdsklassen.values_list('pk', flat=True))

                for indiv in indiv_alike[tup]:
                    # zoek klasse met deze indiv
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
            Vult pk2scores en pk2scores_alt.
        """
        self.pk2scores = dict()
        self.pk2scores_alt = dict()

        scorehist_latest = ScoreHist.objects.latest('pk')
        # als hierna een extra ScoreHist aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

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
            is_alt = ronde.is_voor_import_oude_programma()

            # tijdelijk: de geïmporteerde uitslagen zijn de normale
            #            de handmatig ingevoerde scores zijn het alternatief
            is_alt = not is_alt     # FUTURE: schakelaar omzetten als we geen import meer doen

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
                                  .select_related('schutterboog')
                                  .all()):
                        tup = (uitslag.afstand_meter, score)
                        pk = score.schutterboog.pk
                        if pk in allowed_schutterboog_pks:   # presumed better than huge __in
                            pk2scores = self.pk2scores_alt if is_alt else self.pk2scores
                            try:
                                pk2scores[pk].append(tup)
                            except KeyError:
                                pk2scores[pk] = [tup]
                    # for
            # for
        # for

        self.stdout.write('[INFO] Aantallen: pk2scores=%s, pk2scores_alt=%s' % (
                               len(self.pk2scores), len(self.pk2scores_alt)))

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
                comp_afstand = 18
            else:
                pijlen_per_ronde = 25
                max_score = 250
                comp_afstand = 25

            for deelnemer in (RegioCompetitieSchutterBoog
                              .objects
                              .filter(deelcompetitie=deelcomp)
                              .select_related('schutterboog')
                              .prefetch_related('scores')
                              .all()):

                pk = deelnemer.schutterboog.pk
                tups = list()
                found = False
                try:
                    tups.extend(self.pk2scores[pk])
                    found = True
                except KeyError:
                    pass

                try:
                    tups.extend(self.pk2scores_alt[pk])
                    found = True
                except KeyError:
                    pass

                if found:
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

                    try:
                        tups = self.pk2scores[pk]
                    except KeyError:
                        waardes = list()
                    else:
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
                    deelnemer.gemiddelde, deelnemer.totaal = self._bepaal_gemiddelde_en_totaal(waardes, laagste, pijlen_per_ronde)

                    # kijk of verplaatsing uit klasse onbekend van toepassing is
                    if deelnemer.aanvangsgemiddelde < 0.001:        # TODO: verander is heeft_automatisch_ag
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
                                                deelnemer.schutterboog.nhblid.nhb_nr, klasse.competitie.afstand, new_ag, klasse))
                                        deelnemer.klasse = klasse
                                        break
                                # for

                    try:
                        tups = self.pk2scores_alt[pk]
                    except KeyError:
                        waardes = list()
                    else:
                        # door waarde te filteren op max_score voorkomen we problemen
                        # die anders pas naar boven komen tijdens de save()
                        waardes = [score.waarde for afstand, score in tups if score.waarde != SCORE_WAARDE_VERWIJDERD and afstand == comp_afstand]

                    waardes.extend([0, 0, 0, 0, 0, 0, 0])
                    waardes = waardes[:7]
                    deelnemer.alt_score1 = waardes[0]
                    deelnemer.alt_score2 = waardes[1]
                    deelnemer.alt_score3 = waardes[2]
                    deelnemer.alt_score4 = waardes[3]
                    deelnemer.alt_score5 = waardes[4]
                    deelnemer.alt_score6 = waardes[5]
                    deelnemer.alt_score7 = waardes[6]
                    deelnemer.alt_aantal_scores = len(waardes) - waardes.count(0)
                    deelnemer.alt_laagste_score_nr, laagste = self._bepaal_laagste_nr(waardes)
                    deelnemer.alt_gemiddelde, deelnemer.alt_totaal = self._bepaal_gemiddelde_en_totaal(waardes, laagste, pijlen_per_ronde)

                    deelnemer.save()
                    count += 1
        # for
        self.stdout.write('[INFO] Scores voor %s schuttersboog bijgewerkt' % count)

    def _update_tussenstand(self):
        begin = datetime.datetime.now()

        # stap 1: alle RegioCompetitieSchutterBoog.scores vaststellen
        self._vind_scores()

        # stap 2: overige velden bijwerken van aangepaste RegioCompetitieSchutterBoog
        self._update_regiocompetitieschuttersboog()

        klaar = datetime.datetime.now()
        self.stdout.write('[INFO] Tussenstand bijgewerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_scores(self):
        # monitor voor nieuwe ScoreHist
        hist_count = 0      # moet 0 zijn: beschermd tegen query op lege scorehist tabel
        now = datetime.datetime.now()
        while now < self.stop_at:               # pragma: no branch
            new_count = ScoreHist.objects.count()
            if new_count != hist_count:
                hist_count = new_count
                self._update_tussenstand()
                now = datetime.datetime.now()

            # sleep at least 5 seconds, then check again
            secs = (self.stop_at - now).total_seconds()
            if secs > 5:                    # pragma: no branch
                secs = min(secs, 5.0)
                time.sleep(secs)
            else:
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
        self._set_stop_time(**options)

        if options['all']:
            self.taken.hoogste_scorehist = None

        self._verwerk_overstappers()

        self._prep_caches()

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_scores()
        except django.db.utils.DataError as exc:        # pragma: no coverage
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
        except KeyboardInterrupt:                       # pragma: no coverage
            pass

        self.stdout.write('Klaar')

# end of file
