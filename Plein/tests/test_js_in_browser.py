# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.test import LiveServerTestCase, tag
from django.utils import timezone
from Account.models import Account
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Regio, Rayon
from Sporter.models import Sporter
from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Vereniging.models import Vereniging
import datetime
import pyotp
import time
import os


@tag("browser")
class TestBrowser(LiveServerTestCase):

    """ entrypoint voor alle in-browser tests van Javascript
        alle applicaties kunnen testen aanleveren in app/js_tests/

        Na het aanmaken van de standaard inhoud van de database en het openen van de browser,
        worden alle tests in 1x gedraaid. Dit scheelt een hoop tijd.
    """

    show_browser = True         # set to True for visibility during debugging

    url_login = '/account/login/'
    url_otp = '/account/otp-controle/'

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

    def setUp(self):
        self._database_vullen()
        self._driver = bh.get_driver(show_browser=self.show_browser)

    def tearDown(self):
        self._driver.close()      # important, otherwise the server port keeps occupied
        self._database_opschonen()

    def _wait_until_url_not(self, url: str, timeout: float = 2.0):
        duration = 0.5
        check_url = self.live_server_url + url
        curr_url = self._driver.current_url
        while curr_url == check_url and timeout > 0:
            time.sleep(duration)
            timeout -= duration
            duration *= 2
            curr_url = self._driver.current_url
        # while

    def test_all(self):
        # fail early: haal een eerste pagina op
        self._driver.get(self.live_server_url + bh.BrowserTestCase.url_plein)

        # inloggen
        self._driver.get(self.live_server_url + self.url_login)
        self._driver.find_element(bh.By.ID, 'id_login_naam').send_keys(self.account.username)
        self._driver.find_element(bh.By.ID, 'id_wachtwoord').send_keys(TEST_WACHTWOORD)
        login_vink = self._driver.find_element(bh.By.NAME, 'aangemeld_blijven')
        self.assertTrue(login_vink.is_selected())
        self._driver.find_element(bh.By.ID, 'submit_knop').click()
        self._wait_until_url_not(self.url_login)

        # pass otp
        self._driver.get(self.live_server_url + self.url_otp)
        otp_code = pyotp.TOTP(self.account.otp_code).now()
        self._driver.find_element(bh.By.ID, 'id_otp_code').send_keys(otp_code)
        self._driver.find_element(bh.By.ID, 'submit_knop').click()
        self._wait_until_url_not(self.url_otp)

        print('searching...')
        test_modules = list()
        for app in apps.get_app_configs():
            js_tests_path = os.path.join(app.name, 'js_tests')
            if os.path.exists(js_tests_path):
                for d in os.listdir(js_tests_path):
                    if d.startswith('test_') and d.endswith('.py'):
                        test_modules.append(app.name + '.js_tests.' + d[:-3])
                # for
        # for

        test_modules.sort()     # consistent execution order
        # print('Found: %s' % test_modules)

        for test_module in test_modules:
            try:
                mod = __import__(test_module)
            except ImportError:
                pass
            else:
                parts = test_module.split('.')
                for part in parts[1:]:
                    mod = getattr(mod, part)
                # print('%s is %s' % (test_module, mod))
                for name in dir(mod):
                    obj = getattr(mod, name)
                    if isinstance(obj, type) and issubclass(obj, bh.BrowserTestCase):
                        inst = obj()

                        # dirty part: take over all members into the other instance
                        inst._driver = self._driver
                        inst.account = self.account
                        inst.sporter = self.sporter
                        inst.regio = self.regio
                        inst.rayon = self.rayon
                        inst.ver = self.ver
                        inst.functie_hwl = self.functie_hwl
                        inst.vhpg = self.vhpg
                        inst.live_server_url = self.live_server_url

                        for inst_name in dir(inst):
                            if inst_name.startswith('test_'):
                                test_func = getattr(inst, inst_name)
                                if callable(test_func):
                                    print('%s.%s.%s ...' % (test_module, name, inst_name ), end='')
                                    test_func()
                                    # time.sleep(2)
                                    print('ok')
                        # for

# end of file
