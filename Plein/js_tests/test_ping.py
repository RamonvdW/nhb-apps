# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore
from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Account.models import Account
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Regio, Rayon
from Plein.views import SESSIONVAR_VORIGE_POST
from Sporter.models import Sporter
from Vereniging.models import Vereniging
import datetime
import pyotp
import time


class TestPleinStuurPing(bh.BrowserTestCase):

    """ Test de Plein applicatie, gebruik van stuur_ping.js vanuit de browser """

    port = bh.port

    url_root = bh.url_root
    url_plein = url_root + '/plein/'
    url_login = url_root + '/account/login/'
    url_otp = url_root + '/account/otp-controle/'
    url_wissel_van_rol = url_root + '/functie/wissel-van-rol/'

    def _database_vullen(self):
        Account.objects.filter(username='424200').delete()
        self.account = Account.objects.create(
                                    username='424200',
                                    first_name='Bro',
                                    last_name='dés Browser',
                                    unaccented_naam='Bro des Browser',
                                    bevestigde_email='bro@test.not',
                                    email_is_bevestigd=True,
                                    otp_code='whatever',
                                    otp_is_actief=True)
        self.account.set_password(TEST_WACHTWOORD)
        self.account.save()

        self.vhpg = VerklaringHanterenPersoonsgegevens.objects.create(
                                                    account=self.account,
                                                    acceptatie_datum=timezone.now())

        self.rayon, _ = Rayon.objects.get_or_create(rayon_nr=5, naam="Rayon 5")
        self.regio, _ = Regio.objects.get_or_create(regio_nr=117, rayon_nr=self.rayon.rayon_nr, rayon=self.rayon)

        self.ver, _ = Vereniging.objects.get_or_create(
                                    naam="Browser Club",
                                    ver_nr=4200,
                                    regio=self.regio)

        Sporter.objects.filter(lid_nr=100001).delete()
        self.sporter = Sporter.objects.create(
                                    lid_nr=100001,
                                    geslacht="V",
                                    voornaam="Bro",
                                    achternaam="de Browser",
                                    geboorte_datum=datetime.date(year=1988, month=8, day=8),
                                    sinds_datum=datetime.date(year=2020, month=8, day=8),
                                    bij_vereniging=self.ver,
                                    account=self.account,
                                    email=self.account.email)

        self.functie_hwl, _ = Functie.objects.get_or_create(
                                    rol='HWL',
                                    beschrijving='HWL 4200',
                                    bevestigde_email='hwl4200@test.not',
                                    vereniging=self.ver)
        self.functie_hwl.accounts.add(self.account)

    def _database_opschonen(self):
        self.functie_hwl.delete()
        self.sporter.delete()
        self.vhpg.delete()
        self.account.delete()
        self.ver.delete()
        self.regio.delete()
        self.rayon.delete()

    def _login(self):
        # log in
        self.driver.get(self.url_login)
        bh.find_element_by_id(self.driver, 'id_login_naam').send_keys(self.account.username)
        bh.find_element_by_id(self.driver, 'id_wachtwoord').send_keys(TEST_WACHTWOORD)
        login_vink = bh.find_element_by_name(self.driver, 'aangemeld_blijven')
        self.assertTrue(login_vink.is_selected())
        bh.find_element_by_id(self.driver, 'submit_knop').click()
        bh.wait_until_url_not(self.driver, self.url_login)

    def _otp_controle(self):
        # pass otp
        self.driver.get(self.url_otp)
        otp_code = pyotp.TOTP(self.account.otp_code).now()
        bh.find_element_by_id(self.driver, 'id_otp_code').send_keys(otp_code)
        bh.find_element_by_id(self.driver, 'submit_knop').click()
        bh.wait_until_url_not(self.driver, self.url_otp)

    def _wissel_naar_hwl(self):
        # wissel naar rol HWL
        self.driver.get(self.url_wissel_van_rol)
        radio = bh.find_element_by_id(self.driver, 'id_eigen_%s' % self.functie_hwl.pk)    # radio button voor HWL
        bh.get_following_sibling(radio).click()
        bh.find_element_by_id(self.driver, 'activeer_eigen').click()        # activeer knop
        bh.wait_until_url_not(self.driver, self.url_wissel_van_rol)         # redirect naar /vereniging/

    def _check_ping(self):
        mh_session_id = self.driver.get_cookie('mh_session_id')['value']
        # print('mh_session_id cookie value: %s' % mh_session_id)
        session = SessionStore(session_key=mh_session_id)
        session[SESSIONVAR_VORIGE_POST] = 'forceer'
        session.save()

        self.driver.get(self.url_plein)

        has_ping = "simple_post" in self.driver.page_source
        # print('has_ping: %s' % has_ping)
        self.assertTrue(has_ping)
        # if not has_ping:
        #     print(self.driver.page_source[:500])
        #     print(self.driver.page_source[-500:])

        # wacht even en check daarna dat de post gedaan is door de js load event handler
        # time.sleep(1)

        session = SessionStore(session_key=mh_session_id)
        stamp = session.get(SESSIONVAR_VORIGE_POST, '')
        self.assertFalse(stamp == '')

    def setUp(self):
        self._database_vullen()
        self.driver = bh.get_driver(show_browser=False)

    def tearDown(self):
        self.driver.close()      # important, otherwise the server port keeps occupied
        self._database_opschonen()

    def test_sporter(self):
        # controleer dat we niet ingelogd zijn
        self.driver.get(self.url_plein)
        knop = bh.find_element_type_with_text(self.driver, 'a', 'Inloggen')
        self.assertIsNotNone(knop)
        bh.get_console_log(self.driver)

        # log in als sporter
        self._login()               # redirects naar Plein

        # pagina is gebaseerd op template plein-sporter.dtl

        # controleer dat we ingelogd zijn
        menu = bh.find_element_type_with_text(self.driver, 'a', 'Wissel van rol')
        self.assertIsNotNone(menu)
        menu = bh.find_element_type_with_text(self.driver, 'a', 'Mijn pagina')
        self.assertIsNotNone(menu)
        menu = bh.find_element_type_with_text(self.driver, 'a', 'Toon bondspas')
        self.assertIsNotNone(menu)
        menu = bh.find_element_type_with_text(self.driver, 'a', 'Uitloggen')
        self.assertIsNotNone(menu)

        self._check_ping()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = bh.get_console_log(self.driver)
        self.assertEqual(regels, [])

    def test_beheerder(self):
        # controleer dat we niet ingelogd zijn
        self.driver.get(self.url_plein)
        knop = bh.find_element_type_with_text(self.driver, 'a', 'Inloggen')
        self.assertIsNotNone(knop)
        bh.get_console_log(self.driver)

        # log in als sporter en wissel naar de HWL rol
        self._login()
        self._otp_controle()
        self._wissel_naar_hwl()     # redirect naar /vereniging/

        # controleer dat we beheerder zijn
        self.driver.get(self.url_plein)
        # pagina is plein-beheerder.dtl

        h3 = bh.find_element_type_with_text(self.driver, 'h3', 'Beheerders Plein')
        self.assertIsNotNone(h3)

        # check dat de ping gedaan is
        self._check_ping()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = bh.get_console_log(self.driver)
        self.assertEqual(regels, [])


# end of file
