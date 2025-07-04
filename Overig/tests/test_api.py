# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog, CompetitieIndivKlasse
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from HistComp.models import HistCompSeizoen, HistCompRegioIndiv
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving


class TestOverigAPI(E2EHelpers, TestCase):

    """ tests voor de Overig applicatie; module API """

    test_after = ('Account.tests.test_login',)

    url_api = '/overig/api/lijst/csv/'

    def setUp(self):
        """ initialisatie van de test case """

        huidige_jaar = timezone.now().year

        account = self.e2e_create_account('100001', 'normal@khsn.not', 'Norma')

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112))
        ver.save()

        sporter = Sporter(
                    lid_nr=100001,
                    voornaam='Norma',
                    achternaam='de Sporter',
                    unaccented_naam='Norma de Sporter',  # hier wordt op gezocht
                    geboorte_datum='1980-01-01',
                    sinds_datum='2008-01-08',
                    lid_tot_einde_jaar=huidige_jaar,
                    bij_vereniging=ver)
        sporter.save()

        boog_c = BoogType.objects.get(afkorting='C')
        boog_r = BoogType.objects.get(afkorting='R')

        sporterboog = SporterBoog(
                        sporter=sporter,
                        boogtype=boog_r,
                        voor_wedstrijd=False)
        sporterboog.save()

        sporterboog = SporterBoog(
                        sporter=sporter,
                        boogtype=boog_c,
                        voor_wedstrijd=True)
        sporterboog.save()

        comp = Competitie(
                    afstand='18',
                    begin_jaar=huidige_jaar)
        comp.save()
        self.comp = comp

        functie_rcl = maak_functie('RCL 112', 'RCL')

        regiocomp = Regiocompetitie(
                        competitie=comp,
                        regio=Regio.objects.get(regio_nr=112),
                        functie=functie_rcl)
        regiocomp.save()

        klasse = CompetitieIndivKlasse(
                        competitie=comp,
                        volgorde=1,
                        boogtype=boog_c,
                        min_ag=0)
        klasse.save()

        deelnemer = RegiocompetitieSporterBoog(
                        regiocompetitie=regiocomp,
                        sporterboog=sporterboog,
                        bij_vereniging=ver,
                        aantal_scores=5,
                        indiv_klasse=klasse)
        deelnemer.save()

        locatie = WedstrijdLocatie(
                        naam='Test')
        locatie.save()

        vandaag = timezone.now().date()
        wedstrijd = Wedstrijd(
                        datum_begin=vandaag,
                        datum_einde=vandaag,
                        organiserende_vereniging=ver,
                        locatie=locatie)
        wedstrijd.save()

        sessie = WedstrijdSessie(
                        datum=vandaag,
                        tijd_begin='23:00',
                        tijd_einde='02:00',
                        beschrijving='Nachtverschieting',
                        max_sporters=64)
        sessie.save()
        wedstrijd.sessies.add(sessie)

        klasse = KalenderWedstrijdklasse.objects.get(volgorde=220)      # C gemengd
        inschrijving = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                            sporterboog=sporterboog,
                            wedstrijdklasse=klasse,
                            koper=account)
        inschrijving.save()

        hist_seizoen = HistCompSeizoen(
                            seizoen='this/that',
                            comp_type='18')
        hist_seizoen.save()
        self.hist_seizoen = hist_seizoen

        hist_indiv = HistCompRegioIndiv(
                            seizoen=hist_seizoen,
                            indiv_klasse='',
                            rank=0,
                            sporter_lid_nr=sporter.lid_nr,
                            sporter_naam='',
                            boogtype='',
                            vereniging_nr=0,
                            vereniging_naam='',
                            vereniging_plaats='',
                            regio_nr=0,
                            totaal=0,
                            gemiddelde=0)
        hist_indiv.save()

        sporter = Sporter(
                    lid_nr=100002,
                    voornaam='Andere',
                    achternaam='Sporter',
                    unaccented_naam='Andere Sporter',
                    geboorte_datum='1980-12-31',         # na de huidige datum (behalve op 31 dec)
                    sinds_datum='2008-01-08',
                    lid_tot_einde_jaar=huidige_jaar,
                    account=account,
                    bij_vereniging=ver)
        sporter.save()

    def test_api(self):
        # zonder token
        resp = self.client.get(self.url_api)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'\xef\xbb\xbf')     # BOM_UTF8

        with self.assert_max_queries(33):
            resp = self.client.get(self.url_api + '?token=%s' % settings.OVERIG_API_TOKENS[0])
        self.assertEqual(resp.status_code, 200)
        self.assert200_is_bestand_csv(resp)
        # print(resp.content)

        self.comp.afstand = '25'
        self.comp.save(update_fields=['afstand'])

        self.hist_seizoen.comp_type = '25'
        self.hist_seizoen.save(update_fields=['comp_type'])

        with self.assert_max_queries(33):
            resp = self.client.get(self.url_api + '?token=%s' % settings.OVERIG_API_TOKENS[0])
        self.assertEqual(resp.status_code, 200)
        self.assert200_is_bestand_csv(resp)
        # print(resp.content)


# end of file
