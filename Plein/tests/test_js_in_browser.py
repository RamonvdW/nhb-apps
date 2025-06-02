# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.test import LiveServerTestCase, tag
from TestHelpers import browser_helper as bh
from selenium.common.exceptions import NoSuchElementException
import inspect
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
    pause_after_each_test = 2       # seconden wachten na elke test
    pause_after_console_log = 180   # seconden wachten als we een console error zien
    pause_after_all_tests = 0       # seconden wachten aan het einde van alle tests

    def setUp(self):
        self._test_count = 0
        self._driver = None
        self.account = None
        self.session_state = "?"

        bh.database_vullen(self)

        self.assertIsNotNone(self.account)

    def tearDown(self):
        if self._driver:                # pragma: no branch
            self._driver.close()        # important, otherwise the server port remains occupied
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
        logs = self._driver.get_log('browser')      # gets the log + clears it!
        regels = list()
        for log in logs:
            msg = log['message']
            if msg not in regels:
                regels.append(msg)
        return regels

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
                                inst.fetch_js_cov()
                                if self.show_browser and self.pause_after_each_test:
                                    time.sleep(self.pause_after_each_test)
                                print('ok')
                    # for

                    # take over the session state so we can pass it to the next test case
                    self.session_state = inst.session_state
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
        except NoSuchElementException as exc:
            print('\n[ERROR] Selenium error: %s' % str(exc))
            do_fail = True

        # raise outside try-except to avoid raising exception from inside exception handler
        if do_fail:
            self.fail('Test aborted')

        print('js_tests modules found: %s' % len(test_modules))
        for test_module in test_modules:
            self._run_module_tests(test_module)
        # for

        print('ran %s js tests ...' % self._test_count, end='')

        # give the developer some time to play with the browser instance
        if self.show_browser and self.pause_after_all_tests:
            print('[INFO] Sleeping for %s seconds' % self.pause_after_all_tests)
            time.sleep(self.pause_after_all_tests)

        bh.js_cov_save()

    def import_js_cov(self):
        res = bh.js_cov_import()
        self.assertEqual(res, 1)

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
