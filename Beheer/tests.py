# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.admin.models import LogEntry
from Beheer.views import beheer_opschonen
from Geo.models import Regio
from Betaal.models import BetaalActief, BetaalInstellingenVereniging
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
import datetime
import io


# updaten met dit commando:
# noqa: for x in `./manage.py show_urls --settings=SiteMain.settings_dev | rev | cut -d'/' -f2- | rev | grep '/beheer/'`; do echo "'$x/',"; done | grep -vE ':object_id>/|/add/|/autocomplete/|<app_label>|<id>|bondscompetities/beheer/'
BEHEER_URLS = (
    '/beheer/Account/account/',
    '/beheer/Account/accountverzoekenteller/',
    '/beheer/BasisTypen/boogtype/',
    '/beheer/BasisTypen/kalenderwedstrijdklasse/',
    '/beheer/BasisTypen/leeftijdsklasse/',
    '/beheer/BasisTypen/teamtype/',
    '/beheer/BasisTypen/templatecompetitieindivklasse/',
    '/beheer/BasisTypen/templatecompetitieteamklasse/',
    '/beheer/Bestelling/bestelling/',
    '/beheer/Bestelling/bestellingmandje/',
    '/beheer/Bestelling/bestellingmutatie/',
    '/beheer/Bestelling/bestellingproduct/',
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
    '/beheer/Evenement/evenement/',
    '/beheer/Evenement/evenementafgemeld/',
    '/beheer/Evenement/evenementinschrijving/',
    '/beheer/Feedback/feedback/',
    '/beheer/Functie/functie/',
    '/beheer/Functie/verklaringhanterenpersoonsgegevens/',
    '/beheer/Geo/cluster/',
    '/beheer/Geo/rayon/',
    '/beheer/Geo/regio/',
    '/beheer/HistComp/histcompregioindiv/',
    '/beheer/HistComp/histcompregioteam/',
    '/beheer/HistComp/histcompseizoen/',
    '/beheer/HistComp/histkampindivbk/',
    '/beheer/HistComp/histkampindivrk/',
    '/beheer/HistComp/histkampteam/',
    '/beheer/Locatie/evenementlocatie/',
    '/beheer/Locatie/reistijd/',
    '/beheer/Locatie/wedstrijdlocatie/',
    '/beheer/Logboek/logboekregel/',
    '/beheer/Mailer/mailqueue/',
    '/beheer/Opleidingen/opleiding/',
    '/beheer/Opleidingen/opleidingdeelnemer/',
    '/beheer/Opleidingen/opleidingdiploma/',
    '/beheer/Opleidingen/opleidingmoment/',
    '/beheer/Records/anderrecord/',
    '/beheer/Records/besteindivrecords/',
    '/beheer/Records/indivrecord/',
    '/beheer/Registreer/gastlidnummer/',
    '/beheer/Registreer/gastregistratie/',
    '/beheer/Registreer/gastregistratieratetracker/',
    '/beheer/Scheidsrechter/matchscheidsrechters/',
    '/beheer/Scheidsrechter/scheidsbeschikbaarheid/',
    '/beheer/Scheidsrechter/scheidsmutatie/',
    '/beheer/Scheidsrechter/wedstrijddagscheidsrechters/',
    '/beheer/Score/aanvangsgemiddelde/',
    '/beheer/Score/aanvangsgemiddeldehist/',
    '/beheer/Score/score/',
    '/beheer/Score/scorehist/',
    '/beheer/Score/uitslag/',
    '/beheer/Spelden/speld/',
    '/beheer/Spelden/speldaanvraag/',
    '/beheer/Spelden/speldbijlage/',
    '/beheer/Spelden/speldscore/',
    '/beheer/Sporter/speelsterkte/',
    '/beheer/Sporter/sporter/',
    '/beheer/Sporter/sporterboog/',
    '/beheer/Sporter/sportervoorkeuren/',
    '/beheer/Taken/taak/',
    '/beheer/TijdelijkeCodes/tijdelijkecode/',
    '/beheer/Vereniging/secretaris/',
    '/beheer/Vereniging/vereniging/',
    '/beheer/Webwinkel/webwinkelfoto/',
    '/beheer/Webwinkel/webwinkelkeuze/',
    '/beheer/Webwinkel/webwinkelproduct/',
    '/beheer/Wedstrijden/kwalificatiescore/',
    '/beheer/Wedstrijden/wedstrijd/',
    '/beheer/Wedstrijden/wedstrijdinschrijving/',
    '/beheer/Wedstrijden/wedstrijdkorting/',
    '/beheer/Wedstrijden/wedstrijdsessie/',
    '/beheer/auth/group/',
    '/beheer/jsi18n/',
    '/beheer/login/',
    '/beheer/logout/',
    '/beheer/password_change/',
    '/beheer/sessions/session/',
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

    def test_index(self):
        # voordat 2FA verificatie gedaan is
        self.e2e_login(self.account_admin)

        # redirect naar wissel-van-rol pagina
        with self.assert_max_queries(20):
            resp = self.client.get('/beheer/', follow=True)
        self.assertEqual(resp.redirect_chain[-1], ('/account/otp-controle/?next=/beheer/', 302))

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

        for url in BEHEER_URLS:
            try:
                with self.assert_max_queries(20):
                    self.client.get(url)

                with self.assert_max_queries(20):
                    self.client.get(url + 'add/')

                with self.assert_max_queries(20):
                    self.client.get(url + '1/change/')
            except AttributeError:      # pragma: no cover
                self.fail('AttributeError on url %s' % repr(url))
        # for

        settings.DEBUG = False

    def test_admin_specials(self):
        self.e2e_login_and_pass_otp(self.account_admin)

        regio = Regio.objects.get(regio_nr=111)

        ver = Vereniging(ver_nr=1234, naam='Test', regio=regio)
        ver.save()

        ontvanger = BetaalInstellingenVereniging(
                        vereniging=ver,
                        mollie_api_key='',
                        akkoord_via_bond=True)
        ontvanger.save()

        actief = BetaalActief(
                    ontvanger=ontvanger,
                    payment_id='12345')
        actief.save()

        urls = (
            # Betaal
            '/beheer/Betaal/betaalinstellingenvereniging/?Mollie=0',
            '/beheer/Betaal/betaalinstellingenvereniging/?Mollie=1',
            '/beheer/Betaal/betaaltransactie/?heeft_restitutie=ja',
            '/beheer/Betaal/betaaltransactie/?heeft_restitutie=ja&heeft_terugvordering=ja',
            '/beheer/Betaal/betaalactief/?ontvanger=',
            '/beheer/Betaal/betaalactief/?ontvanger=1234',

            # Bestelling
            '/beheer/Bestelling/bestellingmandje/?is_leeg=0',       # noqa
            '/beheer/Bestelling/bestellingmandje/?is_leeg=1',       # noqa

            # Sporter
            '/beheer/Sporter/sporter/?heeft_wa_id=Ja',
            '/beheer/Sporter/sporter/?heeft_account=Ja',

            # Opleiding
            '/beheer/Opleidingen/opleidingdiploma/?heeft_account=Ja',

            # Reistijden
            '/beheer/Locatie/reistijd/?reistijd_vastgesteld=nul',
            '/beheer/Locatie/reistijd/?reistijd_vastgesteld=1',

            # Competitie
            '/beheer/Competitie/regiocompetitiesporterboog/?Zelfstandig=HWL',
            '/beheer/Competitie/regiocompetitiesporterboog/?Zelfstandig=Zelf',
            '/beheer/Competitie/regiocompetitiesporterboog/?TeamAG=Ontbreekt',
            '/beheer/Competitie/regiocompetitieteam/?TeamType=R2',
            '/beheer/Competitie/regiocompetitierondeteam/?RondeTeamType=R2',
            '/beheer/Competitie/regiocompetitierondeteam/?RondeTeamVer=1350',
            '/beheer/Competitie/kampioenschapteam/?rk_bk_type=RK',
            '/beheer/Competitie/kampioenschapteam/?rk_bk_type=BK',
            '/beheer/Competitie/kampioenschapteam/?incompleet=incompleet',
            '/beheer/Competitie/kampioenschapteam/?incompleet=compleet',
            '/beheer/Competitie/kampioenschapsporterboog/',
            '/beheer/Competitie/kampioenschapsporterboog/?indiv_klasse_rk_bk=1100',
        )

        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)     # 200 = OK
            self.assert_template_used(resp, ('admin/base.html', 'admin/filter.html'))
        # for

    def test_opschonen(self):

        lang_geleden = timezone.now() - datetime.timedelta(days=365)

        LogEntry(
            action_time=lang_geleden,
            user=self.account_admin,
            object_repr='test',
            action_flag=1).save()

        stdout = io.StringIO()
        beheer_opschonen(stdout)

        # geen records meer om op te schonen
        beheer_opschonen(stdout)

# end of file
