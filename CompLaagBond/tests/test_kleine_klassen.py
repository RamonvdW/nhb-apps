# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Competitie.models import CompetitieIndivKlasse, KampioenschapSporterBoog, CompetitieMutatie
from Competitie.test_utils.tijdlijn import zet_competitie_fase_bk_klein, zet_competitie_fase_rk_wedstrijden
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import json


class TestCompLaagBondKleineKlassen(E2EHelpers, TestCase):

    """ tests voor de CompLaagBond applicatie, Kleine Klassen views """

    test_after = ('Competitie.tests.test_overzicht', 'CompBeheer.tests.test_bko')

    url_samenvoegen = '/bondscompetities/bk/kleine-klassen-samenvoegen/%s/indiv/'    # deelkamp_pk
    url_verplaats = '/bondscompetities/bk/verplaats-deelnemer/'

    testdata = None
    klasse1 = None

    @classmethod
    def setUpTestData(cls):
        print('%s: populating testdata start' % cls.__name__)
        s1 = timezone.now()

        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()
        data.maak_bondscompetities()

        for regio_nr in (111, 113):
            ver_nr = data.regio_ver_nrs[regio_nr][0]
            data.maak_rk_deelnemers(18, ver_nr, regio_nr, limit_boogtypen=['R', 'BB'])
        # for

        data.maak_uitslag_rk_indiv(18)
        data.maak_bk_deelnemers(18)

        # verplaats 4 van 6 sporters in 1111 (R O21 kl 2) naar 1110 (R O21 kl 1)
        cls.klasse1 = CompetitieIndivKlasse.objects.get(competitie=data.comp18, volgorde=1110)
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(indiv_klasse__volgorde=1111,
                                  kampioenschap=data.deelkamp18_bk)
                          .order_by('sporterboog__sporter__lid_nr'))[:4]:
            deelnemer.indiv_klasse = cls.klasse1
            deelnemer.save(update_fields=['indiv_klasse'])
        # for

        # zet de competities in fase N
        zet_competitie_fase_bk_klein(data.comp18)

        s2 = timezone.now()
        d = s2 - s1
        print('%s: populating testdata took %.1f seconds' % (cls.__name__, d.total_seconds()))

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)
        self.e2e_check_rol('BKO')

    def test_anon(self):
        self.client.logout()

        resp = self.client.get(self.url_samenvoegen % 999999)
        self.assert_is_redirect_login(resp)

        resp = self.client.post(self.url_verplaats)
        self.assert_is_redirect_login(resp)

    def test_lijst(self):
        # ingelogd als BKO Indoor
        resp = self.client.get(self.url_samenvoegen % 999999)
        self.assert404(resp, 'Kampioenschap niet gevonden')

        resp = self.client.get(self.url_samenvoegen % self.testdata.deelkamp25_bk.pk)
        self.assert403(resp, 'Niet de beheerder')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_samenvoegen % self.testdata.deelkamp18_bk.pk)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagbond/kleine-klassen-indiv.dtl', 'design/site_layout.dtl'))

        # verkeerde competitie fase
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        resp = self.client.get(self.url_samenvoegen % self.testdata.deelkamp18_bk.pk)
        self.assert404(resp, 'Verkeerde competitie fase')

        self.e2e_assert_other_http_commands_not_supported(self.url_samenvoegen % 999999)

    def test_verplaats(self):
        # ingelogd als BKO Indoor

        # zonder data
        resp = self.client.post(self.url_verplaats)
        self.assert404(resp, 'Geen valide verzoek')

        # bad: geen deelnemer of klasse
        json_data = {'test': 'hoi'}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Deelnemer niet gevonden')

        # niet bestaand
        json_data = {'deelnemer': 99999}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Deelnemer niet gevonden')

        # bad: geen klasse
        json_data = {'deelnemer': self.testdata.comp18_bk_deelnemers[0].pk}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Klasse niet gevonden')

        json_data = {'deelnemer': self.testdata.comp18_bk_deelnemers[0].pk,
                     'klasse': 999999}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Klasse niet gevonden')

        # goed
        self.assertEqual(0, CompetitieMutatie.objects.count())
        json_data = {'deelnemer': self.testdata.comp18_bk_deelnemers[0].pk,
                     'klasse': self.klasse1.pk}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert200_json(resp)
        self.assertEqual(1, CompetitieMutatie.objects.count())

        # verkeerde competitie fase
        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)
        json_data = {'deelnemer': self.testdata.comp18_bk_deelnemers[0].pk}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert404(resp, 'Verkeerde competitie fase')

        # repeat voor 25m1pijl
        self.e2e_wissel_naar_functie(self.testdata.comp25_functie_bko)

        json_data = {'deelnemer': self.testdata.comp18_bk_deelnemers[0].pk}
        resp = self.client.post(self.url_verplaats,
                                json.dumps(json_data),
                                content_type='application/json')
        self.assert403(resp, 'Niet de beheerder')

        self.e2e_assert_other_http_commands_not_supported(self.url_verplaats, get=True, post=False)

# end of file
