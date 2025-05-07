# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import LiveServerTestCase, tag
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Account.models import Account
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Regio, Rayon
from Sporter.models import Sporter
from Vereniging.models import Vereniging
import datetime


@tag("browser")
class TestBrowserPlein(LiveServerTestCase):

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

        self.vhpg = VerklaringHanterenPersoonsgegevens.objects.create(
                                                    account=self.account,
                                                    acceptatie_datum=timezone.now())

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

        self.functie_hwl = Functie.objects.create(
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

    def setUp(self):
        self._database_vullen()

    def tearDown(self):
        self._database_opschonen()

    def test_plein(self):
        driver = bh.get_driver()    # show_browser=True

        driver.get(self.url_plein)
        knop = bh.find_element_type_with_text(driver, 'a', 'Inloggen')
        self.assertIsNotNone(knop)
        bh.get_console_log(driver)

        # log in
        driver.get(self.url_login)
        bh.find_element_by_id(driver, 'id_login_naam').send_keys(self.account.username)
        bh.find_element_by_id(driver, 'id_wachtwoord').send_keys(TEST_WACHTWOORD)
        login_vink = bh.find_element_by_name(driver, 'aangemeld_blijven')
        self.assertTrue(login_vink.is_selected())
        bh.find_element_by_id(driver, 'submit_knop').click()
        bh.wait_until_url_not(driver, self.url_login)

        # controleer dat we ingelogd zijn
        driver.get(self.url_plein)
        menu = bh.find_element_type_with_text(driver, 'a', 'Wissel van rol')
        self.assertIsNotNone(menu)
        menu = bh.find_element_type_with_text(driver, 'a', 'Mijn pagina')
        self.assertIsNotNone(menu)
        menu = bh.find_element_type_with_text(driver, 'a', 'Toon bondspas')
        self.assertIsNotNone(menu)
        menu = bh.find_element_type_with_text(driver, 'a', 'Uitloggen')
        self.assertIsNotNone(menu)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = bh.get_console_log(driver)
        self.assertEqual(regels, [])

        driver.close()      # important, otherwise the server port keeps occupied


# end of file
