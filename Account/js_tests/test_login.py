# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Account.models import Account
from Geo.models import Regio, Rayon
from Sporter.models import Sporter
from Vereniging.models import Vereniging
import datetime


class TestAccountLogin(bh.BrowserTestCase):

    port = bh.port

    url_root = bh.url_root
    url_plein = url_root + '/plein/'
    url_login = url_root + '/account/login/'

    def _database_vullen(self):
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

        self.rayon = Rayon.objects.create(rayon_nr=5, naam="Rayon 5")
        self.regio = Regio.objects.create(regio_nr=117, rayon_nr=self.rayon.rayon_nr, rayon=self.rayon)

        self.ver = Vereniging.objects.create(
                                    naam="Browser Club",
                                    ver_nr=4200,
                                    regio=self.regio)

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

    def _database_opschonen(self):
        self.sporter.delete()
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
        # clickable = bh.get_following_sibling(login_vink)
        # login_vink.click()
        # self.assertFalse(login_vink.is_selected())
        bh.find_element_by_id(self.driver, 'submit_knop').click()
        # TODO: nodig?? bh.wait_until_url_not(self.driver, self.url_login)

    def setUp(self):
        self._database_vullen()
        self.driver = bh.get_driver()    # show_browser=True

    def tearDown(self):
        self.driver.close()      # important, otherwise server port remains occupied
        self._database_opschonen()

    def test_login(self):
        self._login()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = bh.get_console_log(self.driver)
        if len(regels):
            for regel in regels:
                print('regel: %s' % repr(regel))
        # for
        self.assertEqual(regels, [])

        bh.wait_until_url_not(self.driver, self.url_login)

        # controleer dat we ingelogd zijn
        self.driver.get(self.url_plein)
        menu = bh.find_element_type_with_text(self.driver, 'a', 'Uitloggen')
        self.assertIsNotNone(menu)


# end of file
