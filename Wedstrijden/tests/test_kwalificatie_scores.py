# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_KHSN
from BasisTypen.models import KalenderWedstrijdklasse
from Competitie.models import Regiocompetitie, RegiocompetitieSporterBoog
from Competitie.tests.test_helpers import maak_competities_en_zet_fase_c
from Geo.models import Regio
from Locatie.definities import BAAN_TYPE_EXTERN
from Locatie.models import Locatie
from Score.operations import score_indiv_ag_opslaan
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporterboog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_DISCIPLINE_INDOOR)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, Kwalificatiescore
import datetime


class TestWedstrijdenKwalificatieScores(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module wedstrijd wijzigen """

    test_after = ('Sporter', 'Competitie')

    url_kwalificatie_scores = '/wedstrijden/inschrijven/kwalificatie-scores-doorgeven/%s/'  # inschrijving_pk
    url_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/'                 # deelcomp_pk, sporterboog_pk
    url_profiel = '/sporter/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grote Club",
                    ver_nr=1000,
                    regio=Regio.objects.get(pk=111))
        ver.save()
        self.ver = ver

        # maak een test lid aan
        sporter = Sporter(
                        lid_nr=100001,
                        geslacht="M",
                        voornaam="Ramon",
                        achternaam="de Tester",
                        geboorte_datum=datetime.date(year=1972, month=3, day=4),
                        sinds_datum=datetime.date(year=2010, month=11, day=12),
                        bij_vereniging=ver,
                        account=self.account_normaal,
                        email=self.account_normaal.email)
        sporter.save()
        self.sporter1 = sporter

        get_sporterboog(sporter, mag_database_wijzigen=True)

        # zet een wedstrijd voorkeur voor Recurve en informatie voorkeur voor Barebow
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        sporterboog.voor_wedstrijd = True
        sporterboog.heeft_interesse = False
        sporterboog.save()

        for boog in ('C', 'TR', 'LB'):
            sporterboog = SporterBoog.objects.get(boogtype__afkorting=boog)
            sporterboog.heeft_interesse = False
            sporterboog.save()
        # for

        now = timezone.now()
        volgende_week = (now + datetime.timedelta(days=7)).date()
        sporterboog = SporterBoog.objects.select_related('boogtype').filter(sporter=self.sporter1).first()
        boogtype = sporterboog.boogtype
        klasse = KalenderWedstrijdklasse.objects.filter(boogtype=sporterboog.boogtype).first()

        locatie = Locatie(
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

        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            status=INSCHRIJVING_STATUS_DEFINITIEF,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            wedstrijdklasse=klasse,
                            koper=self.account_normaal,
                            log='test')
        inschrijving.save()

        self.inschrijving = inschrijving

    def test_wedstrijden(self):
        # log in as sporter
        self.e2e_login(self.account_normaal)

        inschrijving = WedstrijdInschrijving.objects.first()
        url = self.url_kwalificatie_scores % inschrijving.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-kwalificatie-scores.dtl', 'plein/site_layout.dtl'))

        self.e2e_assert_other_http_commands_not_supported(url, post=False)

        jaar = inschrijving.wedstrijd.datum_begin.year - 1
        kwalificatie_datum = datetime.date(jaar, 9, 1)      # 1 september

        # voer de kwalificatie-scores in
        self.assertEqual(0, Kwalificatiescore.objects.count())
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123',
                                          'score2_datum': '2000-01-01',     # fout
                                          'score2_result': '601'})          # fout
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-toegevoegd-aan-mandje.dtl', 'plein/site_layout.dtl'))
        self.assertEqual(3, Kwalificatiescore.objects.count())
        score = Kwalificatiescore.objects.exclude(naam='').first()
        self.assertEqual(score.naam, 'Test naam')
        self.assertEqual(score.waar, 'Test plaats')
        self.assertEqual(score.resultaat, 123)

        # maak een extra record aan
        score.pk = None
        score.save()

        # nog een keer wijzigen
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-kwalificatie-scores.dtl', 'plein/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123'})
        self.assert_is_redirect(resp, '/plein/')
        self.assertEqual(3, Kwalificatiescore.objects.count())

        # sporter mag wijzigingen als iemand anders de aankoop gedaan heeft
        self.account_twee = self.e2e_create_account('twee', 'twee@test.com', 'Twee')
        self.inschrijving.koper = self.account_twee
        self.inschrijving.save(update_fields=['koper'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-kwalificatie-scores.dtl', 'plein/site_layout.dtl'))

        # niet de sporter (geen account) en niet de koper, dan mag je niet wijzigen
        self.sporter1.account = None
        self.sporter1.save(update_fields=['account'])
        resp = self.client.get(url)
        self.assert404(resp, 'Mag niet wijzigen')
        resp = self.client.post(url)
        self.assert404(resp, 'Mag niet wijzigen')

        # corner cases
        self.inschrijving.wedstrijd.eis_kwalificatie_scores = False
        self.inschrijving.wedstrijd.save(update_fields=['eis_kwalificatie_scores'])
        resp = self.client.get(url)
        self.assert404(resp, 'Inschrijving niet gevonden')

        resp = self.client.get(self.url_kwalificatie_scores % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')
        resp = self.client.post(self.url_kwalificatie_scores % 999999)
        self.assert404(resp, 'Inschrijving niet gevonden')

    def test_deelnemer(self):
        # sporter is ook deelnemer in de bondscompetities
        self.comp_18, _ = maak_competities_en_zet_fase_c()

        self.e2e_login(self.account_normaal)

        # schrijf de sporter in voor de 18m Recurve
        sporterboog = SporterBoog.objects.get(boogtype__afkorting='R')
        deelcomp = Regiocompetitie.objects.get(competitie__afstand='18', regio=self.ver.regio)
        res = score_indiv_ag_opslaan(sporterboog, 18, 8.18, None, 'Test')
        self.assertTrue(res)
        url = self.url_aanmelden % (deelcomp.pk, sporterboog.pk)
        with self.assert_max_queries(21):
            resp = self.client.post(url, {'opmerking': 'test van de 18m'})
        self.assert_is_redirect(resp, self.url_profiel)

        self.assertEqual(1, RegiocompetitieSporterBoog.objects.count())
        deelnemer = RegiocompetitieSporterBoog.objects.first()
        deelnemer.score1 = 234
        deelnemer.score2 = 245
        deelnemer.save(update_fields=['score1', 'score2'])

        inschrijving = WedstrijdInschrijving.objects.first()
        url = self.url_kwalificatie_scores % inschrijving.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/inschrijven-kwalificatie-scores.dtl', 'plein/site_layout.dtl'))
        self.assertContains(resp, '245, 234')


# end of file
