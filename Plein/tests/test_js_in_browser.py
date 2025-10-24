# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.test import LiveServerTestCase, tag
from TestHelpers import browser_helper as bh
from selenium.common.exceptions import NoSuchElementException
import time
import os


def outer(app_filter):
    def inner(inst):
        # wordt alleen gebruikt bij testen van subset
        inst.run_focussed_tests(app_filter)     # pragma: no cover
    return inner


class AddFocus(type):
    # create focus_Appname methods before unittest does discovery
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)

        added = list()

        # find the apps with JS tests and add a method focus_AppName for use from browser_test.sh
        for app in apps.get_app_configs():
            add = False
            js_tests_path = os.path.join(app.name, 'js_tests')
            if os.path.exists(js_tests_path):
                for d in os.listdir(js_tests_path):                     # pragma: no branch
                    if d.startswith('test_') and d.endswith('.py'):
                        add = True
                        break
                # for
            if add:
                setattr(cls, 'focus_%s' % app.name, outer(app.name))
                added.append(app.name)
        # for

        print('[INFO] added focus methods for apps with JS tests: ' + ", ".join(added))


@tag("browser")         # deze tag voorkomt het uitvoeren van deze test tijden de main test run
class TestBrowser(LiveServerTestCase, metaclass=AddFocus):

    """ entrypoint voor alle in-browser tests van Javascript
        alle applicaties kunnen testen aanleveren in app/js_tests/

        Na het aanmaken van de standaard inhoud van de database en het openen van de browser,
        worden alle tests in 1x gedraaid. Dit scheelt een hoop tijd.
    """

    show_browser = False                # set to True for visibility during debugging
    pause_after_each_test = False       # is automatically set to True for focussed tests

    pause_after_test_seconds = 2        # seconden wachten na elke test
    pause_after_console_log = 30        # seconden wachten als we een console error zien
    pause_after_all_tests_seconds = 0   # seconden wachten aan het einde van alle tests

    def setUp(self):
        self._test_count = 0
        self._driver = None
        self._nav_hist = list()
        self.account = None
        self.session_state = "?"

        bh.database_vullen(self)

        self.assertIsNotNone(self.account)

    def tearDown(self):
        if self._driver:                # pragma: no branch
            self._driver.close()        # important, otherwise the server port remains occupied
            self._driver = None

        bh.database_opschonen(self)     # TODO: niet nodig: alle tabellen worden leeg gegooid door LiveServerTestCase :(

    def _run_module_tests(self, test_module):
        try:
            mod = __import__(test_module)
        except ImportError:     # pragma: no cover
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

                    if self.init_before_first_test:
                        self.init_before_first_test = False
                        inst.do_navigate_to('/plein/')
                        script = 'localStorage.removeItem("js_cov");\n'
                        script += 'localStorage.removeItem("js_cov_short_timeout");\n'
                        self._driver.execute_script(script)

                    # find and invoke the test functions
                    for inst_name in dir(inst):
                        if inst_name.startswith('test_'):
                            test_func = getattr(inst, inst_name)
                            if callable(test_func):                 # pragma: no branch
                                self._test_count += 1
                                print('  %s.%s.%s ... ' % (test_module, name, inst_name), end='')
                                test_func()
                                inst.fetch_js_cov()                 # collect captured coverage
                                inst.set_normal_xhr_timeouts()      # for the next test
                                if self.show_browser and self.pause_after_each_test:        # pragma: no cover
                                    print('sleeping %s ... ' % self.pause_after_test_seconds, end='')
                                    time.sleep(self.pause_after_test_seconds)
                                print('ok')
                    # for

                    # take over the session state so we can pass it to the next test case
                    self.session_state = inst.session_state
            # for

    def _run_tests(self, app_filter=None):
        test_modules = list()
        for app in apps.get_app_configs():
            if app_filter and app_filter not in app.name:       # pragma: no branch
                continue                                        # pragma: no cover
            js_tests_path = os.path.join(app.name, 'js_tests')
            if os.path.exists(js_tests_path):
                for d in os.listdir(js_tests_path):
                    if d.startswith('test_') and d.endswith('.py'):
                        test_modules.append(app.name + '.js_tests.' + d[:-3])
                # for
        # for
        test_modules.sort()     # consistent execution order
        if len(test_modules) == 0:                              # pragma: no cover
            self.fail('No tests found with focus %s' % repr(app_filter))

        do_fail = False
        try:
            self._driver = bh.get_driver(show_browser=self.show_browser)
        except NoSuchElementException as exc:       # pragma: no cover
            print('\n[ERROR] Selenium error: %s' % str(exc))
            do_fail = True

        # raise outside try-except to avoid raising exception from inside exception handler
        if do_fail:     # pragma: no cover
            self.fail('Test aborted')

        # navigate to "plein" and reset the localStorage
        self.init_before_first_test = True

        print('js_tests modules found: %s' % len(test_modules))
        for test_module in test_modules:
            self._run_module_tests(test_module)
        # for

        print('ran %s js tests ...' % self._test_count, end='')

        # give the developer some time to play with the browser instance
        if self.show_browser and self.pause_after_all_tests_seconds:        # pragma: no cover
            print('[INFO] Sleeping for %s seconds' % self.pause_after_all_tests_seconds)
            time.sleep(self.pause_after_all_tests_seconds)

        bh.js_cov_save()

    def test_all(self):
        self._run_tests()

    def run_focussed_tests(self, app_filter):              # pragma: no cover
        # this method is invoked from outer(), see top of this file
        # for each app with a js_tests directory, a function named focus_AppName is added that calls outer
        self.show_browser = True
        self.pause_after_each_test = True
        self._run_tests(app_filter)


# end of file
