# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# vergelijk de tussenstand met de data van de oude site en toon alle verschillen

from django.conf import settings
from django.core.management.base import BaseCommand
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, CompetitieKlasse, LAAG_REGIO,
                               DeelCompetitie, RegioCompetitieSchutterBoog)
from NhbStructuur.models import NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Score.models import Score, SCORE_TYPE_SCORE
import json
import os


class Command(BaseCommand):
    help = "Vergelijk tussenstand met data oude site"

    JSON_FILE = 'oude_site.json'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._ingelezen = list()           # tuple(afstand, nhbnr, boogtype, score1, ..., score 7)

        # wordt opgezet door _prep_regio2deelcomp_regio2ronde2uitslag
        self._regio2deelcomp = None        # [regio_nr] = DeelCompetitie

        self._cache_boogtype = dict()      # [afkorting] = BoogType
        self._cache_klasse = dict()        # [competitie.pk, klasse_beschrijving] = CompetitieKlasse
        self._cache_nhblid = dict()        # [nhbnr] = NhbLid
        self._cache_schutterboog = dict()  # [(nhblid, afkorting)] = SchutterBoog
        self._cache_inschrijving = dict()  # [(comp.pk, schutterboog.pk)] = RegioCompetitieSchutterBoog

    def _prep_caches(self):
        # bouw caches om herhaaldelijke database toegang te voorkomen, voor performance

        for obj in BoogType.objects.all():
            self._cache_boogtype[obj.afkorting] = obj
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

    def _prep_regio2deelcomp(self):
        # maak vertaling van vereniging naar deelcompetitie
        # wordt aangeroepen voor elke competitie (18/25)

        self._regio2deelcomp = dict()

        for deelcomp in (DeelCompetitie
                         .objects
                         .select_related('nhb_regio')
                         .filter(laag=LAAG_REGIO,
                                 competitie=self._comp)
                         .all()):

            regio_nr = deelcomp.nhb_regio.regio_nr

            self._regio2deelcomp[regio_nr] = deelcomp
        # for

    def _selecteer_klasse(self, beschrijving):
        tup = (self._comp.pk, beschrijving.lower())
        try:
            self._klasse = self._cache_klasse[tup]
        except KeyError:
            self.stderr.write('[ERROR] Kan wedstrijdklasse %s niet vinden (competitie %s)' % (
                                  repr(beschrijving), self._comp))

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

    def _vind_inschrijving(self, deelcomp, schutterboog):
        # zoek de RegioCompetitieSchutterBoog erbij
        tup = (deelcomp.competitie.pk, schutterboog.pk)
        return self._cache_inschrijving[tup]

    def _vergelijk_uitslag(self, inschrijving, scores):

        opgeslagen = [inschrijving.score1, inschrijving.score2, inschrijving.score3, inschrijving.score4,
                      inschrijving.score5, inschrijving.score6, inschrijving.score7]

        if scores != opgeslagen:
            self.stdout.write('[WARNING] Verschil voor %s: opgeslagen:%s != oude_site:%s' % (inschrijving, repr(opgeslagen), repr(scores)))

            scores = Score.objects.filter(schutterboog=inschrijving.schutterboog,
                                          afstand_meter=inschrijving.deelcompetitie.competitie.afstand,
                                          type=SCORE_TYPE_SCORE)
            self.stdout.write('[WARNING] Alle gevonden scores:')
            for score in scores:
                self.stdout.write('             %s' % score)

    def _verwerk_schutter(self, nhb_nr, ver_nr, scores):

        if nhb_nr >= 990000:
            try:
                nhb_nr = settings.MAP_99_NRS[nhb_nr]
            except KeyError:
                # niet een bekende mapping - doe een voorstel
                self.stdout.write('[WARNING] Onbekend NHB nummer: %s' % nhb_nr)
                return

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
                    # skip dubbele invoer
                    return

        try:
            lid = self._cache_nhblid[nhb_nr]
        except KeyError:
            self.stdout.write('[WARNING] Kan lid %s niet vinden' % nhb_nr)
            return

        aantal_scores = len(scores) - scores.count(0)

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
                return

            # onderdruk deze melding zolang er geen scores zijn
            if aantal_scores > 0:
                self.stdout.write('[WARNING] Lid %s heeft %s scores maar geen vereniging en wordt ingeschreven onder de oude vereniging' % (
                                       nhb_nr, aantal_scores))
        else:
            if str(lid.bij_vereniging.ver_nr) != ver_nr:
                # vind de oude vereniging, want die moeten we opslaan bij de inschrijving
                try:
                    lid_ver = NhbVereniging.objects.get(ver_nr=ver_nr)
                except NhbVereniging.DoesNotExist:
                    self.stderr.write('[ERROR] Vereniging %s is niet bekend; kan lid %s niet inschrijven' % (
                                          ver_nr, nhb_nr))
                    return
            else:
                lid_ver = lid.bij_vereniging

        deelcomp = self._regio2deelcomp[lid_ver.regio.regio_nr]
        schutterboog = self._vind_schutterboog(lid)
        inschrijving = self._vind_inschrijving(deelcomp, schutterboog)
        self._vergelijk_uitslag(inschrijving, scores)

    def _verwerk_klassen(self, data, afstand, afkorting):
        self._pk2uitslag = dict()

        for klasse, data_schutters in data.items():
            if klasse == "ver_teams":
                continue

            self._selecteer_klasse(klasse)

            for nhb_nr, data_schutter in data_schutters.items():
                ver_nr = data_schutter['v']
                scores = data_schutter['s']     # list

                self._verwerk_schutter(int(nhb_nr), ver_nr, scores)
        # for

    def _lees_json(self, pad):
        self.stdout.write('[INFO] Inladen: %s' % pad)

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

                self._prep_regio2deelcomp()

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
        # for

        self._ingelezen = list()

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs=1, help="Pad naar directory met opgehaalde rayonuitslagen")

    def handle(self, *args, **options):

        pad = os.path.normpath(options['dir'][0])

        self._prep_caches()
        self._lees_json(pad)


# end of file
