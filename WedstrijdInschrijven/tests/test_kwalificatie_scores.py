# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_KHSN
from BasisTypen.models import KalenderWedstrijdklasse
from Competitie.models import Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Functie.models import Functie
from Geo.models import Regio
from Locatie.definities import BAAN_TYPE_EXTERN
from Locatie.models import WedstrijdLocatie
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporterboog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_DISCIPLINE_INDOOR,
                                    INSCHRIJVING_STATUS_RESERVERING_MANDJE, INSCHRIJVING_STATUS_DEFINITIEF,
                                    KWALIFICATIE_CHECK_GOED, KWALIFICATIE_CHECK_NOG_DOEN)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, Kwalificatiescore
import datetime


class TestWedstrijdInschrijvenKwalificatieScores(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module wedstrijd wijzigen """

    test_after = ('Sporter', 'Competitie')

    url_kwalificatie_scores = '/wedstrijden/inschrijven/kwalificatie-scores-doorgeven/%s/'  # inschrijving_pk
    url_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/'             # deelcomp_pk, sporterboog_pk
    url_profiel = '/sporter/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_sporter1 = self.e2e_create_account('100001', '100001@test.com', 'Eerste')
        self.account_sporter2 = self.e2e_create_account('100002', '100002@test.com', 'Tweede')

        self.account_admin = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        self.functie_mwz = Functie.objects.get(rol='MWZ')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver = ver

        # maak een sporter aan
        sporter1 = Sporter(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_sporter1,
                        email=self.account_sporter1.email)
        sporter1.save()
        self.sporter1 = sporter1

        # maak nog een sporter aan
        sporter2 = Sporter(
                        lid_nr=100002,
                        geslacht="V",
                        voornaam="Ramona",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=5),
                        sinds_datum=datetime.date(year=2011, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_sporter2,
                        email=self.account_sporter2.email)
        sporter2.save()
        self.sporter2 = sporter2

        get_sporterboog(sporter1, mag_database_wijzigen=True)
        get_sporterboog(sporter2, mag_database_wijzigen=True)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        sporterboog1 = SporterBoog.objects.select_related('boogtype').get(boogtype__afkorting='R', sporter=sporter1)
        sporterboog1.voor_wedstrijd = True
        sporterboog1.heeft_interesse = False
        sporterboog1.save()
        self.sporterboog1_r = sporterboog1

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        sporterboog2 = SporterBoog.objects.get(boogtype__afkorting='R', sporter=sporter2)
        sporterboog2.voor_wedstrijd = True
        sporterboog2.heeft_interesse = False
        sporterboog2.save()
        self.sporterboog2_r = sporterboog2

        for boog in ('C', 'TR', 'LB'):
            sporterboog1 = SporterBoog.objects.get(boogtype__afkorting=boog, sporter=sporter1)
            sporterboog1.heeft_interesse = False
            sporterboog1.save()
        # for

        now = timezone.now()
        volgende_week = (now + datetime.timedelta(days=7)).date()

        boogtype = self.sporterboog1_r.boogtype
        klasse = KalenderWedstrijdklasse.objects.filter(boogtype=boogtype).first()

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        baan_type=BAAN_TYPE_EXTERN,
                        discipline_indoor=True,
                        banen_18m=15,
                        max_sporters_18m=15*4,
                        adres='Sportstraat 1, Pijlstad',
                        plaats='Pijlstad')
        locatie.save()
        locatie.verenigingen.add(self.ver)

        sessie = WedstrijdSessie(
                        datum=volgende_week,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        beschrijving='test',
                        max_sporters=20)
        sessie.save()
        sessie.wedstrijdklassen.add(klasse)

        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=volgende_week,
                        datum_einde=volgende_week,
                        inschrijven_tot=1,
                        organiserende_vereniging=self.ver,
                        locatie=locatie,
                        organisatie=ORGANISATIE_KHSN,
                        discipline=WEDSTRIJD_DISCIPLINE_INDOOR,
                        aantal_banen=locatie.banen_18m,
                        eis_kwalificatie_scores=True)
        wedstrijd.save()
        wedstrijd.boogtypen.add(boogtype)
        wedstrijd.wedstrijdklassen.add(klasse)
        wedstrijd.sessies.add(sessie)
        self.wedstrijd = wedstrijd

        inschrijving1 = WedstrijdInschrijving(
                            wanneer=now,
                            status=INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=self.sporterboog1_r,
                            wedstrijdklasse=klasse,
                            koper=self.account_sporter1,
                            log='test')
        inschrijving1.save()
        self.inschrijving1 = inschrijving1

        inschrijving2 = WedstrijdInschrijving(
                            wanneer=now,
                            status=INSCHRIJVING_STATUS_DEFINITIEF,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=self.sporterboog2_r,
                            wedstrijdklasse=klasse,
                            koper=self.account_sporter2,
                            log='test')
        inschrijving2.save()
        self.inschrijving2 = inschrijving2

        jaar = inschrijving1.wedstrijd.datum_begin.year - 1
        self.kwalificatie_datum = datetime.date(jaar, 9, 1)      # 1 september

    def test_anon(self):
        resp = self.client.get(self.url_kwalificatie_scores % 999999)
        self.assert403(resp, 'Geen toegang')

    def test_sporter(self):
        # log in as sporter
        self.e2e_login(self.account_sporter1)

        url = self.url_kwalificatie_scores % self.inschrijving1.pk      # status = mandje

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-kwalificatie-scores.dtl',
                                         'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        # voer de kwalificatie-scores in
        self.assertEqual(0, Kwalificatiescore.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123',
                                          'score2_datum': '2000-01-01',     # fout
                                          'score2_result': '601'})          # fout
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-toegevoegd-aan-mandje.dtl',
                                         'plein/site_layout.dtl'))
        self.assertEqual(3, Kwalificatiescore.objects.count())

        score = Kwalificatiescore.objects.exclude(naam='').first()
        self.assertEqual(score.naam, 'Test naam')
        self.assertEqual(score.waar, 'Test plaats')
        self.assertEqual(score.resultaat, 123)
        self.assertTrue(str(score) != '')       # coverage for admin function

        # nog een keer opslaan, geen wijzigingen
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123'})
        self.assert_is_redirect(resp, '/plein/')

        # echte wijziging terwijl nog niet gecontroleerd
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum + datetime.timedelta(days=1),
                                          'score1_naam': 'Test naam 2',
                                          'score1_waar': 'Test plaats 2',
                                          'score1_result': '124'})
        self.assert_is_redirect(resp, '/plein/')

        # echte wijziging terwijl al gecontroleerd
        score.check_status = KWALIFICATIE_CHECK_GOED
        score.save(update_fields=['check_status'])
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam 2',
                                          'score1_waar': 'Test plaats 2',
                                          'score1_result': '125'})      # changed
        self.assert_is_redirect(resp, '/plein/')

        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertIn('Check status automatisch terug gezet', score.log)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_NOG_DOEN)

        self.inschrijving1.status = INSCHRIJVING_STATUS_DEFINITIEF
        self.inschrijving1.save(update_fields=['status'])

        self.assertTrue(str(self.inschrijving1) != '')
        self.assertTrue(self.inschrijving1.korte_beschrijving() != '')

        # maak een extra record te veel aan
        score.pk = None
        score.save()

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-kwalificatie-scores.dtl',
                                         'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123'})
        self.assert_is_redirect(resp, '/plein/')
        self.assertEqual(3, Kwalificatiescore.objects.count())

        # sporter mag wijzigingen als iemand anders de aankoop gedaan heeft
        self.account_twee = self.e2e_create_account('twee', 'twee@test.com', 'Twee')
        self.inschrijving1.koper = self.account_twee
        self.inschrijving1.save(update_fields=['koper'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-kwalificatie-scores.dtl',
                                         'plein/site_layout.dtl'))

        # te dicht op de wedstrijd
        self.wedstrijd.datum_begin = timezone.now().date()
        self.wedstrijd.save(update_fields=['datum_begin'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-kwalificatie-scores.dtl',
                                         'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123'})
        self.assert404(resp, 'Mag niet meer aanpassen')

        # niet de sporter (geen account) en niet de koper, dan mag je niet wijzigen
        self.sporter1.account = None
        self.sporter1.save(update_fields=['account'])
        resp = self.client.get(url)
        self.assert404(resp, 'Mag niet wijzigen')
        resp = self.client.post(url)
        self.assert404(resp, 'Mag niet wijzigen')

        # corner cases
        self.inschrijving1.wedstrijd.eis_kwalificatie_scores = False
        self.inschrijving1.wedstrijd.save(update_fields=['eis_kwalificatie_scores'])
        resp = self.client.get(url)
        self.assert404(resp, 'Inschrijving niet gevonden')

        resp = self.client.get(self.url_kwalificatie_scores % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')
        resp = self.client.post(self.url_kwalificatie_scores % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

    def test_sporter_met_bondscompetitie(self):
        # sporter is ook deelnemer in de bondscompetities
        self.comp_18, _ = maak_competities_en_zet_fase_c()

        self.e2e_login(self.account_sporter1)

        # schrijf de sporter in voor de 18m Recurve
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(self.sporterboog1_r, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        url = self.url_aanmelden % (deelcomp.pk, self.sporterboog1_r.pk)
        with self.assert_max_queries(21):
            resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        self.assertEqual(1, RegiocompetitieSporterBoog.objects.count())
        deelnemer = RegiocompetitieSporterBoog.objects.first()
        deelnemer.score1 = 234
        deelnemer.score2 = 245
        deelnemer.save(update_fields=['score1', 'score2'])

        url = self.url_kwalificatie_scores % self.inschrijving1.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijdinschrijven/inschrijven-kwalificatie-scores.dtl',
                                         'plein/site_layout.dtl'))
        self.assertContains(resp, '245, 234')

# end of file
