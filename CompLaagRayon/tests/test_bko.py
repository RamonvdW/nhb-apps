# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Competitie.models import KampioenschapSporterBoog, CompetitieMutatie
from Competitie.tijdlijn import zet_competitie_fase_rk_prep, zet_competitie_fase_regio_afsluiten
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestCompLaagRayonBko(E2EHelpers, TestCase):

    """ tests voor de CompLaagRayon applicatie, BKO functies """

    test_after = ('Competitie.tests.test_overzicht', 'Competitie.tests.test_tijdlijn')

    url_extra_deelnemer = '/bondscompetities/rk/%s/extra-deelnemer/'                    # comp_pk
    url_extra_toevoegen = '/bondscompetities/rk/%s/extra-deelnemer/%s/toevoegen/'       # comp_pk, deelnemer_pk

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

        # plaats 1 sporterboog alvast in een RK
        deelnemer = data.comp18_deelnemers[0]
        # print('deelnemer: %s' % repr(deelnemer))
        kamp = KampioenschapSporterBoog(
                    kampioenschap=data.deelkamp18_rk[cls.rayon_nr],
                    sporterboog=deelnemer.sporterboog,
                    indiv_klasse=data.comp18_klassen_indiv['R'][0],
                    bij_vereniging=deelnemer.bij_vereniging)
        kamp.save()

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




# end of file
