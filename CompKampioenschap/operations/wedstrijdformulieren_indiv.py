# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helper functies """

from django.utils import timezone
from django.templatetags.l10n import localize
from Competitie.definities import DEEL_BK, DEEL_RK, DEELNAME_NEE, DEELNAME2STR
from Competitie.models import (Competitie, CompetitieIndivKlasse, CompetitieMatch,
                               Kampioenschap, KampioenschapIndivKlasseLimiet, KampioenschapSporterBoog)
from Geo.models import Rayon
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet
from Sporter.models import SporterVoorkeuren


def iter_indiv_wedstrijdformulieren(comp: Competitie):
    """ generator voor alle individuele wedstrijdformulieren

        generates tuples:
            (afstand, is_bk, klasse_pk, rayon_nr, fname)
    """
    afstand = int(comp.afstand)
    rayon_nrs = list(Rayon.objects.all().values_list('rayon_nr', flat=True))

    for klasse in CompetitieIndivKlasse.objects.filter(competitie=comp, is_ook_voor_rk_bk=True):
        klasse_str = klasse.beschrijving.lower().replace(' ', '-')

        # RK programma's
        for rayon_nr in rayon_nrs:
            fname = "rk-programma_individueel-rayon%s_" % rayon_nr
            fname += klasse_str
            #              is_bk
            yield afstand, False, klasse.pk, rayon_nr, fname
        # for

        # BK programma's
        fname = "bk-programma_individueel_" + klasse_str
        #              is_bk
        yield afstand, True, klasse.pk, 0, fname
    # for


