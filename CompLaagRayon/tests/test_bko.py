# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import KampioenschapSporterBoog, CompetitieMutatie
from Competitie.test_utils.tijdlijn import (zet_competitie_fase_rk_prep, zet_competitie_fase_regio_afsluiten,
                                            zet_competitie_fase_rk_wedstrijden)
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonBko(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, BKO functies """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_extra_deelnemer = '/bondscompetities/rk/%s/extra-deelnemer/'                    # comp_pk
    url_extra_toevoegen = '/bondscompetities/rk/%s/extra-deelnemer/%s/toevoegen/'       # comp_pk, deelnemer_pk
    url_blanco = '/bondscompetities/rk/%s/blanco-resultaat/'                            # comp_pk
    url_blanco_toevoegen = '/bondscompetities/rk/%s/blanco-resultaat/%s/toevoegen/'     # deelnemer_pk

    testdata = None
    rayon_nr = 1
    regio_nr = 102
    ver_nr = None
    deelnemer_geen_ver = None

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()
        data.maak_clubs_en_sporters()       # maakt account_beheerders, die nodig is voor BKO
        cls.ver_nr = data.regio_ver_nrs[cls.regio_nr][0]
        data.maak_bondscompetities()
        data.maak_inschrijvingen_regiocompetitie(18, cls.ver_nr)
        data.geef_regio_deelnemers_genoeg_scores_voor_rk(18)
        zet_competitie_fase_rk_prep(data.comp18)

        # plaats 2 sporterboog in een RK, in dezelfde klasse
        klasse = data.comp18_klassen_indiv['R'][0]
        # nr = 0
        # for deelnemer in data.comp18_deelnemers:
        #     print('[%s] deelnemer: %s' % (nr, deelnemer))
        #     nr += 1
        # # for
        deelnemer1 = data.comp18_deelnemers[24]         # 24=Sen21 (R)
        # print('deelnemer1: %s' % repr(deelnemer1))
        deelnemer2 = data.comp18_deelnemers[27]         # 27=Sen22 (R)
        # print('deelnemer2: %s' % repr(deelnemer2))

        KampioenschapSporterBoog(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                    sporterboog=deelnemer1.sporterboog,
                    indiv_klasse=klasse,
                    bij_vereniging=deelnemer1.bij_vereniging).save()

        KampioenschapSporterBoog(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                    sporterboog=deelnemer2.sporterboog,
                    indiv_klasse=klasse,
                    bij_vereniging=None).save()     # deelnemer2.bij_vereniging
        deelnemer2.sporterboog.sporter.bij_vereniging = None
        deelnemer2.sporterboog.sporter.save(update_fields=['bij_vereniging'])

        # gooi 1 sporter uit de vereniging
        cls.deelnemer_geen_ver = data.comp18_deelnemers[1]
        sporter = cls.deelnemer_geen_ver.sporterboog.sporter
        sporter.bij_vereniging = None
        sporter.save(update_fields=['bij_vereniging'])

    def setUp(self):
        """ eenmalige setup voor alle tests
            wordt als eerste aangeroepen
        """
        pass

    def test_anon(self):
        resp = self.client.get(self.url_extra_deelnemer % 999999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_extra_toevoegen % (999999, 999999))
        self.assert403(resp, "Geen toegang")

        resp = self.client.post(self.url_extra_deelnemer % 999999)
        self.assert403(resp, "Geen toegang")

        resp = self.client.post(self.url_extra_toevoegen % (999999, 999999))
        self.assert403(resp, "Geen toegang")

        resp = self.client.get(self.url_blanco % self.testdata.comp18.pk)
        self.assert403(resp, "Geen toegang")

        resp = self.client.post(self.url_blanco % self.testdata.comp18.pk)
        self.assert403(resp, "Geen toegang")

    def test_extra_deelnemer(self):
        # wissel naar BKO
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)

        url = self.url_extra_deelnemer % self.testdata.comp18.pk
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/bko-extra-deelnemer.dtl', 'plein/site_layout.dtl'))

        # deelnemer_pk ontbreekt via 2e url
        resp = self.client.post(url)
        self.assert404(resp, "Sporter niet gevonden")

        url = self.url_extra_toevoegen % (self.testdata.comp18.pk, self.deelnemer_geen_ver.pk)
        resp = self.client.post(url)
        self.assert404(resp, "Geen vereniging")

        # nu echt toevoegen
        self.assertEqual(0, CompetitieMutatie.objects.count())
        deelnemer = self.testdata.comp18_deelnemers[2]
        url = self.url_extra_toevoegen % (self.testdata.comp18.pk, deelnemer.pk)
        resp = self.client.post(url, {'snel': 1})
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, CompetitieMutatie.objects.count())

        # nog een keer toevoegen
        url = self.url_extra_toevoegen % (self.testdata.comp18.pk, deelnemer.pk)
        resp = self.client.post(url)
        self.assert_is_redirect_not_plein(resp)
        self.assertEqual(1, CompetitieMutatie.objects.count())

        # error handling
        url = self.url_extra_deelnemer % 999999
        resp = self.client.get(url)
        self.assert404(resp, "Competitie niet gevonden")

        url = self.url_extra_deelnemer % 999999
        resp = self.client.post(url)
        self.assert404(resp, "Competitie niet gevonden")

        # verkeerde beheerder
        url = self.url_extra_deelnemer % self.testdata.comp25.pk
        resp = self.client.get(url)
        self.assert403(resp, "Niet de beheerder")

        resp = self.client.post(url)
        self.assert403(resp, "Niet de beheerder")

        # verkeerder fase
        zet_competitie_fase_regio_afsluiten(self.testdata.comp18)

        url = self.url_extra_deelnemer % self.testdata.comp18.pk
        resp = self.client.get(url)
        self.assert404(resp, "Verkeerde fase")

        resp = self.client.post(url)
        self.assert404(resp, "Verkeerde fase")

    def test_blanco(self):
        # BKO geeft RK deelnemer zonder resultaat een "blanco score"
        self.e2e_login_and_pass_otp(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(self.testdata.comp18_functie_bko)

        # niet bestaande competitie
        resp = self.client.get(self.url_blanco % 999999)
        self.assert404(resp, "Competitie niet gevonden")

        resp = self.client.post(self.url_blanco % 999999)
        self.assert404(resp, "Competitie niet gevonden")

        # verkeerde competitie fase
        resp = self.client.get(self.url_blanco % self.testdata.comp18.pk)
        self.assert404(resp, "Verkeerde fase")

        resp = self.client.post(self.url_blanco % self.testdata.comp18.pk)
        self.assert404(resp, "Verkeerde fase")

        # verkeerde BKO
        resp = self.client.get(self.url_blanco % self.testdata.comp25.pk)
        self.assert403(resp, "Niet de beheerder")

        resp = self.client.post(self.url_blanco % self.testdata.comp25.pk)
        self.assert403(resp, "Niet de beheerder")

        zet_competitie_fase_rk_wedstrijden(self.testdata.comp18)

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_blanco % self.testdata.comp18.pk)
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('complaagrayon/bko-blanco-resultaat.dtl', 'plein/site_layout.dtl'))

        # aanpassing doorvoeren
        kamp = KampioenschapSporterBoog.objects.exclude(bij_vereniging=None).first()
        # print('kamp: %s' % kamp)
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_blanco_toevoegen % (self.testdata.comp18.pk, kamp.pk))
        self.assert_is_redirect(resp, self.url_blanco % self.testdata.comp18.pk)

        resp = self.client.post(self.url_blanco_toevoegen % (self.testdata.comp18.pk, 99999))
        self.assert404(resp, 'Deelnemer niet gevonden')

        # verkeerde URL, komt toch bij POST handler
        resp = self.client.post(self.url_blanco % self.testdata.comp18.pk)
        self.assert404(resp, 'Deelnemer niet gevonden')

        # geen ver
        kamp = KampioenschapSporterBoog.objects.filter(bij_vereniging=None).first()
        with self.assert_max_queries(20):
            resp = self.client.post(self.url_blanco_toevoegen % (self.testdata.comp18.pk, kamp.pk))
        self.assert404(resp, 'Geen vereniging')

        self.e2e_assert_other_http_commands_not_supported(self.url_blanco, post=False)

# end of file
