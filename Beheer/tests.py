# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from TestHelpers.e2ehelpers import E2EHelpers


# updaten met dit commando:
#  for x in `./manage.py show_urls --settings=nhbapps.settings_dev | rev | cut -d'/' -f2- | rev | grep '/beheer/'`; do echo "'$x/',"; done | grep -vE ':object_id>/|/add/|/autocomplete/|<app_label>|<id>|bondscompetities/beheer/'
BEHEER_PAGINAS = (
    '/beheer/Account/account/',
    '/beheer/Account/accountemail/',
    '/beheer/Account/accountverzoekenteller/',
    '/beheer/BasisTypen/boogtype/',
    '/beheer/BasisTypen/kalenderwedstrijdklasse/',
    '/beheer/BasisTypen/leeftijdsklasse/',
    '/beheer/BasisTypen/teamtype/',
    '/beheer/BasisTypen/templatecompetitieindivklasse/',
    '/beheer/BasisTypen/templatecompetitieteamklasse/',
    '/beheer/Bestel/bestelling/',
    '/beheer/Bestel/bestelmandje/',
    '/beheer/Bestel/bestelmutatie/',
    '/beheer/Bestel/bestelproduct/',
    '/beheer/Betaal/betaalactief/',
    '/beheer/Betaal/betaalinstellingenvereniging/',
    '/beheer/Betaal/betaalmutatie/',
    '/beheer/Betaal/betaaltransactie/',
    '/beheer/Competitie/competitie/',
    '/beheer/Competitie/competitieindivklasse/',
    '/beheer/Competitie/competitiematch/',
    '/beheer/Competitie/competitiemutatie/',
    '/beheer/Competitie/competitieteamklasse/',
    '/beheer/Competitie/kampioenschap/',
    '/beheer/Competitie/kampioenschapindivklasselimiet/',
    '/beheer/Competitie/kampioenschapsporterboog/',
    '/beheer/Competitie/kampioenschapteam/',
    '/beheer/Competitie/kampioenschapteamklasselimiet/',
    '/beheer/Competitie/regiocompetitie/',
    '/beheer/Competitie/regiocompetitieronde/',
    '/beheer/Competitie/regiocompetitierondeteam/',
    '/beheer/Competitie/regiocompetitiesporterboog/',
    '/beheer/Competitie/regiocompetitieteam/',
    '/beheer/Competitie/regiocompetitieteampoule/',
    '/beheer/Feedback/feedback/',
    '/beheer/Functie/functie/',
    '/beheer/Functie/verklaringhanterenpersoonsgegevens/',
    '/beheer/HistComp/histcompetitie/',
    '/beheer/HistComp/histcompetitieindividueel/',
    '/beheer/HistComp/histcompetitieteam/',
    '/beheer/Logboek/logboekregel/',
    '/beheer/Mailer/mailqueue/',
    '/beheer/NhbStructuur/nhbcluster/',
    '/beheer/NhbStructuur/nhbrayon/',
    '/beheer/NhbStructuur/nhbregio/',
    '/beheer/NhbStructuur/nhbvereniging/',
    '/beheer/Opleidingen/opleiding/',
    '/beheer/Opleidingen/opleidingdeelnemer/',
    '/beheer/Opleidingen/opleidingdiploma/',
    '/beheer/Opleidingen/opleidingmoment/',
    '/beheer/Overig/sitetijdelijkeurl/',
    '/beheer/Records/besteindivrecords/',
    '/beheer/Records/indivrecord/',
    '/beheer/Score/aanvangsgemiddelde/',
    '/beheer/Score/aanvangsgemiddeldehist/',
    '/beheer/Score/score/',
    '/beheer/Score/scorehist/',
    '/beheer/Score/uitslag/',
    '/beheer/Sporter/speelsterkte/',
    '/beheer/Sporter/sporter/',
    '/beheer/Sporter/sporterboog/',
    '/beheer/Sporter/sportervoorkeuren/',
    '/beheer/Taken/taak/',
    '/beheer/Vereniging/secretaris/',
    '/beheer/Webwinkel/webwinkelfoto/',
    '/beheer/Webwinkel/webwinkelkeuze/',
    '/beheer/Webwinkel/webwinkelproduct/',
    '/beheer/Wedstrijden/wedstrijd/',
    '/beheer/Wedstrijden/wedstrijdinschrijving/',
    '/beheer/Wedstrijden/wedstrijdkorting/',
    '/beheer/Wedstrijden/wedstrijdlocatie/',
    '/beheer/Wedstrijden/wedstrijdsessie/',
    '/beheer/auth/group/',
    '/beheer/jsi18n/',
    '/beheer/login/',
    '/beheer/logout/',
    '/beheer/password_change/',
)


class TestBeheer(E2EHelpers, TestCase):

    """ tests voor de Beheer applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()

    def test_login(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:login')      # interne url
        self.assertEqual(url, '/beheer/login/')

        self.e2e_logout()
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/login/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/', 302))

        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/login/?next=/records/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/?next=/records/', 302))

        self.e2e_assert_other_http_commands_not_supported('/beheer/login/')

    def test_index(self):
        # voordat 2FA verificatie gedaan is
        self.e2e_login(self.account_admin)

        # redirect naar wissel-van-rol pagina
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/functie/otp-controle/?next=/beheer/', 302))

        self.e2e_assert_other_http_commands_not_supported('/beheer/')

        # na 2FA verificatie
        self.e2e_login_and_pass_otp(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/', follow=True)
        self.assertTrue(len(resp.redirect_chain) == 0)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '<title>Admin Site</title>')

        # onnodig via beheer-login naar post-authenticatie pagina
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/login/?next=/records/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/records/', 302))

        # onnodig via beheer-login zonder post-authenticatie pagina
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/login/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/plein/', 302))

    def test_logout(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:logout')      # interne url
        self.assertEqual(url, '/beheer/logout/')

        self.e2e_login_and_pass_otp(self.account_admin)
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/logout/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/logout/', 302))

    def test_pw_change(self):
        url = reverse('admin:password_change')
        self.assertEqual(url, '/beheer/password_change/')

        self.e2e_login_and_pass_otp(self.account_admin)

        with self.assert_max_queries(20):
            resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Nieuw wachtwoord')
        self.assertEqual(resp.redirect_chain[-1], ('/account/nieuw-wachtwoord/', 302))

    def test_queries(self):
        # TODO: zorg dat er van elk type record 1 bestaat

        # controleer dat alle beheer pagina's het goed doen
        settings.DEBUG = True
        self.e2e_login_and_pass_otp(self.account_admin)

        for url in BEHEER_PAGINAS:
            # print(url)
            with self.assert_max_queries(20):
                self.client.get(url)

            with self.assert_max_queries(20):
                self.client.get(url + 'add/')

            with self.assert_max_queries(20):
                self.client.get(url + '1/change/')
        # for

        settings.DEBUG = False

# end of file
