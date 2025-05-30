# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.test import LiveServerTestCase, tag
from TestHelpers import browser_helper as bh
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import inspect
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

    show_browser = False            # set to True for visibility during debugging
    pause_after_each_test = False   # 2 seconden wachten aan het einde van de test

    url_login = '/account/login/'
    url_otp = '/account/otp-controle/'

    def setUp(self):
        self._test_count = 0
        self._driver = None
        self.account = None

        bh.database_vullen(self)

        self.assertIsNotNone(self.account)

    def tearDown(self):
        if self._driver:
            self._driver.close()      # important, otherwise the server port keeps occupied
            self._driver = None

        bh.database_opschonen(self)

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

    # browser interacties
    def _get_console_log(self) -> list[str]:
        logs = self._driver.get_log('browser')
        regels = list()
        for log in logs:
            msg = log['message']
            if msg not in regels:
                regels.append(msg)
        return regels

    def _login_and_otp(self):
        # inloggen
        self._driver.get(self.live_server_url + self.url_login)
        self.assertEqual(self._driver.title, 'Inloggen')

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = self._get_console_log()
        if len(regels):
            for regel in regels:
                print('regel: %s' % repr(regel))
        # for
        self.assertEqual(regels, [])

        self._driver.find_element(By.ID, 'id_login_naam').send_keys(self.account.username)
        self._driver.find_element(By.ID, 'id_wachtwoord').send_keys(TEST_WACHTWOORD)
        login_vink = self._driver.find_element(By.NAME, 'aangemeld_blijven')
        self.assertTrue(login_vink.is_selected())
        self._driver.find_element(By.ID, 'submit_knop').click()
        self._wait_until_url_not(self.url_login)        # gaat naar otp control (want: is_BB)

        # pass otp
        # self._driver.get(self.live_server_url + self.url_otp)
        self.assertEqual(self._driver.title, 'Controle tweede factor MijnHandboogsport')

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        regels = self._get_console_log()
        if len(regels):
            for regel in regels:
                print('regel: %s' % repr(regel))
        # for
        self.assertEqual(regels, [])

        otp_code = pyotp.TOTP(self.account.otp_code).now()
        self._driver.find_element(By.ID, 'id_otp_code').send_keys(otp_code)
        self._driver.find_element(By.ID, 'submit_knop').click()
        self._wait_until_url_not(self.url_otp)          # gaat naar wissel-van-rol

    def _run_module_tests(self, test_module):
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
                    # create an instance of the this BrowserTestCase
                    inst = obj()

                    # populate with promised members
                    bh.populate_inst(self, inst)

                    # find and invoke the test functions
                    for inst_name in dir(inst):
                        if inst_name.startswith('test_'):
                            test_func = getattr(inst, inst_name)
                            if callable(test_func):
                                self._test_count += 1
                                print('  %s.%s.%s ...' % (test_module, name, inst_name), end='')
                                test_func()
                                if self.pause_after_each_test:
                                    time.sleep(2)
                                print('ok')
                    # for
            # for

    def _run_tests(self, app_filter=None):
        test_modules = list()
        for app in apps.get_app_configs():
            if app_filter and app_filter not in app.name:
                continue
            js_tests_path = os.path.join(app.name, 'js_tests')
            if os.path.exists(js_tests_path):
                for d in os.listdir(js_tests_path):
                    if d.startswith('test_') and d.endswith('.py'):
                        test_modules.append(app.name + '.js_tests.' + d[:-3])
                # for
        # for

        test_modules.sort()     # consistent execution order
        if len(test_modules) == 0:
            self.fail('No tests found with focus %s' % repr(app_filter))

        do_fail = False
        try:
            self._driver = bh.get_driver(show_browser=self.show_browser)
            self._login_and_otp()
        except NoSuchElementException as exc:
            print('\n[ERROR] Selenium error: %s' % str(exc))
            do_fail = True

        # raise outside try-except to avoid repeat
        if do_fail:
            self.fail('Test aborted')

        print('js_tests modules found: %s' % len(test_modules))
        for test_module in test_modules:
            self._run_module_tests(test_module)
        # for

        print('ran %s js tests ...' % self._test_count, end='')

        bh.js_cov_save('/tmp/browser_js_cov.json')

    def test_all(self):
        self._run_tests()

    def _run_focussed_tests(self):
        # get the function name of the caller
        caller_func_name = inspect.currentframe().f_back.f_code.co_name
        self.show_browser = True
        self.pause_after_each_test = True
        self._run_tests(app_filter=caller_func_name[6:])

    def focus_Account(self):
        self._run_focussed_tests()

    def focus_CompScores(self):
        self._run_focussed_tests()

    def focus_Logboek(self):
        self._run_focussed_tests()

    def focus_Overig(self):
        self._run_focussed_tests()

    def focus_Plein(self):
        self._run_focussed_tests()

    def focus_Webwinkel(self):
        self._run_focussed_tests()


# end of file
