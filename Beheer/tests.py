# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import connection, reset_queries
from django.test import TestCase
from django.urls import reverse
from Overig.e2ehelpers import E2EHelpers


# updaten met dit commando:
#  for x in `./manage.py show_urls | rev | cut -d'/' -f2- | rev | grep '/beheer/'`; do echo "'$x/',"; done | grep -vE ':object_id>/|/add/|/autocomplete/'
BEHEER_PAGINAS=(
'/beheer/',
'/beheer/Account/account/',
'/beheer/Account/account/1/password/',
'/beheer/Account/account/1/change/',
'/beheer/Account/account/add/',
'/beheer/Account/accountemail/',
'/beheer/Account/accountemail/1/change/',
'/beheer/Account/accountemail/add/',
'/beheer/Account/hanterenpersoonsgegevens/',
'/beheer/Account/hanterenpersoonsgegevens/1/change/',
'/beheer/Account/hanterenpersoonsgegevens/add/',
'/beheer/BasisTypen/boogtype/',
'/beheer/BasisTypen/boogtype/1/change/',
'/beheer/BasisTypen/boogtype/add/',
'/beheer/BasisTypen/indivwedstrijdklasse/',
'/beheer/BasisTypen/indivwedstrijdklasse/1/change/',
'/beheer/BasisTypen/indivwedstrijdklasse/add/',
'/beheer/BasisTypen/leeftijdsklasse/',
'/beheer/BasisTypen/leeftijdsklasse/1/change/',
'/beheer/BasisTypen/leeftijdsklasse/add/',
'/beheer/BasisTypen/teamwedstrijdklasse/',
'/beheer/BasisTypen/teamwedstrijdklasse/1/change/',
'/beheer/BasisTypen/teamwedstrijdklasse/add/',
'/beheer/Competitie/competitie/',
'/beheer/Competitie/competitie/1/change/',
'/beheer/Competitie/competitie/add/',
'/beheer/Competitie/competitieklasse/',
'/beheer/Competitie/competitieklasse/1/change/',
'/beheer/Competitie/competitieklasse/add/',
'/beheer/Competitie/deelcompetitie/',
'/beheer/Competitie/deelcompetitie/1/change/',
'/beheer/Competitie/deelcompetitie/add/',
'/beheer/Competitie/deelcompetitieronde/',
'/beheer/Competitie/deelcompetitieronde/1/change/',
'/beheer/Competitie/deelcompetitieronde/add/',
'/beheer/Competitie/regiocompetitieschutterboog/',
'/beheer/Competitie/regiocompetitieschutterboog/1/change/',
'/beheer/Competitie/regiocompetitieschutterboog/add/',
'/beheer/Functie/functie/',
'/beheer/Functie/functie/1/change/',
'/beheer/Functie/functie/add/',
'/beheer/HistComp/histcompetitie/',
'/beheer/HistComp/histcompetitie/1/change/',
'/beheer/HistComp/histcompetitie/add/',
'/beheer/HistComp/histcompetitieindividueel/',
'/beheer/HistComp/histcompetitieindividueel/1/change/',
'/beheer/HistComp/histcompetitieindividueel/add/',
'/beheer/HistComp/histcompetitieteam/',
'/beheer/HistComp/histcompetitieteam/1/change/',
'/beheer/HistComp/histcompetitieteam/add/',
'/beheer/Logboek/logboekregel/',
'/beheer/Logboek/logboekregel/1/change/',
'/beheer/Logboek/logboekregel/add/',
'/beheer/Mailer/mailqueue/',
'/beheer/Mailer/mailqueue/1/change/',
'/beheer/Mailer/mailqueue/add/',
'/beheer/NhbStructuur/nhbcluster/',
'/beheer/NhbStructuur/nhbcluster/1/change/',
'/beheer/NhbStructuur/nhbcluster/add/',
'/beheer/NhbStructuur/nhblid/',
'/beheer/NhbStructuur/nhblid/1/change/',
'/beheer/NhbStructuur/nhblid/add/',
'/beheer/NhbStructuur/nhbrayon/',
'/beheer/NhbStructuur/nhbrayon/1/change/',
'/beheer/NhbStructuur/nhbrayon/add/',
'/beheer/NhbStructuur/nhbregio/',
'/beheer/NhbStructuur/nhbregio/1/change/',
'/beheer/NhbStructuur/nhbregio/add/',
'/beheer/NhbStructuur/nhbvereniging/',
'/beheer/NhbStructuur/nhbvereniging/1/change/',
'/beheer/NhbStructuur/nhbvereniging/add/',
'/beheer/Overig/sitefeedback/',
'/beheer/Overig/sitefeedback/1/change/',
'/beheer/Overig/sitefeedback/add/',
'/beheer/Overig/sitetijdelijkeurl/',
'/beheer/Overig/sitetijdelijkeurl/1/change/',
'/beheer/Overig/sitetijdelijkeurl/add/',
'/beheer/Records/besteindivrecords/',
'/beheer/Records/besteindivrecords/1/change/',
'/beheer/Records/besteindivrecords/add/',
'/beheer/Records/indivrecord/',
'/beheer/Records/indivrecord/1/change/',
'/beheer/Records/indivrecord/add/',
'/beheer/Schutter/schutterboog/',
'/beheer/Schutter/schutterboog/1/change/',
'/beheer/Schutter/schutterboog/add/',
'/beheer/Schutter/schuttervoorkeuren/',
'/beheer/Schutter/schuttervoorkeuren/1/change/',
'/beheer/Schutter/schuttervoorkeuren/add/',
'/beheer/Score/score/',
'/beheer/Score/score/1/change/',
'/beheer/Score/score/add/',
'/beheer/Score/scorehist/',
'/beheer/Score/scorehist/<path:object_id>/',
'/beheer/Score/scorehist/<path:object_id>/change/',
'/beheer/Score/scorehist/add/',
'/beheer/Wedstrijden/wedstrijd/',
'/beheer/Wedstrijden/wedstrijd/<path:object_id>/',
'/beheer/Wedstrijden/wedstrijd/<path:object_id>/change/',
'/beheer/Wedstrijden/wedstrijd/add/',
'/beheer/Wedstrijden/wedstrijdenplan/',
'/beheer/Wedstrijden/wedstrijdenplan/<path:object_id>/',
'/beheer/Wedstrijden/wedstrijdenplan/<path:object_id>/change/',
'/beheer/Wedstrijden/wedstrijdenplan/add/',
'/beheer/Wedstrijden/wedstrijdlocatie/',
'/beheer/Wedstrijden/wedstrijdlocatie/<path:object_id>/',
'/beheer/Wedstrijden/wedstrijdlocatie/<path:object_id>/change/',
'/beheer/Wedstrijden/wedstrijdlocatie/add/',
'/beheer/Wedstrijden/wedstrijduitslag/',
'/beheer/Wedstrijden/wedstrijduitslag/<path:object_id>/',
'/beheer/Wedstrijden/wedstrijduitslag/<path:object_id>/change/',
'/beheer/Wedstrijden/wedstrijduitslag/add/',
'/beheer/auth/group/',
'/beheer/auth/group/<path:object_id>/',
'/beheer/auth/group/<path:object_id>/change/',
'/beheer/auth/group/add/',
'/beheer/jsi18n/',
'/beheer/login/',
'/beheer/logout/',
'/beheer/password_change/',
'/beheer/r/<int:content_type_id>/<path:object_id>/',
)


