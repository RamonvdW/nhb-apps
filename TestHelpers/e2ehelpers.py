# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import auth
from django.test import TestCase, Client
from django.db import connection
from Account.operations.aanmaken import account_create
from Functie.view_vhpg import account_vhpg_is_geaccepteerd
from TestHelpers.test_asserts import MyTestAsserts
from TestHelpers.query_tracer import MyQueryTracer
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
from TestHelpers.app_hierarchy_testrunner import get_test_cases_count
from contextlib import contextmanager
import webbrowser
import tempfile
import pyotp


# debug optie: toon waar in de code de queries vandaan komen
FAIL_UNSAFE_DATABASE_MODIFICATION = False

# sterk genoeg default wachtwoord
TEST_WACHTWOORD = "qewretrytuyi"        # noqa


class E2EHelpers(MyTestAsserts, MyMgmtCommandHelper, TestCase):

    """ Helpers voor het End-to-End testen, dus zoals de gebruiker de website gebruikt vanuit de browser

        mixin class voor django.test.TestCase
    """

    WACHTWOORD = TEST_WACHTWOORD

    client: Client                  # for code completion / code inspection

    @staticmethod
    def is_small_test_run():
        app_count, fpath_count, testcase_count = get_test_cases_count()
        if app_count == 1 and fpath_count == 1:              # pragma: no cover
            print('[INFO] This is a small test run (1 app, 1 file, %s cases)' % testcase_count)
            return True
        return False

    def e2e_logout(self):
        # in case the test client behaves different from the real website, we can compensate here
        self.client.logout()

    @staticmethod
    def e2e_account_accepteert_vhpg(account):
        account_vhpg_is_geaccepteerd(account)

    def e2e_create_account(self, username, email, voornaam, accepteer_vhpg=False):
        """ Maak een Account aan in de database van de website """
        account = account_create(username, voornaam, '', TEST_WACHTWOORD, email, True)

        # zet OTP actief (een test kan deze altijd weer uit zetten)
        account.otp_code = "whatever"
        account.otp_is_actief = True
        account.save(update_fields=['otp_code', 'otp_is_actief'])

        if accepteer_vhpg:
            self.e2e_account_accepteert_vhpg(account)
        return account

    def e2e_create_account_admin(self, accepteer_vhpg=True):
        account = self.e2e_create_account('424242', 'admin@test.com', 'Admin', accepteer_vhpg)
        # zet de benodigde vlaggen om admin te worden
        account.is_staff = True         # toegang tot de admin site
        account.is_superuser = True     # alle rechten op alle database tabellen
        account.save()
        return account

    def e2e_login_no_check(self, account, wachtwoord=None, follow=False):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        if not wachtwoord:
            wachtwoord = TEST_WACHTWOORD
        resp = self.client.post('/account/login/', {'login_naam': account.username,
                                                    'wachtwoord': wachtwoord},
                                follow=follow)
        return resp

    def e2e_login(self, account, wachtwoord=None):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        resp = self.e2e_login_no_check(account, wachtwoord)
        if resp.status_code != 302:         # pragma: no cover
            self.e2e_dump_resp(resp)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def e2e_login_and_pass_otp(self, account, wachtwoord=None):
        self.e2e_login(account, wachtwoord)
        # door de login is een cookie opgeslagen met het csrf token
        resp = self.client.post('/account/otp-controle/', {'otp_code': pyotp.TOTP(account.otp_code).now()})
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def _wissel_naar_rol(self, rol, expected_redirect):
        resp = self.client.post('/functie/activeer-rol/%s/' % rol)
        self.assert_is_redirect(resp, expected_redirect)

    def e2e_wisselnaarrol_bb(self):
        self._wissel_naar_rol('BB', '/functie/wissel-van-rol/')

    def e2e_wisselnaarrol_sporter(self):
        self._wissel_naar_rol('sporter', '/plein/')

    def e2e_wisselnaarrol_gebruiker(self):
        self._wissel_naar_rol('geen', '/functie/wissel-van-rol/')

    WISSEL_VAN_ROL_EXPECTED_URL = {
        'SEC': '/vereniging/',
        'HWL': '/vereniging/',
        'WL':  '/vereniging/',
        'BKO': '/bondscompetities/##',          # startswith = ##
        'RKO': '/bondscompetities/##',
        'RCL': '/bondscompetities/##',
        'MO':  '/opleidingen/manager/',
        'SUP': '/feedback/inzicht/',
        'MWW': '/webwinkel/manager/',
        'MWZ': '/wedstrijden/manager/wacht/',
        'CS': '/scheidsrechter/'
    }

    def e2e_wissel_naar_functie(self, functie):
        resp = self.client.post('/functie/activeer-functie/%s/' % functie.pk)

        try:
            expected_url = self.WISSEL_VAN_ROL_EXPECTED_URL[functie.rol]
        except KeyError:        # pragma: no cover
            expected_url = 'functie ontbreekt (fout in test suite)'

        self.assert_is_redirect(resp, expected_url)

    def e2e_check_rol(self, rol_verwacht):
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)

        # <meta property="nhb-apps:rol" content="SEC">
        # <meta property="nhb-apps:functie" content="Secretaris vereniging 4444">
        page = str(resp.content)
        pos = page.find('<meta property="nhb-apps:rol" content="')
        if pos < 0:
            # informatie is niet aanwezig
            rol_nu = "geen meta"            # pragma: no cover
        else:
            spl = page[pos+39:pos+39+15].split('"')
            rol_nu = spl[0]
        if rol_nu != rol_verwacht:
            raise ValueError('Rol mismatch: rol_nu=%s, rol_verwacht=%s' % (rol_nu, rol_verwacht))

    # Not a true e2e function (no calls made)
    def e2e_dump_resp(self, resp):                        # pragma: no cover
        self.dump_resp(resp)

    # safe links zijn altijd bereikbaar en hoeven niet bij elke test gecontroleerd te worden
    SAFE_LINKS = ('/plein/', '/bondscompetities/', '/records/', '/account/login/', '/account/logout/')

    def e2e_test_link(self, link, template_name):
        """ make sure the link works """
        if link in self.SAFE_LINKS or link.startswith('/feedback/') or link.startswith('#'):
            return

        resp = self.client.head(link)

        if resp.status_code == 302:                                                 # pragma: no cover
            self.fail(msg='Found NOK href %s that gives code 302 (redirect to %s) on page %s' % (
                        repr(link), resp.url, template_name))

        if resp.status_code != 200:                                                 # pragma: no cover
            self.e2e_dump_resp(resp)
            self.fail(msg='Found NOK href %s that gives code %s on page %s' % (
                        repr(link), resp.status_code, template_name))

        # 403 and 404 also have status_code 200 but use a special template
        for templ in resp.templates:
            if templ.name == 'plein/fout_403.dtl':                                  # pragma: no cover
                # haal de hele pagina op, inclusief de foutmelding
                resp = self.client.get(link)
                error_msg = self.get_error_msg_from_403_page(resp)
                self.fail(msg='Found NOK href %s that gives code 403 with message "%s" on page %s' % (
                            repr(link), error_msg, template_name))

            if templ.name == 'plein/fout_404.dtl':                                  # pragma: no cover
                self.fail(msg='Found NOK href %s that gives code 404 on page %s' % (
                            repr(link), template_name))
        # for

    def e2e_test_broodkruimels(self, content, template_name):
        # find the start
        pos = content.find('class="broodkruimels-link" href="')
        while pos > 0:
            content = content[pos+33:]
            link = content[:content.find('"')]
            self.e2e_test_link(link, template_name)
            pos = content.find('class="broodkruimels-link" href="')
        # while

    def assert_link_quality(self, content, template_name, is_email=False):
        """ uitbreiding op assert_html_ok met e2e_test_broodkruimels """
        super().assert_link_quality(content, template_name, is_email)
        self.e2e_test_broodkruimels(content, template_name)

    def e2e_assert_logged_in(self):
        resp = self.client.get('/account/logout/', follow=False)
        # indien ingelogd krijgen we een pagina terug met status_code == 200
        # indien niet ingelogd krijgen we een redirect met status_code == 302
        if resp.status_code == 302:                     # pragma: no branch
            self.fail(msg='Onverwacht NIET ingelogd')   # pragma: no cover

    def e2e_assert_not_logged_in(self):
        resp = self.client.get('/account/logout/', follow=False)
        # indien ingelogd krijgen we een pagina terug met status_code == 200
        # indien niet ingelogd krijgen we een redirect met status_code == 302
        if resp.status_code == 200:                     # pragma: no branch
            self.fail(msg='Onverwacht ingelogd')        # pragma: no cover

    def e2e_assert_other_http_commands_not_supported(self, url,
                                                     get=False, post=True, delete=True, put=True, patch=True):
        """ Test een aantal 'common' http methoden
            en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
            POST, DELETE, PATCH
        """
        # toegestane status_codes:
        #   302 (redirect)
        #   403 (not allowed)
        #   404 (not found)
        #   405 (not allowed)
        accepted_status_codes = (405,)  # (302, 403, 404, 405)

        if get:
            resp = self.client.get(url)
            if resp.status_code not in accepted_status_codes and not self.is_fout_pagina(resp):    # pragma: no cover
                self.fail(msg='Onverwachte status code %s bij GET command' % resp.status_code)

        if post:
            resp = self.client.post(url)
            if resp.status_code not in accepted_status_codes and not self.is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij POST command' % resp.status_code)     # pragma: no cover

        if delete:                            # pragma: no cover
            resp = self.client.delete(url)
            if resp.status_code not in accepted_status_codes and not self.is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij DELETE command' % resp.status_code)

        if put:                               # pragma: no cover
            resp = self.client.put(url)
            if resp.status_code not in accepted_status_codes and not self.is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij PUT command' % resp.status_code)

        if patch:                             # pragma: no cover
            resp = self.client.patch(url)
            if resp.status_code not in accepted_status_codes and not self.is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij PATCH command' % resp.status_code)

    @contextmanager
    def assert_max_queries(self, num, check_duration=True, modify_acceptable=False):
        tracer = MyQueryTracer(modify_acceptable)
        try:
            with connection.execute_wrapper(tracer):
                yield
        finally:
            if not tracer.found_500:
                if check_duration:
                    duration_seconds = tracer.get_elapsed_seconds()
                else:
                    duration_seconds = 0.0

                count = len(tracer.trace)

                if num == -1:                         # pragma: no cover
                    print('[INFO] Operation resulted in %s queries' % count)

                elif count > num:                     # pragma: no cover
                    msg = "Too many queries: %s; maximum %d. %s" % (count, num, tracer)
                    self.fail(msg)

                if count <= num:
                    # kijk of het wat minder kan
                    if num > 20:
                        ongebruikt = num - count
                        if ongebruikt / num > 0.25:                                     # pragma: no cover
                            self.fail(msg="Maximum (%s) has a lot of margin. Can be set as low as %s" % (num, count))

                if duration_seconds > 1.5:                                              # pragma: no cover
                    print("[WARNING] Operation took suspiciously long: %.2f seconds (%s queries took %.2f ms)" % (
                                        duration_seconds, len(tracer.trace), tracer.total_duration_us / 1000.0))

                if len(tracer.trace) > 500:                                             # pragma: no cover
                    print("[WARNING] Operation required a lot of database interactions: %s queries" % len(tracer.trace))

                if tracer.found_modify:
                    # more than just SELECT
                    self.check_concurrency_risks(tracer)

        if not tracer.found_500:
            report = tracer.report()
            if report:                      # pragma: no cover
                print(report)

    @staticmethod
    def e2e_open_in_browser(resp, show=True):
        if show and resp.status_code == 200:            # pragma: no cover
            msg = resp.content.decode('utf-8')

            msg = msg.replace('/static/', '/tmp/tmp_html/static/')

            f = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.html', dir='/tmp/tmp_html/')
            f.write(msg.encode('utf-8'))
            f.close()
            fname = f.name

            try:
                # will hang here for a few seconds, unless browser already open
                webbrowser.open_new_tab(fname)
            except KeyboardInterrupt:
                # capture user interrupt due to long wait
                pass

# end of file