class UpdateIndivWedstrijdFormulier:

    def __init__(self, stdout, sheet: StorageGoogleSheet):
        self.stdout = stdout
        self.sheet = sheet      # kan google sheets bijwerken

        self.aantal_regels_deelnemers = 24        # altijd dit aantal overschrijven, voor als de cut omlaag gezet wordt
        self.aantal_regels_reserves = 0

        self.klasse = None
        self.kampioenschap = None
        self.limiet = 0                 # maximaal aantal deelnemers
        self.aantal_ingeschreven = 0

        self.ranges = {
            'titel': 'C2',
            'info': 'F4:F7',
            'bijgewerkt': 'A37',
            'scores': 'J11:K35',
            'deelnemers': 'D11:I%d' % (11 + self.aantal_regels_deelnemers - 1),
            'deelnemers_notities': 'T11:U%d' % (11 + self.aantal_regels_deelnemers - 1),
            'reserves': 'D41:I99',                # wordt bijgewerkt in laad_klasse
            'reserves_notities': 'T41:U99',       # wordt bijgewerkt in laad_klasse
        }

    def _laad_klasse(self, bestand: Bestand):
        # zoek de wedstrijdklasse erbij
        self.klasse = CompetitieIndivKlasse.objects.get(pk=bestand.klasse_pk)

        competitie = self.klasse.competitie
        if bestand.is_bk:
            self.kampioenschap = Kampioenschap.objects.filter(competitie=competitie, deel=DEEL_BK).first()
        else:
            self.kampioenschap = Kampioenschap.objects.filter(competitie=competitie, deel=DEEL_RK,
                                                              rayon__rayon_nr=bestand.rayon_nr).first()

        self.aantal_ingeschreven = KampioenschapSporterBoog.objects.filter(kampioenschap=self.kampioenschap,
                                                                           indiv_klasse=self.klasse).count()

        # haal de limiet op (maximum aantal deelnemers)
        self.limiet = 24
        lim = KampioenschapIndivKlasseLimiet.objects.filter(kampioenschap=self.kampioenschap,
                                                            indiv_klasse=self.klasse).first()
        if lim:
            self.limiet = lim.limiet

        # pas de range aan zodat we niet onnodig veel data hoeven te sturen
        self.aantal_regels_reserves = self.aantal_ingeschreven      # iedereen kan afgemeld zijn
        self.ranges['reserves'] = 'D41:I%d' % (41 + self.aantal_regels_reserves - 1)
        self.ranges['reserves_notities'] = 'T41:U%d' % (41 + self.aantal_regels_reserves - 1)

        if bestand.is_bk:
            self.titel = 'BK'
        else:
            self.titel = 'RK'
        self.titel += ' individueel, %s' % competitie.beschrijving.replace('competitie ', '')   # is inclusief seizoen

        if not bestand.is_bk:
            # benoem het rayon
            self.titel += ', Rayon %s' % bestand.rayon_nr

    def _schrijf_kopje(self, match: CompetitieMatch):
        # zet de titel
        self.sheet.wijzig_cellen(self.ranges['titel'], [[self.titel]])

        # schrijf de info in de heading
        regels = list()

        # wedstrijdklasse
        regels.append([self.klasse.beschrijving])

        # datum
        print('pk=%s' % match.pk, match.datum_wanneer, '->', localize(match.datum_wanneer))
        regels.append([localize(match.datum_wanneer)])      # localize geeft NL formaat "1 januari 2026"

        # organisatie
        ver = match.vereniging
        if ver:
            regels.append([ver.ver_nr_en_naam()])
        else:
            regels.append(['Nog niet toegekend'])

        # adres
        loc = match.locatie
        if loc:
            regels.append([loc.adres])
        else:
            regels.append(['Onbekend'])

        self.sheet.wijzig_cellen(self.ranges['info'], regels)

    def _schrijf_deelnemers(self):
        deelnemers = list()
        afgemeld = list()

        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=self.kampioenschap,
                                  indiv_klasse=self.klasse)
                          .exclude(bij_vereniging=None)
                          .select_related('sporterboog__sporter',
                                          'bij_vereniging',
                                          'bij_vereniging__regio')
                          .order_by('rank',  # laagste eerst
                                    'volgorde')):  # sorteert afgemeld

            sporter = deelnemer.sporterboog.sporter

            para_notities = ''
            voorkeuren = SporterVoorkeuren.objects.filter(sporter=sporter).first()
            if voorkeuren:      # pragma: no branch
                if voorkeuren.para_voorwerpen:
                    para_notities = 'Sporter laat voorwerpen op de schietlijn staan'

                if voorkeuren.opmerking_para_sporter:
                    if para_notities != '':
                        para_notities += '\n'
                    para_notities += voorkeuren.opmerking_para_sporter

            regel = [str(sporter.lid_nr),
                     sporter.volledige_naam(),
                     deelnemer.bij_vereniging.ver_nr_en_naam(),
                     deelnemer.bij_vereniging.regio.regio_nr,
                     deelnemer.kampioen_label,
                     str(deelnemer.gemiddelde).replace('.', ','),  # NL format
                     DEELNAME2STR[deelnemer.deelname],
                     para_notities]

            if deelnemer.deelname == DEELNAME_NEE:
                afgemeld.append(regel)
            else:
                deelnemers.append(regel)
        # for

        # pas de cut toe
        reserves = deelnemers[self.limiet:] + afgemeld
        deelnemers = deelnemers[:self.limiet]

        # maak beide lijsten op lengte
        regel = ['', '', '', '', '', '', '', '']  # bondsnr, naam, ver, regio, leeg, gemiddelde, deelname, notities
        while len(deelnemers) < self.aantal_regels_deelnemers:
            deelnemers.append(regel)
        # while
        while len(reserves) < self.aantal_regels_reserves:
            reserves.append(regel)
        # while

        # split de data over 2 ranges: 6 kolommen en 2 kolommen
        deelnemers_1 = [deelnemer[:6] for deelnemer in deelnemers]
        deelnemers_2 = [deelnemer[-2:] for deelnemer in deelnemers]
        self.sheet.wijzig_cellen(self.ranges['deelnemers'], deelnemers_1)
        self.sheet.wijzig_cellen(self.ranges['deelnemers_notities'], deelnemers_2)

        reserves_1 = [deelnemer[:6] for deelnemer in reserves]
        reserves_2 = [deelnemer[-2:] for deelnemer in reserves]
        self.sheet.wijzig_cellen(self.ranges['reserves'], reserves_1)
        self.sheet.wijzig_cellen(self.ranges['reserves_notities'], reserves_2)

    def _schrijf_bijgewerkt(self):
        # geef aan wanneer de lijst bijgewerkt is
        vastgesteld = timezone.localtime(timezone.now())
        msg = 'Deze gegevens zijn bijgewerkt door MijnHandboogsport op %s' % vastgesteld.strftime('%Y-%m-%d %H:%M:%S')
        self.sheet.wijzig_cellen(self.ranges['bijgewerkt'], [[msg]])

    def _schrijf_update(self, bestand: Bestand, match: CompetitieMatch):
        self._schrijf_kopje(match)
        self._schrijf_deelnemers()
        self._schrijf_bijgewerkt()

        # voer alle wijzigingen door met 1 transactie
        self.sheet.stuur_wijzigingen()

    def _heeft_scores(self):
        values = self.sheet.get_range(self.ranges['scores'])
        if values:
            for row in values:
                for cell in row:
                    if cell:
                        # cell is niet leeg
                        self.stdout.write('[DEBUG] score gevonden: %s' % repr(cell))
                        return True
                # for
            # for
        return False

    def update_wedstrijdformulier(self, bestand: Bestand, match: CompetitieMatch):
        # zoek de wedstrijdklasse, kampioenschap, limiet, etc. erbij
        self._laad_klasse(bestand)

        # enige verschil tussen de templates
        if bestand.afstand == 18:
            # Indoor
            self.sheet.selecteer_sheet('Voorronde')
        else:
            # 25m1pijl
            self.sheet.selecteer_sheet('Wedstrijd')

        if self._heeft_scores():
            self.stdout.write('[DEBUG] heeft scores')
            return "NOK: Heeft scores"

        # update het bestand
        self._schrijf_update(bestand, match)
        return "OK"


# end of file
