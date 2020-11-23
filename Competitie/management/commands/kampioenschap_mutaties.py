# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# werk de tussenstand bij voor deelcompetities die niet afgesloten zijn
# zodra er nieuwe ScoreHist records zijn

from django.core.management.base import BaseCommand
from django.db.models import F
import django.db.utils
from Competitie.models import (CompetitieTaken, DeelCompetitie, LAAG_RK, LAAG_BK,
                               DeelcompetitieKlasseLimiet, KampioenschapSchutterBoog,
                               KampioenschapMutatie, MUTATIE_INITIEEL, MUTATIE_CUT,
                               MUTATIE_AANMELDEN, MUTATIE_AFMELDEN)
import datetime
import time


class Command(BaseCommand):
    help = "Competitie kampioenschap mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.stop_at = datetime.datetime.now()

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

    def _update_rank_nummers(self, deelcomp, klasse):
        #self.stdout.write('[DEBUG] Updated ranking:')
        rank = 0
        for obj in (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse)
                    .order_by('volgorde')):
            if obj.is_afgemeld:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank
            obj.save()
            # self.stdout.write('  rank=%s, volgorde=%s, nhb_nr=%s, gem=%s, afgemeld=%s, label=%s' % (
            #                     obj.rank, obj.volgorde, obj.schutterboog.nhblid.nhb_nr, obj.gemiddelde, obj.is_afgemeld, obj.kampioen_label))
        # for

    def _kampioenschap_bepaal_deelnemers(self, deelcomp, klasse):
        """
            Bepaal de top-X deelnemers voor een klasse van een kampioenschap:
                De niet-afgemelde kampioenen
                aangevuld met de niet-afgemelde schutters met hoogste gemiddelde
                gesorteerde op gemiddelde

            Deze functie wordt gebruikt na het vaststellen van de initiële deelnemers
            en na het aanpassen van de cut.
        """

        self.stdout.write('[INFO] Bepaal deelnemers in klasse %s van %s' % (klasse, deelcomp))

        limiet = self._get_limiet(deelcomp, klasse)

        # kampioenen mogen altijd meedoen, ook als de cut omlaag gaat
        kampioenen = (KampioenschapSchutterBoog
                      .objects
                      .exclude(kampioen_label='')
                      .filter(deelcompetitie=deelcomp,
                              klasse=klasse))

        lijst = list()
        aantal = 0
        for obj in kampioenen:
            if not obj.is_afgemeld:
                aantal += 1
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
        # for

        # aanvullen met schutters tot aan de cut
        objs = (KampioenschapSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        klasse=klasse)
                .order_by('kampioen_label',     # kampioenen eerst
                          '-gemiddelde'))

        for obj in objs:
            if not obj.kampioen_label != "":
                tup = (obj.gemiddelde, len(lijst), obj)
                lijst.append(tup)
                if not obj.is_afgemeld:
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

            if obj.is_afgemeld:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank
            obj.save()
            pks.append(obj.pk)
        # for

        # geef nu alle andere schutters en nieuw volgnummer
        # dit voorkomt dubbele volgnummers als de cut omlaag gezet is
        for obj in objs:
            if obj.pk not in pks:
                volgorde += 1
                obj.volgorde = volgorde

                if obj.is_afgemeld:
                    obj.rank = 0
                else:
                    rank += 1
                    obj.rank = rank
                obj.save()
        # for

    def _verwerk_mutatie_initieel_deelcomp(self, deelcomp):
        # bepaal alle wedstrijdklassen aan de hand van de ingeschreven schutters
        for deelnemer in (KampioenschapSchutterBoog
                          .objects
                          .filter(deelcompetitie=deelcomp)
                          .distinct('klasse')):

            # sorteer de lijst op gemiddelde en bepaalde volgorde
            self._kampioenschap_bepaal_deelnemers(deelcomp, deelnemer.klasse)
        # for

    def _verwerk_mutatie_initieel(self, deelnemer):
        # bepaal de volgorde en rank van de deelnemers
        # in alle klassen van de RK deelcompetities

        # via deelnemer kunnen we bepalen over welke kampioenschappen dit gaat
        if deelnemer.deelcompetitie.laag == LAAG_RK:
            for deelcomp_rk in (DeelCompetitie
                                .objects
                                .filter(competitie=deelnemer.deelcompetitie.competitie,
                                        laag=LAAG_RK)):
                self._verwerk_mutatie_initieel_deelcomp(deelcomp_rk)
            # for
        else:
            deelcomp_bk = (DeelCompetitie
                           .objects
                           .get(competitie=deelnemer.deelcompetitie.competitie,
                                laag=LAAG_BK))
            self._verwerk_mutatie_initieel_deelcomp(deelcomp_bk)

    def _verwerk_mutatie_afmelden(self, deelnemer):
        # pas alleen de ranking aan voor alle schutters in deze klasse
        # de deelnemer is al afgemeld en behoudt zijn volgorde zodat de RKO/BKO
        # 'm in grijs kan zien in de tabel

        # bij een mutatie "boven de cut" wordt de schutter bovenaan de lijst van reserve schutters
        # tot deelnemer gepromoveerd. Zijn gemiddelde bepaalt de volgorde

        deelnemer.is_afgemeld = True
        deelnemer.save()

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
                    reserve.save()

                    # schuif de andere schutters omlaag
                    slechter.update(volgorde=F('volgorde') + 1)
                # else: geen schutters om op te schuiven

        self._update_rank_nummers(deelcomp, klasse)

    def _opnieuw_aanmelden(self, deelnemer):
        # meld de deelnemer opnieuw aan door hem bij de reserves te zetten

        deelcomp = deelnemer.deelcompetitie
        klasse = deelnemer.klasse
        oude_volgorde = deelnemer.volgorde

        limiet = self._get_limiet(deelcomp, klasse)

        # 1) zoek de plek waar de deelnemer ingestopt moet worden

        if deelnemer.kampioen_label != "":
            # een kampioen die zich opnieuw aanmeldt mag bovenaan in de lijst van reserve-schutters
            # daar kunnen nog meer kampioenen staan, dus daarna op gemiddelde
            objs = (KampioenschapSchutterBoog
                    .objects
                    .exclude(kampioen_label='')
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
                            rank__gt=limiet,
                            gemiddelde__gt=deelnemer.gemiddelde)
                    .order_by('gemiddelde'))

            if len(objs):
                # na deze kampioen op de reserve-lijst
                nieuwe_rank = objs[0].rank + 1
            else:
                # boven aan de reserve lijst
                nieuwe_rank = limiet + 1

            # 2) maak een plekje door de andere deelnemers op te schuiven
            objs = (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
                            rank__gte=nieuwe_rank))

            if len(objs) > 0:
                obj = objs.order_by('volgorde')[0]
                nieuwe_volgorde = obj.volgorde
                objs.update(volgorde=F('volgorde') + 1)
            else:
                # niemand om op te schuiven - zet aan het einde
                nieuwe_volgorde = (KampioenschapSchutterBoog
                                   .objects
                                   .filter(deelcompetitie=deelcomp,
                                           klasse=klasse)
                                   .count()) + 1
        else:
            # zoek alle reserve schutters met een beter gemiddelde
            objs = (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelnemer.deelcompetitie,
                            klasse=deelnemer.klasse,
                            rank__gt=limiet,                      # na de cut
                            gemiddelde__gt=deelnemer.gemiddelde)  # beter dan in te voegen schutter
                    .order_by('gemiddelde'))

            self.stdout.write('[DEBUG] reserve-schutters:')
            for obj in objs:
                self.stdout.write('    obj: rank=%s, volgorde=%s, nhbnr=%s, gemiddelde=%s' % (
                    obj.rank, obj.volgorde, obj.schutterboog.nhblid.nhb_nr, obj.gemiddelde))

            if len(objs) > 0:
                # na deze kampioen op de reserve-lijst
                nieuwe_volgorde = objs[0].volgorde + 1
            else:
                # bovenaan de reserve lijst
                self.stdout.write('[DEBUG] bovenaan de reserve-lijst')
                try:
                    obj = (KampioenschapSchutterBoog
                           .objects
                           .get(deelcompetitie=deelcomp,
                                klasse=klasse,
                                rank=limiet + 1))
                except KampioenschapSchutterBoog.DoesNotExist:
                    # er zijn te weinig schutters
                    # zet de schutter aan het einde van de lijst
                    self.stdout.write('[DEBUG] TODO: te weinig schutters')
                    pass
                else:
                    nieuwe_volgorde = obj.volgorde

            # 2) maak een plekje door de andere deelnemers op te schuiven
            objs = (KampioenschapSchutterBoog
                    .objects
                    .filter(deelcompetitie=deelcomp,
                            klasse=klasse,
                            volgorde__gte=nieuwe_volgorde))

            objs.update(volgorde=F('volgorde') + 1)

        deelnemer.volgorde = nieuwe_volgorde
        deelnemer.is_afgemeld = False
        deelnemer.deelname_bevestigd = True
        deelnemer.save()

        # 3) verwijder deelnemer uit de lijst, schuif de rest omhoog
        qset = (KampioenschapSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        klasse=klasse,
                        volgorde__gt=oude_volgorde))
        qset.update(volgorde=F('volgorde') - 1)

        # 4) deel de rank nummers opnieuw uit
        self._update_rank_nummers(deelcomp, klasse)

    def _verwerk_mutatie_aanmelden(self, deelnemer):
        if not deelnemer.deelname_bevestigd:
            if deelnemer.is_afgemeld:
                self._opnieuw_aanmelden(deelnemer)
            else:
                deelnemer.deelname_bevestigd = True
                deelnemer.save()
                # verder hoeven we niets te doen: volgorde en rank blijft hetzelfde

    def _verwerk_mutatie_cut(self, deelnemer):
        # de cut is aangepast, dus herhaal de methode die initieel gebruikt is
        # zodat de regiokampioenen gegarandeerd deelnemer
        self._kampioenschap_bepaal_deelnemers(deelnemer.deelcompetitie, deelnemer.klasse)

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.mutatie

        if code == MUTATIE_INITIEEL:
            self.stdout.write('[INFO] Verwerk mutatie %s: initieel' % mutatie.pk)
            self._verwerk_mutatie_initieel(mutatie.deelnemer)
        elif code == MUTATIE_CUT:
            self.stdout.write('[INFO] Verwerk mutatie %s: aangepaste limiet (cut)' % mutatie.pk)
            self._verwerk_mutatie_cut(mutatie.deelnemer)
        elif code == MUTATIE_AANMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: aanmelden' % mutatie.pk)
            self._verwerk_mutatie_aanmelden(mutatie.deelnemer)
        elif code == MUTATIE_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: afmelden' % mutatie.pk)
            self._verwerk_mutatie_afmelden(mutatie.deelnemer)
        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s door %s (pk=%s)' % (code, mutatie.door, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = KampioenschapMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self.taken.hoogste_mutatie:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste KampioenschapMutatie pk is %s' % self.taken.hoogste_mutatie.pk)
            qset = (KampioenschapMutatie
                    .objects
                    .filter(pk__gt=self.taken.hoogste_mutatie.pk))
        else:
            qset = (KampioenschapMutatie
                    .objects
                    .all())

        mutatie_pks = qset.values_list('pk', flat=True)

        self.taken.hoogste_mutatie = mutatie_latest
        self.taken.save(update_fields=['hoogste_mutatie'])
        self.stdout.write('[INFO] nieuwe hoogste KampioenschapMutatie pk is %s' % self.taken.hoogste_mutatie.pk)

        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            mutatie = (KampioenschapMutatie
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
        # for

        klaar = datetime.datetime.now()
        self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe ScoreHist
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:
            # self.stdout.write('tick')
            new_count = KampioenschapMutatie.objects.count()
            if new_count != mutatie_count:
                mutatie_count = new_count
                self._verwerk_nieuwe_mutaties()
                now = datetime.datetime.now()

            # sleep at least 1 second, then check again
            secs = (self.stop_at - now).total_seconds()
            if secs > 1:                    # pragma: no branch
                time.sleep(0.5)
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

        self.stdout.write('Klaar')

# end of file
