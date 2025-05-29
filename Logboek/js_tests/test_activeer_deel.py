# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Account.models import Account
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Regio, Rayon
from Sporter.models import Sporter
from Vereniging.models import Vereniging
import datetime
import pyotp


class TestLogboekActiveerDeel(bh.BrowserTestCase):

    """ Test de Logboek applicatie, gebruik van activeer_deel.js vanuit de browser """

    port = bh.port

    url_root = bh.url_root
    url_plein = url_root + '/plein/'
    url_login = url_root + '/account/login/'
    url_otp = url_root + '/account/otp-controle/'
    url_wissel_van_rol = url_root + '/functie/wissel-van-rol/'
    url_logboek = url_root + '/logboek/'

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
                                    otp_is_actief=True,
                                    is_BB=True)
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

    def _database_opschonen(self):
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

    def _wissel_naar_bb(self):
        # wissel naar rol Manager MH
        self.driver.get(self.url_wissel_van_rol)
        radio = bh.find_element_by_id(self.driver, 'id_eigen_90002')        # radio button voor Manager MH
        bh.get_following_sibling(radio).click()
        bh.find_element_by_id(self.driver, 'activeer_eigen').click()         # activeer knop
        bh.wait_until_url_not(self.driver, self.url_wissel_van_rol)

    def setUp(self):
        self._database_vullen()
        self.driver = bh.get_driver(show_browser=True)

    def tearDown(self):
        self.driver.close()      # important, otherwise the server port keeps occupied
        self._database_opschonen()

    def test_logboek(self):
        # controleer dat we niet ingelogd zijn
        self.driver.get(self.url_plein)
        knop = bh.find_element_type_with_text(self.driver, 'a', 'Inloggen')
        self.assertIsNotNone(knop)
        bh.get_console_log(self.driver)

        # log in als sporter en wissel naar de rol Manager MH
        self._login()
        self._otp_controle()
        self._wissel_naar_bb()

        # ga naar het logboek (dit controleert ook dat we beheerder zijn)
        self.driver.get(self.url_logboek)
        h3 = bh.find_element_type_with_text(self.driver, 'h3', 'Logboek')
        self.assertIsNotNone(h3)

        # kies een het deel Records en klik op de activeer knop
        radio = bh.find_element_by_id(self.driver, 'id_records')        # radio button voor deel 'Records'
        bh.get_following_sibling(radio).click()
        bh.find_element_by_id(self.driver, 'id_activeer_knop').click()
        bh.wait_until_url_not(self.driver, self.url_logboek)

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = bh.get_console_log(self.driver)
        self.assertEqual(regels, [])


# end of file
