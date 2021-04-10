# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# import the data van de oude site die opgeslagen staat in de .json file

from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from django.conf import settings
from BasisTypen.models import BoogType, TeamType
from NhbStructuur.models import NhbLid, NhbVereniging
from Logboek.models import schrijf_in_logboek
from Competitie.models import (Competitie, CompetitieKlasse,
                               LAAG_REGIO, DeelCompetitie, DeelcompetitieRonde,
                               AG_NUL, RegioCompetitieSchutterBoog, RegiocompetitieTeam)
from Schutter.models import SchutterBoog
from Wedstrijden.models import CompetitieWedstrijd, CompetitieWedstrijdUitslag, WedstrijdenPlan
from Score.models import Score, ScoreHist, SCORE_TYPE_SCORE, SCORE_TYPE_INDIV_AG
from decimal import Decimal
import datetime
import json
import sys
import os


class Command(BaseCommand):
    help = "Data van de oude site overnemen"

    JSON_FILE = 'oude_site.json'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._afstand = 0
        self._comp = None
        self._klasse = None
        self._boogtype = None
        self._dryrun = False
        self._count_errors = 0
        self._count_warnings = 0
        self._warnings = list()            # al geroepen warnings
        self._meld_afwijking_lid = list()

        # datum/tijd stempel voor alle nieuwe ScoreHist
        self._import_when = None

        # wordt opgezet door _prep_regio2deelcomp_regio2ronde2uitslag
        self._regio2deelcomp = None        # [regio_nr] = DeelCompetitie
        self._regio2ronde2uitslag = None   # [regio_nr] = [1..7] = WedstrijdUitslag
        self._uitslag2wedstrijd = dict()   # [uitslag.pk] = Wedstrijd
        self._wedstrijd2ronde = dict()     # [wedstrijd.pk] = DeelcompetitieRonde

        self._ingelezen = list()           # tuple(afstand, nhbnr, boogtype, score1, ..., score 7)
        self._verwijder_r_18 = list()
        self._verwijder_r_25 = list()
        self._verwijder = None             # wijst naar _verwijder_r_18 of _verwijder_r_25, afhankelijk van afstand

        self._cache_boogtype = dict()      # [afkorting] = BoogType
        self._cache_teamtype = dict()      # [afkorting] = TeamType
        self._cache_klasse = dict()        # [competitie.pk, klasse_beschrijving] = CompetitieKlasse
        self._cache_nhblid = dict()        # [nhbnr] = NhbLid
        self._cache_nhbver = dict()        # [ver_nr] = NhbVereniging
        self._cache_schutterboog = dict()  # [(nhblid, afkorting)] = SchutterBoog
        self._cache_inschrijving = dict()  # [(comp.pk, schutterboog.pk)] = RegioCompetitieSchutterBoog
        self._cache_ag_score = dict()      # [(afstand, schutterboog.pk)] = Score
        self._cache_scores = dict()        # [(inschrijving.pk, ronde.pk)] = score
        self._cache_teams = dict()         # [(afstand, ver_nr, team_naam)] = RegiocompetitieTeam   (met team_naam = "R-1098-1")

        self._prev_hash = dict()           # [fname] = hash

        self._bulk_score = list()
        self._bulk_hist = list()
        self._bulk_uitslag = dict()        # [uitslag] = [score, ...]
        self._pk2uitslag = dict()          # [uitslag.pk] = WedstrijdUitslag

        self._gezocht_99 = list()
        self._nhbnr_uit_99nr = list()
        self._nhbnr_scores = dict()

    def _roep_warning(self, msg):
        # print en tel waarschuwingen
        # en onderdruk dubbele berichten
        if msg not in self._warnings:
            self._warnings.append(msg)
            self._count_warnings += 1
            self.stdout.write('[WARNING] ' + msg)

    def _roep_info(self, msg):
        self.stdout.write('[INFO] ' + msg)

    def _prep_caches(self):
        # bouw caches om herhaaldelijke database toegang te voorkomen, voor performance

        for obj in BoogType.objects.all():
            self._cache_boogtype[obj.afkorting] = obj
        # for

        for obj in TeamType.objects.all():
            self._cache_teamtype[obj.afkorting] = obj
        # for

        for obj in (CompetitieKlasse
                    .objects
                    .select_related('competitie', 'indiv')
                    .filter(indiv__buiten_gebruik=False,
                            team=None)):
            tup = (obj.competitie.pk, obj.indiv.beschrijving.lower())
            self._cache_klasse[tup] = obj
        # for

        for obj in (NhbLid
                    .objects
                    .select_related('bij_vereniging',
                                    'bij_vereniging__regio')
                    .all()):
            obj.volledige_naam_str = obj.volledige_naam()
            self._cache_nhblid[obj.nhb_nr] = obj
        # for

        for obj in NhbVereniging.objects.all():
            self._cache_nhbver[obj.ver_nr] = obj
        # for

        for obj in (SchutterBoog
                    .objects
                    .select_related('nhblid', 'boogtype')
                    .all()):
            tup = (obj.nhblid.nhb_nr, obj.boogtype.afkorting)
            self._cache_schutterboog[tup] = obj
        # for

        afstand_schutterboog_pk2inschrijving = dict()
        for obj in (RegioCompetitieSchutterBoog
                    .objects
                    .select_related('deelcompetitie',
                                    'deelcompetitie__competitie',
                                    'schutterboog',
                                    'bij_vereniging')
                    .all()):
            tup = (obj.deelcompetitie.competitie.pk, obj.schutterboog.pk)
            self._cache_inschrijving[tup] = obj

            tup = (obj.deelcompetitie.competitie.afstand, obj.schutterboog.pk)
            afstand_schutterboog_pk2inschrijving[tup] = obj
        # for

        for obj in (Score
                    .objects
                    .select_related('schutterboog')
                    .filter(type=SCORE_TYPE_INDIV_AG,
                            afstand_meter__in=(18, 25))
                    .all()):
            tup = (obj.afstand_meter, obj.schutterboog.pk)
            self._cache_ag_score[tup] = obj
        # for

        for hist in (ScoreHist
                     .objects
                     .select_related('score', 'score__schutterboog')
                     .filter(score__type=SCORE_TYPE_SCORE,
                             notitie__startswith="Importeer scores van uitslagen.handboogsport.nl voor ronde ")):
            ronde = int(hist.notitie[-1])
            score = hist.score
            tup = (str(score.afstand_meter), score.schutterboog.pk)
            try:
                inschrijving = afstand_schutterboog_pk2inschrijving[tup]
            except KeyError:        # pragma: no cover
                pass
            else:
                tup = (inschrijving.pk, ronde)
                self._cache_scores[tup] = score
        # for

        for obj in (RegiocompetitieTeam
                    .objects
                    .select_related('vereniging',
                                    'deelcompetitie__competitie')
                    .all()):
            tup = (obj.deelcompetitie.competitie.afstand, str(obj.vereniging.ver_nr), obj.team_naam)
            self._cache_teams[tup] = obj
        # for

    def _prep_regio2deelcomp_regio2ronde2uitslag(self):
        # maak vertaling van vereniging naar deelcompetitie
        # wordt aangeroepen voor elke competitie (18/25)

        self._regio2deelcomp = dict()
        self._regio2ronde2uitslag = dict()
        self._uitslag2wedstrijd = dict()

        nul_uur = datetime.time(hour=0, minute=0, second=0)

        if self._afstand == 18:
            max_score = 300
        else:
            max_score = 250

        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('nhb_regio')
                         .filter(laag=LAAG_REGIO,
                                 competitie=self._comp)
                         .all()):

            regio_nr = deelcomp.nhb_regio.regio_nr

            self._regio2deelcomp[regio_nr] = deelcomp

            # zorg dat het plan wedstrijden heeft voor geïmporteerde regiocompetitie scores
            # 1 wedstrijd voor elke ronde
            self._regio2ronde2uitslag[regio_nr] = dict()

            for ronde in range(1, 7+1):
                self._regio2ronde2uitslag[regio_nr][ronde] = dict()

                beschrijving = "Ronde %s oude programma" % ronde

                try:
                    deelcomp_ronde = (DeelcompetitieRonde
                                      .objects
                                      .get(beschrijving=beschrijving,
                                           deelcompetitie=deelcomp))
                except DeelcompetitieRonde.DoesNotExist:
                    # geen ronde met een plan met die naam
                    # maak een nieuwe aan

                    plan = WedstrijdenPlan()
                    plan.bevat_hiaat = False
                    plan.save()

                    deelcomp_ronde = DeelcompetitieRonde()
                    deelcomp_ronde.deelcompetitie = deelcomp
                    deelcomp_ronde.week_nr = 37
                    deelcomp_ronde.beschrijving = beschrijving
                    deelcomp_ronde.plan = plan
                    deelcomp_ronde.save()

                beschrijving = "Resultaat van uitslagen.handboogsport.nl regio %s ronde %s" % (regio_nr, ronde)

                try:
                    wedstrijd = deelcomp_ronde.plan.wedstrijden.get(beschrijving=beschrijving)
                except CompetitieWedstrijd.DoesNotExist:
                    # maak een nieuwe wedstrijd aan
                    wedstrijd = CompetitieWedstrijd()
                    wedstrijd.beschrijving = beschrijving
                    wedstrijd.preliminair = False
                    wedstrijd.datum_wanneer = self._maandag_wk37
                    wedstrijd.tijd_begin_aanmelden = nul_uur
                    wedstrijd.tijd_begin_wedstrijd = nul_uur
                    wedstrijd.tijd_einde_wedstrijd = nul_uur
                    wedstrijd.save()

                    deelcomp_ronde.plan.wedstrijden.add(wedstrijd)

                # zorg dat de wedstrijd een uitslag heeft
                if not wedstrijd.uitslag:
                    uitslag = CompetitieWedstrijdUitslag()
                    uitslag.max_score = max_score
                    uitslag.afstand_meter = self._afstand
                    uitslag.save()

                    wedstrijd.uitslag = uitslag
                    wedstrijd.save()

                self._regio2ronde2uitslag[regio_nr][ronde] = wedstrijd.uitslag
                self._uitslag2wedstrijd[wedstrijd.uitslag.pk] = wedstrijd
                self._wedstrijd2ronde[wedstrijd.pk] = deelcomp_ronde
            # for
        # for

    def _update_wedstrijd_datum(self, wedstrijd):
        # deze wedstrijd heeft de default datum maandag_wk37
        # aan de hand van de momenten waarop de scores in gevoerd zijn
        # bepalen we een nieuwe datum: maandag in de week van deze import

        d1 = wedstrijd.datum_wanneer
        d2 = self._maandag_wk37

        if d1.year == d2.year and d1.month == d2.month and d1.day == d2.day:
            # weekday = 0..6, waarbij 0=maandag
            wanneer = self._import_when - datetime.timedelta(days=self._import_when.weekday())
            wedstrijd.datum_wanneer = datetime.date(year=wanneer.year, month=wanneer.month, day=wanneer.day)
            wedstrijd.save()

            ronde = self._wedstrijd2ronde[wedstrijd.pk]
            ronde.week_nr = self._import_when.isocalendar()[1]
            ronde.save()

            self._roep_info('Datum van wedstrijd %s aangepast naar %s in week %s' % (
                                repr(wedstrijd.beschrijving), wedstrijd.datum_wanneer, ronde.week_nr))

    def _selecteer_klasse(self, beschrijving):
        tup = (self._comp.pk, beschrijving.lower())
        try:
            self._klasse = self._cache_klasse[tup]
        except KeyError:
            self.stderr.write('[ERROR] Kan wedstrijdklasse %s niet vinden (competitie %s)' % (
                                  repr(beschrijving), self._comp))
            self._count_errors += 1

    def _vind_schutterboog(self, lid):
        # schutterboog record vinden / aanmaken
        # boogtype aanzetten voor wedstrijden
        # aanvangsgemiddelde record aanmaken

        tup = (lid.nhb_nr, self._boogtype.afkorting)

        try:
            schutterboog = self._cache_schutterboog[tup]
        except KeyError:
            schutterboog, _ = SchutterBoog.objects.get_or_create(nhblid=lid,
                                                                 boogtype=self._boogtype)
            self._cache_schutterboog[tup] = schutterboog

        if not schutterboog.voor_wedstrijd:
            schutterboog.voor_wedstrijd = True
            schutterboog.save()

        return schutterboog

    def _vind_of_maak_ag(self, schutterboog, ag_str, aantal_scores):
        if ag_str:
            gemiddelde = Decimal(ag_str)
        else:
            gemiddelde = AG_NUL
        waarde = int(gemiddelde * 1000)

        tup = (self._afstand, schutterboog.pk)
        try:
            score = self._cache_ag_score[tup]
        except KeyError:
            # maak een tijdelijk AG aan dat we niet opslaan
            # want de oude site vult ontbrekende AG's aan vanaf 3 scores
            score = Score()
            score.type = SCORE_TYPE_INDIV_AG
            score.schutterboog = schutterboog
            score.afstand_meter = self._afstand
            score.waarde = waarde

            self._cache_ag_score[tup] = score
        else:
            # controleer of het AG overeen komt
            # stop hiermee vanaf 3 scores omdat de oude site het ontbrekende AG dan invult
            # en deze altijd afwijkend is
            if waarde != score.waarde and aantal_scores < 3:
                self._roep_warning(
                    'Verschil in AG voor nhbnr %s (%sm): bekend=%.3f, in uitslag=%.3f bij %s scores' % (
                                schutterboog.nhblid.nhb_nr,
                                self._afstand,
                                score.waarde / 1000,
                                waarde / 1000,
                                aantal_scores))

        return score

    def _vind_of_maak_inschrijving(self, deelcomp, schutterboog, lid_vereniging, ag_str, teamtype):
        # zoek de RegioCompetitieSchutterBoog erbij
        tup = (deelcomp.competitie.pk, schutterboog.pk)
        try:
            inschrijving = self._cache_inschrijving[tup]
        except KeyError:
            # schrijf de schutter in
            inschrijving = RegioCompetitieSchutterBoog()
            inschrijving.deelcompetitie = deelcomp
            inschrijving.schutterboog = schutterboog
            inschrijving.bij_vereniging = lid_vereniging
            inschrijving.klasse = self._klasse
            inschrijving.inschrijf_voorkeur_team = (teamtype is not None)

            if ag_str:
                inschrijving.aanvangsgemiddelde = ag_str
            else:
                inschrijving.aanvangsgemiddelde = AG_NUL
            if not self._dryrun:
                inschrijving.save()

            self._cache_inschrijving[tup] = inschrijving
        else:
            if teamtype:
                inschrijving.inschrijf_voorkeur_team = True
                inschrijving.save()

        return inschrijving

    def _uitslag_opslaan(self, deelcomp, inschrijving, scores):
        regio_nr = deelcomp.nhb_regio.regio_nr

        uitslagen = self._regio2ronde2uitslag[regio_nr]

        heb_eerste_score = False
        for ronde in range(7, 0, -1):
            notitie = "Importeer scores van uitslagen.handboogsport.nl voor ronde %s" % ronde

            waarde = scores[ronde - 1]

            if heb_eerste_score or waarde:              # filter 0 van nog niet geschoten wedstrijden
                heb_eerste_score = True

                # zoek de uitslag van de virtuele wedstrijd erbij
                uitslag = uitslagen[ronde]

                tup = (inschrijving.pk, ronde)
                try:
                    score = self._cache_scores[tup]
                except KeyError:
                    # eerste keer: maak het record + score aan
                    score = Score()
                    score.type = SCORE_TYPE_SCORE
                    score.afstand_meter = self._afstand
                    score.schutterboog = inschrijving.schutterboog
                    score.waarde = waarde
                    self._bulk_score.append(score)

                    hist = ScoreHist()
                    hist.score = score
                    hist.oude_waarde = 0
                    hist.nieuwe_waarde = waarde
                    hist.notitie = notitie
                    self._bulk_hist.append(hist)

                    try:
                        self._bulk_uitslag[uitslag.pk].append(score)
                    except KeyError:
                        self._pk2uitslag[uitslag.pk] = uitslag
                        self._bulk_uitslag[uitslag.pk] = [score]

                    self._cache_scores[tup] = score
                else:
                    # kijk of de score gewijzigd is
                    if score.waarde != waarde:
                        # sla de aangepaste score op
                        hist = ScoreHist()
                        hist.score = score
                        hist.oude_waarde = score.waarde
                        hist.nieuwe_waarde = waarde
                        hist.notitie = notitie
                        self._bulk_hist.append(hist)

                        score.waarde = waarde
                        score.save()
            else:
                # hanteer het op 0 zetten van een van de achterste score
                tup = (inschrijving.pk, ronde)
                try:
                    score = self._cache_scores[tup]
                except KeyError:
                    # geen score, geen probleem
                    pass
                else:
                    # zet deze score op 0
                    hist = ScoreHist()
                    hist.score = score
                    hist.oude_waarde = score.waarde
                    hist.nieuwe_waarde = waarde
                    hist.notitie = notitie
                    self._bulk_hist.append(hist)

                    score.waarde = waarde
                    score.save()
        # for

    def _zoek_echte_lid(self, nhb_nr, naam, ver_nr):

        objs = NhbLid.objects.filter(bij_vereniging__ver_nr=ver_nr)
        objs_no_ver = NhbLid.objects.filter(bij_vereniging__isnull=True)

        # doe een paar kleine aanpassingen aan de naam
        pos = naam.find(' vd ')
        if pos > 0:
            naam = naam[:pos] + ' v.d. ' + naam[pos+4:]

        pos = naam.find(' v ')
        if pos > 0:
            naam = naam[:pos] + ' van ' + naam[pos+3:]

        low_naam = naam.lower()

        # poging 1: volledige naam
        for obj in objs:
            if obj.volledige_naam().lower() == low_naam:
                return obj
        # for

        # poging 1: volledige naam, geen vereniging
        for obj in objs_no_ver:
            if obj.volledige_naam().lower() == low_naam:
                return obj
        # for

        # poging 2: alleen op achternaam
        matches = list()
        for obj in objs:
            if len(obj.achternaam) >= 4 and obj.achternaam.lower() in low_naam:
                matches.append(obj)
        # for
        if len(matches) == 1:
            return matches[0]

        if len(matches):
            self.stdout.write('[DEBUG] MULTI match (achternaam): %s, %s, %s' % (nhb_nr, ver_nr, naam))
            for obj in matches:
                msg = str(obj)
                self.stdout.write('  ' + msg)
            return None

        # poging 2: alleen op achternaam, geen vereniging
        matches = list()
        for obj in objs_no_ver:
            if len(obj.achternaam) >= 4 and obj.achternaam.lower() in low_naam:
                matches.append(obj)
        # for
        if len(matches) == 1:
            return matches[0]

        if len(matches):
            self.stdout.write('[DEBUG] MULTI match (achternaam): %s, %s, %s' % (nhb_nr, ver_nr, naam))
            for obj in matches:
                msg = str(obj) + ' (GEEN VERENIGING)'
                self.stdout.write('  ' + msg)
            return None

        # poging 3: op voornaam
        matches = list()
        for obj in objs:
            if len(obj.voornaam) >= 3 and obj.voornaam.lower() in low_naam[:len(obj.voornaam)+3]:
                matches.append(obj)
        # for

        if len(matches) == 1:
            return matches[0]

        if len(matches):
            self.stdout.write('[DEBUG] MULTI match (voornaam): %s, %s, %s' % (nhb_nr, ver_nr, naam))
            for obj in matches:
                msg = str(obj)
                self.stdout.write('  ' + msg)
            return None

        return None

    def _verwerk_schutter(self, nhb_nr, naam, ver_nr, ag_str, scores, teamtype):

        aantal_scores = len(scores) - scores.count(0)

        if nhb_nr >= 990000 and nhb_nr not in self._gezocht_99:
            try:
                self._nhbnr_scores[nhb_nr] = scores
                self._nhbnr_uit_99nr.append(nhb_nr)
                nhb_nr = settings.MAP_99_NRS[nhb_nr]
            except KeyError:
                # niet een bekende mapping - doe een voorstel
                self._gezocht_99.append(nhb_nr)
                lid = self._zoek_echte_lid(nhb_nr, naam, ver_nr)
                if lid:
                    msg = '[VOORSTEL] %s --> %s (%s' % (nhb_nr, lid.nhb_nr, ver_nr)
                    if not lid.bij_vereniging:
                        msg += ' --> GEEN VERENIGING'
                    msg += ' / %s' % naam
                    if naam != lid.volledige_naam():
                        msg += ' --> %s' % lid.volledige_naam()
                    msg += ')'
                    self.stdout.write(msg)
                else:
                    self.stdout.write('[WARNING] No match for %s %s %s' % (nhb_nr, ver_nr, naam))
        else:
            if nhb_nr in settings.MAP_99_NRS.values():
                self._nhbnr_uit_99nr.append(nhb_nr)
                self._nhbnr_scores[nhb_nr] = scores
                # kan geen problemen voorkomen, want afhankelijk van volgorde

        # zoek naar hout schutters die ook bij recurve staan
        if self._boogtype.afkorting in ('BB', 'IB', 'LB'):
            tup = tuple([self._afstand, nhb_nr, self._boogtype.afkorting] + scores)
            self._ingelezen.append(tup)

        elif self._boogtype.afkorting == 'R':
            # kijk of dit een dupe is met een houtboog uitslag
            # dit ivm het dupliceren van uitslagen onder Recurve voor de teamcompetitie
            for afkorting in ('BB', 'IB', 'LB'):
                tup = tuple([self._afstand, nhb_nr, afkorting] + scores)
                if tup in self._ingelezen:
                    self._roep_info('Sla dubbele invoer onder recurve (%sm) over: %s (scores: %s)' % (
                                    self._afstand, nhb_nr, ",".join([str(score) for score in scores])))
                    self._verwijder.append(nhb_nr)
                    return

        try:
            lid = self._cache_nhblid[nhb_nr]
        except KeyError:
            self._roep_warning('Kan lid %s niet vinden' % nhb_nr)
            return

        if naam != lid.volledige_naam_str:
            tup = (lid.nhb_nr, lid.volledige_naam_str, naam)
            if tup not in self._meld_afwijking_lid:
                self._meld_afwijking_lid.append(tup)
                self._roep_info('Verschil in lid %s naam: bekend=%s, oude programma=%s' % (
                                    lid.nhb_nr, lid.volledige_naam_str, naam))

        lid_ver = None
        if not lid.bij_vereniging:
            # sporter is op dit moment niet meer lid bij een vereniging
            # dit kan een overschrijving zijn, dus toch importeren onder de oude vereniging

            # zoek de oude vereniging erbij
            try:
                lid_ver = NhbVereniging.objects.get(ver_nr=ver_nr)
            except NhbVereniging.DoesNotExist:
                self.stderr.write('[ERROR] Vereniging %s is niet bekend; kan lid %s niet inschrijven (bij de oude vereniging)' % (
                                      ver_nr, nhb_nr))
                self._count_errors += 1
                return

            # onderdruk deze melding zolang er geen scores zijn
            if aantal_scores > 0:
                self._roep_warning('Lid %s heeft %s scores maar geen vereniging en wordt ingeschreven onder de oude vereniging' % (
                                       nhb_nr, aantal_scores))
        else:
            if str(lid.bij_vereniging.ver_nr) != ver_nr:
                # vind de oude vereniging, want die moeten we opslaan bij de inschrijving
                try:
                    lid_ver = NhbVereniging.objects.get(ver_nr=ver_nr)
                except NhbVereniging.DoesNotExist:
                    self.stderr.write('[ERROR] Vereniging %s is niet bekend; kan lid %s niet inschrijven' % (
                                          ver_nr, nhb_nr))
                    self._count_errors += 1
                    return
            else:
                lid_ver = lid.bij_vereniging

        deelcomp = self._regio2deelcomp[lid_ver.regio.regio_nr]

        # zorg dat de schutter-boog records er zijn en de voorkeuren ingevuld zijn
        schutterboog = self._vind_schutterboog(lid)
        score_ag = self._vind_of_maak_ag(schutterboog, ag_str, aantal_scores)

        inschrijving = self._vind_of_maak_inschrijving(deelcomp, schutterboog, lid_ver, ag_str, teamtype)

        if not self._dryrun:
            # bij 3 scores wordt de schutter verplaatst van klasse onbekend naar andere klasse
            if aantal_scores < 3:
                klasse_min_ag = int(self._klasse.min_ag * 1000)
                if score_ag.waarde < klasse_min_ag:
                    self._roep_warning(
                        'Schutter %s heeft te laag AG (%.3f) voor klasse %s' % (
                              nhb_nr, score_ag.waarde / 1000, self._klasse))

            self._uitslag_opslaan(deelcomp, inschrijving, scores)

            if inschrijving.klasse != self._klasse:
                self._roep_warning(
                    'Verschil in klasse voor nhbnr %s (%sm): %s; oude programma: %s' % (
                        schutterboog.nhblid.nhb_nr,
                        deelcomp.competitie.afstand,
                        inschrijving.klasse,
                        self._klasse))

    def _verwerk_ver_teams(self, data, afstand, afkorting):
        for ver_nr, team_data in data.items():
            try:
                ver = self._cache_nhbver[int(ver_nr)]
            except (ValueError, KeyError):
                pass
            else:
                for team_nr in team_data.keys():
                    naam = "%s-%s-%s" % (afkorting, ver_nr, team_nr)        # R-1000-1
                    tup = (str(afstand), ver_nr, naam)
                    if tup not in self._cache_teams:
                        # nieuw team

                        volg_nrs = [obj.volg_nr for obj in self._cache_teams.values() if obj.vereniging.ver_nr == ver.ver_nr and obj.deelcompetitie.competitie == self._comp]
                        volg_nrs.append(0)
                        next_nr = max(volg_nrs) + 1

                        team = RegiocompetitieTeam(
                                    deelcompetitie=self._regio2deelcomp[ver.regio.regio_nr],
                                    vereniging=ver,
                                    volg_nr=next_nr,
                                    team_type=self._cache_teamtype[afkorting],
                                    team_naam=naam)
                        team.save()
                        self._cache_teams[tup] = team
                        self.stdout.write('[INFO] Regio team aangemaakt: %s in competitie %s' % (naam, self._comp))
                # for
        # for

    def _verwerk_klassen(self, data, afstand, afkorting):
        self._bulk_score = list()
        self._bulk_hist = list()
        self._bulk_uitslag = dict()
        self._pk2uitslag = dict()

        for klasse, data_schutters in data.items():
            if klasse == "ver_teams":
                self._verwerk_ver_teams(data_schutters, afstand, afkorting)
                continue

            self._selecteer_klasse(klasse)

            for nhb_nr, data_schutter in data_schutters.items():
                naam = data_schutter['n'].strip()
                ver_nr = data_schutter['v']
                ag = data_schutter['a']         # "9.123"
                scores = data_schutter['s']     # list
                try:
                    teamtype_str = data_schutter['t']
                    teamtype = self._cache_teamtype[teamtype_str]
                except KeyError:
                    teamtype = None

                self._verwerk_schutter(int(nhb_nr), naam, ver_nr, ag, scores, teamtype)
        # for

        # bulk-create the scores en scorehist records
        if len(self._bulk_score):
            Score.objects.bulk_create(self._bulk_score)

        if len(self._bulk_hist):
            for hist in self._bulk_hist:
                hist.score = hist.score     # doet iets voor net bulk-aangemaakte score records
            # for
            ScoreHist.objects.bulk_create(self._bulk_hist)

            # must manually back-date hist.when for each created object
            for hist in self._bulk_hist:
                hist.when = self._import_when
                hist.save()
            # for

        for uitslag_pk, scores in self._bulk_uitslag.items():
            uitslag = self._pk2uitslag[uitslag_pk]
            uitslag.scores.add(*scores)

            # wedstrijd datum aanpassen
            wedstrijd = self._uitslag2wedstrijd[uitslag_pk]
            self._update_wedstrijd_datum(wedstrijd)
        # for

    def _verwijder_dubbele_deelnemers(self):
        # ruim op: eerder aangemaakte dubbele inschrijvingen (BB + R)
        #          dit kan gebeuren als een uitslag wel in de BB/IB/LB staat maar nog niet in R
        for afstand, nhb_nrs in (('18', self._verwijder_r_18),
                                 ('25', self._verwijder_r_25)):
            # zoek alle inschrijvingen die hier bij passen
            objs = (RegioCompetitieSchutterBoog
                    .objects
                    .filter(deelcompetitie__competitie__afstand=afstand,
                            schutterboog__nhblid__nhb_nr__in=nhb_nrs,
                            schutterboog__boogtype__afkorting='R')
                    .all())

            if objs.count() > 0:
                self._roep_info('Verwijder %s dubbele inschrijvingen (%sm)' % (objs.count(), afstand))
                objs.delete()
        # for

        # reset memory
        self._verwijder_r_18 = list()
        self._verwijder_r_25 = list()
        self._verwijder = None
        self._ingelezen = list()

    def _lees_json(self, pad):
        self._roep_info('Inladen: %s' % pad)

        # filename: YYYYMMDD_HHMMSS_uitslagen
        spl = pad.split('/')
        grabbed_at = spl[-1][:15]
        import_when = datetime.datetime.strptime(grabbed_at, '%Y%m%d_%H%M%S')
        self._import_when = make_aware(import_when)
        # self.stdout.write('[DEBUG] import_when=%s' % self._import_when)

        json_file = os.path.join(pad, self.JSON_FILE)
        with open(json_file, 'r') as f:
            json_data = json.load(f)

        for afstand in (18, 25):
            self._afstand = afstand
            self._comp = None
            for comp in Competitie.objects.filter(afstand=afstand):
                comp.bepaal_fase()
                if 'E' <= comp.fase <= 'F':
                    # in de regiocompetitie wedstrijdfase, dus importeren
                    self._comp = comp
            # for

            if self._comp:
                self._maandag_wk37 = datetime.datetime.strptime("%s-W%d-1" % (self._comp.begin_jaar, 37), "%G-W%V-%u")
                self._maandag_wk37 = make_aware(self._maandag_wk37)

                self._prep_regio2deelcomp_regio2ronde2uitslag()

                if afstand == 18:
                    self._verwijder = self._verwijder_r_18
                else:
                    self._verwijder = self._verwijder_r_25

                afstand_data = json_data[str(afstand)]

                # doe R als laatste ivm verwijderen dubbelen door administratie teamcompetitie
                # (BB/IB/LB wordt met zelfde score onder Recurve gezet)
                for afkorting in ('C', 'BB', 'IB', 'LB', 'R'):
                    self._boogtype = self._cache_boogtype[afkorting]
                    boog_data = afstand_data[afkorting]
                    self._verwerk_klassen(boog_data, afstand, afkorting)
                # for
            else:
                self.stdout.write('[WARNING] Import %sm wordt overgeslagen want geen competitie gevonden in fase E..F' % afstand)

            for old, new in settings.MAP_99_NRS.items():
                if old in self._nhbnr_uit_99nr and new in self._nhbnr_uit_99nr:
                    self.stderr.write('[WARNING] Mogelijke dubbele deelnemer met %s nummer en %s' % (old, new))
                    self.stderr.write('          %s scores: %s' % (old, self._nhbnr_scores[old]))
                    self.stderr.write('          %s scores: %s' % (new, self._nhbnr_scores[new]))
            # for

            self._nhbnr_uit_99nr = list()
        # for

        self._verwijder_dubbele_deelnemers()

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs=1, help="Pad naar directory met opgehaalde rayonuitslagen")
        parser.add_argument('max_fouten', nargs=1, type=int, help="Zet exit code bij meer dan dit aantal fouten")
        parser.add_argument('--dryrun', action='store_true')
        parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        # self.stdout.write('[DEBUG] self.stdout.encoding = %s' % self.stdout.encoding)
        # self.stdout.write('[DEBUG]  sys.stdout.encoding = %s' % sys.stdout.encoding)

        pad = os.path.normpath(options['dir'][0])
        max_fouten = options['max_fouten'][0]
        self._dryrun = options['dryrun']

        self._prep_caches()

        if options['all']:
            # pad wijst naar een top-dir
            # doorloop alle sub-directories op zoek naar oude_site.json
            json_dirs = list()
            subdirs = os.listdir(pad)
            subdirs.sort()  # oudste eerst
            for subdir in subdirs:
                fpath = os.path.join(pad, subdir)
                if os.path.isdir(fpath):
                    fname = os.path.join(fpath, self.JSON_FILE)
                    if os.path.isfile(fname):
                        json_dirs.append(fpath)
            # for
            del subdirs

            for nr, json_dir in enumerate(json_dirs):
                self.stdout.write("Voortgang: %s van de %s" % (nr + 1, len(json_dirs)))
                self._lees_json(json_dir)
            # for
        else:
            self._lees_json(pad)

        activiteit = "Competitie inschrijvingen en scores aangevuld vanuit het oude programma"

        if self._dryrun:
            activiteit = "(DRY RUN) " + activiteit
        activiteit += " (waarschuwingen: %s, fouten: %s)" % (self._count_warnings, self._count_errors)

        # schrijf in het logboek
        if not self._dryrun:
            schrijf_in_logboek(account=None,
                               gebruikte_functie='oude_site_overnemen (command line)',
                               activiteit=activiteit)
        self.stdout.write(activiteit)

        if self._count_errors > max_fouten:
            sys.exit(1)


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
"""

# end of file