class TestBeheer(E2EHelpers, TestCase):
    """ unit tests voor de Beheer applicatie """

    def setUp(self):
        """ initialisatie van de test case """
        self.account_admin = self.e2e_create_account_admin()

    def test_login(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:login')      # interne url
        self.assertEqual(url, '/beheer/login/')

        self.e2e_logout()
        resp = self.client.get('/beheer/login/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/', 302))

        resp = self.client.get('/beheer/login/?next=/records/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/login/?next=/records/', 302))

        self.e2e_assert_other_http_commands_not_supported('/beheer/login/')

    def test_index(self):
        # voordat 2FA verificatie gedaan is
        self.e2e_login(self.account_admin)

        # redirect naar wissel-van-rol pagina
        resp = self.client.get('/beheer/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/functie/otp-controle/?next=/beheer/', 302))

        self.e2e_assert_other_http_commands_not_supported('/beheer/')

        # na 2FA verificatie
        self.e2e_login_and_pass_otp(self.account_admin)
        resp = self.client.get('/beheer/', follow=True)
        self.assertTrue(len(resp.redirect_chain) == 0)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, '<title>Websitebeheer | Django-websitebeheer</title>')

        # onnodig via beheer-login naar post-authenticatie pagina
        resp = self.client.get('/beheer/login/?next=/records/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/records/', 302))

        # onnodig via beheer-login zonder post-authenticatie pagina
        resp = self.client.get('/beheer/login/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/plein/', 302))

    def test_logout(self):
        # controleer dat de admin login vervangen is door een redirect naar onze eigen login
        url = reverse('admin:logout')      # interne url
        self.assertEqual(url, '/beheer/logout/')

        self.e2e_login_and_pass_otp(self.account_admin)
        resp = self.client.get('/beheer/logout/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/logout/', 302))

    def test_pw_change(self):
        url = reverse('admin:password_change')
        self.assertEqual(url, '/beheer/password_change/')

        self.e2e_login_and_pass_otp(self.account_admin)

        resp = self.client.get(url, follow=True)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assertContains(resp, 'Nieuw wachtwoord')
        self.assertEqual(resp.redirect_chain[-1], ('/account/nieuw-wachtwoord/', 302))

    def _check_url_queries(self, url):
        reset_queries()

        # print('url: %s' % repr(url))
        resp = self.client.get(url)
        self.assertTrue(resp.status_code, 200)  # 200 = OK

        # TODO: hoeveel data zit er eigenlijk in de test database?
        if len(connection.queries) > 15:
            msg = 'Veel (%s) queries voor url %s' % (len(connection.queries), url)
            for query in connection.queries:
                msg += '\n%s' % query
            # for
            self.fail(msg=msg)

        self.assertTrue(len(connection.queries) < 20)

    def test_queries(self):
        settings.DEBUG = True
        self.e2e_login_and_pass_otp(self.account_admin)

        for url in BEHEER_PAGINAS:
            self._check_url_queries(url)
            self._check_url_queries(url + 'add/')
            self._check_url_queries(url + '1/change/')
        # for

        settings.DEBUG = False

# end of file
