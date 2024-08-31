# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_KHSN
from BasisTypen.models import KalenderWedstrijdklasse
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Locatie.definities import BAAN_TYPE_EXTERN
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from Sporter.operations import get_sporterboog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import (INSCHRIJVING_STATUS_DEFINITIEF, WEDSTRIJD_STATUS_GEACCEPTEERD,
                                    WEDSTRIJD_DISCIPLINE_INDOOR,
                                    KWALIFICATIE_CHECK_GOED, KWALIFICATIE_CHECK_NOG_DOEN, KWALIFICATIE_CHECK_AFGEKEURD)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving, Kwalificatiescore
import datetime
import json


class TestWedstrijdenKwalificatieScores(E2EHelpers, TestCase):

    """ tests voor de Wedstrijden applicatie, module wedstrijd wijzigen """

    test_after = ('Sporter', 'Competitie')

    url_kwalificatie_scores = '/wedstrijden/inschrijven/kwalificatie-scores-doorgeven/%s/'  # inschrijving_pk
    url_check_lijst = '/wedstrijden/manager/check-kwalificatie-scores/%s/'                  # wedstrijd_pk
    url_check_wedstrijd = '/wedstrijden/manager/check-kwalificatie-scores/wedstrijd/%s/'    # score_pk
    url_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/'             # deelcomp_pk, sporterboog_pk

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

        self.functie_hwl = maak_functie('HWL 1000', rol='HWL')
        self.functie_hwl.vereniging = ver
        self.functie_hwl.save(update_fields=['vereniging'])

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
                            status=INSCHRIJVING_STATUS_DEFINITIEF,
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

        # maak een test vereniging
        ver = Vereniging(
                    naam="Grotere Club",
                    ver_nr=1001,
                    regio=Regio.objects.get(pk=101))
        ver.save()
        self.ver2 = ver

    def test_anon(self):
        resp = self.client.get(self.url_check_lijst % 999999)
        self.assert403(resp, 'Geen toegang')

        resp = self.client.get(self.url_check_wedstrijd % 999999)
        self.assert403(resp, 'Geen toegang')

    def _store_kwalificatiescores(self):

        self.assertEqual(0, Kwalificatiescore.objects.count())

        # log in as sporter 1 en store qualification score
        self.e2e_login(self.account_sporter1)

        url = self.url_kwalificatie_scores % self.inschrijving1.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '123'})
        self.assert_is_redirect(resp, '/plein/')

        self.assertEqual(3, Kwalificatiescore.objects.count())

        # log in as sporter 2 en store qualification score
        self.e2e_login(self.account_sporter2)

        url = self.url_kwalificatie_scores % self.inschrijving2.pk
        with self.assert_max_queries(20):
            resp = self.client.post(url, {'score1_datum': self.kwalificatie_datum,
                                          'score1_naam': 'Test naam',
                                          'score1_waar': 'Test plaats',
                                          'score1_result': '234'})
        self.assert_is_redirect(resp, '/plein/')

        self.assertEqual(6, Kwalificatiescore.objects.count())

    def test_check_lijst(self):
        # toon de lijst met kwalificatie-scores opgegeven voor een specifieke wedstrijd

        self._store_kwalificatiescores()

        # wissel naar de Manager Wedstrijdzaken
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_mwz)

        url = self.url_check_lijst % self.wedstrijd.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/check-kwalificatie-scores.dtl', 'plein/site_layout.dtl'))

        # als HWL van de organiserende vereniging
        self.e2e_wissel_naar_functie(self.functie_hwl)

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/check-kwalificatie-scores.dtl', 'plein/site_layout.dtl'))

        # corner cases
        resp = self.client.get(self.url_check_lijst % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # corner case: verkeerde HWL
        self.wedstrijd.organiserende_vereniging = self.ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Niet de organisator')

    def test_scores_goedkeuren_mwz(self):
        # check alle kwalificatie-scores gerelateerd aan dezelfde wedstrijd

        self._store_kwalificatiescores()

        # wissel naar de Manager Wedstrijdzaken
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_mwz)

        score = Kwalificatiescore.objects.filter(datum=self.kwalificatie_datum).first()
        url = self.url_check_wedstrijd % score.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/check-kwalificatie-scores-wedstrijd.dtl',
                                         'plein/site_layout.dtl'))

        # post zonder data
        resp = self.client.post(url)
        self.assert404(resp, 'Geen valide verzoek')

        # post met garbage
        resp = self.client.post(url, data={'dit is geen': 'JSON'})
        self.assert404(resp, 'Geen valide verzoek')

        # post met json maar foute inhoud
        json_data = {'niet_nodig': 'hoi'}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

        # keur een kwalificatiescore goed
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_NOG_DOEN)
        json_data = {'keuze': 1}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_GOED)
        self.assertIn('Goedgekeurd door', score.log)

        # keur een kwalificatiescore af
        json_data = {'keuze': 3}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_AFGEKEURD)
        self.assertIn('Afgekeurd door', score.log)

        # zet een kwalificatiescore terug naar "nog te doen"
        json_data = {'keuze': 2}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_NOG_DOEN)
        self.assertIn("Terug gezet naar 'nog te doen' door", score.log)

        # geen wijziging
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)

        # corner cases
        json_data = {'keuze': 999999}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.get(self.url_check_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        json_data = {'keuze': 1}
        resp = self.client.post(self.url_check_wedstrijd % 999999,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Wedstrijd niet gevonden')

    def test_scores_goedkeuren_hwl(self):
        # check alle kwalificatie-scores gerelateerd aan dezelfde wedstrijd

        self._store_kwalificatiescores()

        # wissel naar de Manager Wedstrijdzaken
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_hwl)

        score = Kwalificatiescore.objects.filter(datum=self.kwalificatie_datum).first()
        url = self.url_check_wedstrijd % score.pk

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('wedstrijden/check-kwalificatie-scores-wedstrijd.dtl',
                                         'plein/site_layout.dtl'))

        # post zonder data
        resp = self.client.post(url)
        self.assert404(resp, 'Geen valide verzoek')

        # post met garbage
        resp = self.client.post(url, data={'dit is geen': 'JSON'})
        self.assert404(resp, 'Geen valide verzoek')

        # post met json maar foute inhoud
        json_data = {'niet_nodig': 'hoi'}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

        # keur een kwalificatiescore goed
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_NOG_DOEN)
        json_data = {'keuze': 1}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_GOED)
        self.assertIn('Goedgekeurd door', score.log)

        # keur een kwalificatiescore af
        json_data = {'keuze': 3}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_AFGEKEURD)
        self.assertIn('Afgekeurd door', score.log)

        # zet een kwalificatiescore terug naar "nog te doen"
        json_data = {'keuze': 2}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        score = Kwalificatiescore.objects.get(pk=score.pk)
        self.assertEqual(score.check_status, KWALIFICATIE_CHECK_NOG_DOEN)
        self.assertIn("Terug gezet naar 'nog te doen' door", score.log)

        # geen wijziging
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)

        # corner cases
        json_data = {'keuze': 999999}
        resp = self.client.post(url,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Geen valide verzoek')

        resp = self.client.get(self.url_check_wedstrijd % 999999)
        self.assert404(resp, 'Wedstrijd niet gevonden')

        json_data = {'keuze': 1}
        resp = self.client.post(self.url_check_wedstrijd % 999999,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Wedstrijd niet gevonden')

        # corner case: verkeerde HWL
        self.wedstrijd.organiserende_vereniging = self.ver2
        self.wedstrijd.save(update_fields=['organiserende_vereniging'])

        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assert403(resp, 'Niet de organisator')


# end of file
