# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core.management.base import BaseCommand
from Competitie.models import Competitie, RegioCompetitieSchutterBoog, AG_NUL
from Competitie.operations.klassengrenzen import KlasseBepaler
from Sporter.models import Sporter, SporterBoog
from Score.models import ScoreHist, Score, SCORE_TYPE_INDIV_AG, SCORE_TYPE_TEAM_AG
from decimal import Decimal


class Command(BaseCommand):
    help = "Ingeschreven sporter + scores + klasse aanpassen naar een ander boogtype"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Voorgestelde wijzigingen opslaan')
        parser.add_argument('lid_nr', type=int, help='Bondsnummer')
        parser.add_argument('boog', type=str, help='Boogtype afkorting (R/C/BB/IB/LB)')
        parser.add_argument('afstand', type=int, help='Competitie afstand (18/25)')

    def handle(self, *args, **options):
        lid_nr = options['lid_nr']
        boog_afk = options['boog'].upper()
        afstand = options['afstand']
        do_save = options['commit']

        if boog_afk not in ('R', 'C', 'BB', 'IB', 'LB'):
            self.stderr.write('Onbekend boog type: %s' % repr(options['boog']))
            return

        # er kunnen meerdere competities actief zijn
        # neem de competitie
        try:
            comp = (Competitie
                    .objects
                    .get(afstand=afstand,
                         is_afgesloten=False,
                         klassengrenzen_vastgesteld=True))
        except Competitie.DoesNotExist:
            self.stderr.write('[ERROR] Kan de competitie niet vinden')
            return

        self.stdout.write('[INFO] Geselecteerde competitie: %s' % comp)

        try:
            sporter = (Sporter
                       .objects
                       .select_related('bij_vereniging',
                                       'bij_vereniging__regio')
                       .get(lid_nr=lid_nr))
        except Sporter.DoesNotExist:
            self.stderr.write('[ERROR] Sporter met %s niet gevonden' % lid_nr)
            return

        self.stdout.write('[INFO] Sporter %s is van vereniging %s in regio %s' % (
                        sporter.lid_nr_en_volledige_naam(),
                        sporter.bij_vereniging,
                        sporter.bij_vereniging.regio.regio_nr))

        # check de voorkeuren
        juiste_sporterboog = None
        wedstrijd_bogen = list()
        for sporterboog in (SporterBoog
                            .objects
                            .filter(sporter__lid_nr=lid_nr,
                                    voor_wedstrijd=True)
                            .select_related('boogtype')):
            afk = sporterboog.boogtype.afkorting
            wedstrijd_bogen.append(afk)
            if afk == boog_afk:
                juiste_sporterboog = sporterboog
        # for

        if len(wedstrijd_bogen) == 0:
            self.stderr.write('[ERROR] Sporter heeft geen wedstrijd boog als voorkeur')
            return

        if not juiste_sporterboog:
            self.stderr.write('[ERROR] Sporter heeft boog %s niet als voorkeur. Wel: %s' % (boog_afk, ", ".join(wedstrijd_bogen)))
            return

        # controleer dat de sporter niet al geschreven
        count = (RegioCompetitieSchutterBoog
                 .objects
                 .filter(deelcompetitie__competitie=comp,
                         sporterboog=juiste_sporterboog)
                 .count())
        if count > 0:
            self.stderr.write('[ERROR] Sporter is al ingeschreven met dat boog type')
            return

        # sporter heeft de nieuwe boog als voorkeur voor wedstrijden
        # juiste sporterboog is nog niet ingeschreven voor de competitie

        deelnemer = (RegioCompetitieSchutterBoog
                     .objects
                     .select_related('sporterboog',
                                     'sporterboog__boogtype')
                     .get(deelcompetitie__competitie=comp,
                          sporterboog__sporter__lid_nr=lid_nr))
        huidige_boog_afk = deelnemer.sporterboog.boogtype.afkorting
        self.stdout.write('[INFO] Huidige deelnemer pk = %s' % deelnemer.pk)
        self.stdout.write('[INFO] Huidige sporterboog pk = %s, boogtype = %s' % (deelnemer.sporterboog.pk, huidige_boog_afk))
        self.stdout.write('[INFO] Huidige klasse: %s' % deelnemer.klasse)

        # controleer of de sporter in een team mee doet
        if deelnemer.regiocompetitieteam_set.count() > 0:
            self.stderr.write('[ERROR] Huidige deelnemer is deel van een team')
            return

        score_pks = list()
        score_waardes = list()
        for scorehist in (ScoreHist
                          .objects
                          .select_related('score')
                          .filter(score__sporterboog=deelnemer.sporterboog)
                          .order_by('when')):      # oudste eerst
            score = scorehist.score
            ag = Decimal(score.waarde) / Decimal(1000)
            if score.type == SCORE_TYPE_INDIV_AG:
                self.stdout.write("[INFO] Boog %s: Individueel AG: %1.3f" % (huidige_boog_afk, float(ag)))
            elif score.type == SCORE_TYPE_TEAM_AG:
                pass
            else:
                # echte score
                self.stdout.write('[INFO] Boog %s: Score (pk=%s) %s neergezet op %s' % (huidige_boog_afk, score.pk, score.waarde, scorehist.when))
                score_pks.append(score.pk)
                if score.waarde > 0:
                    score_waardes.append(score.waarde)
        # for

        self.stdout.write('[INFO] Juiste sporterboog pk = %s' % juiste_sporterboog.pk)

        juiste_ag = AG_NUL
        score_gevonden = False
        for scorehist in (ScoreHist.objects.select_related('score').filter(score__sporterboog=juiste_sporterboog)):
            score = scorehist.score
            ag = Decimal(score.waarde) / Decimal(1000)
            if score.type == SCORE_TYPE_INDIV_AG:
                self.stdout.write("[INFO] Boog %s: Individueel AG: %1.3f" % (boog_afk, float(ag)))
                juiste_ag = ag
            elif score.type == SCORE_TYPE_TEAM_AG:
                pass
            else:
                # echte score
                score_gevonden = True
                self.stdout.write('[INFO] Boog %s: Score (pk=%s) %s neergezet op %s' % (boog_afk, score.pk, score.waarde, scorehist.when))
        # for

        if score_gevonden:
            self.stderr.write('[ERROR] Onverwacht een score gevonden')
            return

        self.stdout.write('[INFO] Juiste individuele AG: %1.3f' % float(juiste_ag))

        # pas de AG's, klasse en sporterboog aan van deze deelnemer
        deelnemer.sporterboog = juiste_sporterboog
        deelnemer.ag_voor_indiv = deelnemer.ag_voor_team = juiste_ag
        deelnemer.ag_voor_team_mag_aangepast_worden = (juiste_ag > AG_NUL)

        # bepaal de nieuwe klasse
        bepaler = KlasseBepaler(comp)
        bepaler.bepaal_klasse_deelnemer(deelnemer)
        self.stdout.write('[INFO] Nieuwe klasse: %s' % deelnemer.klasse)

        if not do_save:
            self.stdout.write('\nGebruik --commit om wijziging door te voeren')
            return

        deelnemer.save()

        # scores overzetten naar de juiste sporterboog
        for score in Score.objects.filter(pk__in=score_pks):
            score.sporterboog = juiste_sporterboog
            score.save(update_fields=['sporterboog'])
        # for

        self.stdout.write('[INFO] Deelnemer pk=%s is aangepast; scores zijn omgezet naar sporterboog pk=%s' % (deelnemer.pk, juiste_sporterboog.pk))

# end of file
