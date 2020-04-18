# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import auth
from Account.models import Account, account_create
from Functie.views import account_vhpg_is_geaccepteerd
from bs4 import BeautifulSoup
from django.test import TestCase
import pyotp


class E2EHelpers(object):

    """ Helpers voor het End-to-End testen, dus zoals de gebruiker de website gebruikt vanuit de browser

        mixin class voor django.test.TestCase
    """

    WACHTWOORD = "qewretrytuyi"     # sterk genoeg default wachtwoord

    def e2e_logout(self):
        # in case the test client behaves different from the real website, we can compensate here
        assert isinstance(self, TestCase)
        self.client.logout()

    @staticmethod
    def e2e_account_accepteert_vhpg(account):
        account_vhpg_is_geaccepteerd(account)

    def e2e_create_account(self, username, email, voornaam, accepteer_vhpg=False):
        """ Maak een Account met AccountEmail aan in de database van de website """
        account_create(username, self.WACHTWOORD, email, voornaam)
        account = Account.objects.get(username=username)

        # zet OTP actief (een test kan deze altijd weer uit zetten)
        account.otp_code = "whatever"
        account.otp_is_actief = True
        account.save()

        if accepteer_vhpg:
            self.e2e_account_accepteert_vhpg(account)
        return account

    def e2e_create_account_admin(self, accepteer_vhpg=True):
        account = self.e2e_create_account('admin', 'admin@test.com', 'Admin', accepteer_vhpg)
        # zet de benodigde vlaggen om admin te worden
        account.is_staff = True
        account.is_superuser = True
        account.save()
        return account

    def e2e_login_no_check(self, account):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        ww = self.WACHTWOORD
        assert isinstance(self, TestCase)
        resp = self.client.post('/account/login/', {'login_naam': account.username, 'wachtwoord': ww})
        return resp

    def e2e_login(self, account):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        resp = self.e2e_login_no_check(account)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def e2e_login_and_pass_otp(self, account):
        self.e2e_login(account)
        # door de login is een cookie opgeslagen met het csrf token
        assert isinstance(self, TestCase)
        resp = self.client.post('/functie/otp-controle/', {'otp_code': pyotp.TOTP(account.otp_code).now()})
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def _wissel_naar_rol(self, rol):
        assert isinstance(self, TestCase)
        resp = self.client.get('/functie/wissel-van-rol/%s/' % rol)
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def e2e_wisselnaarrol_beheerder(self):
        self._wissel_naar_rol('beheerder')

    def e2e_wisselnaarrol_bb(self):
        self._wissel_naar_rol('BB')

    def e2e_wisselnaarrol_schutter(self):
        self._wissel_naar_rol('schutter')

    def e2e_wisselnaarrol_gebruiker(self):
        self._wissel_naar_rol('geen')

    def e2e_wissel_naar_functie(self, functie):
        assert isinstance(self, TestCase)
        resp = self.client.get('/functie/wissel-van-rol/functie/%s/' % functie.pk)
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def e2e_check_rol(self, rol_verwacht):
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)

        # <meta rol_nu="CWZ" functie_nu="CWZ vereniging 4444">
        page = str(resp.content)
        pos = page.find('<meta rol_nu=')
        if pos < 0:
            raise ValueError('Could not locate <meta rol_nu=')
        spl = page[pos+14:pos+100].split('"')
        rol_nu = spl[0]
        functie_nu = spl[2]
        if rol_nu != rol_verwacht:
            print("e2e_check_rol: rol_nu=%s, functie_nu=%s" % (rol_nu, functie_nu))
            raise ValueError('Rol mismatch: rol_nu=%s, rol_verwacht=%s' % (rol_nu, rol_verwacht))

    @staticmethod
    def e2e_dump_resp(resp):                        # pragma: no cover
        print("status code:", resp.status_code)
        print(repr(resp))
        if resp.status_code == 302:
            print("redirect to url:", resp.url)
        content = str(resp.content)
        if len(content) < 50:
            print("very short content:", content)
        else:
            soup = BeautifulSoup(content, features="html.parser")
            print(soup.prettify())

    @staticmethod
    def extract_all_href_urls(resp):
        # TODO: consider using Beautifulsoup to extract all href urls
        #   for link in soup.find_all('a'):
        #       print(link.get('href'))
        content = str(resp.content)
        pos = content.find('<body')
        if pos > 0:                             # pragma: no branch
            content = content[pos:]             # strip head
        urls = list()
        while len(content):
            pos = content.find('href="')
            if pos > 0:
                content = content[pos+6:]       # strip all before href
                pos = content.find('"')
                urls.append(content[:pos])
                content = content[pos:]
            else:
                content = ""
        # while
        return urls

    def assert_html_ok(self, response):
        """ Doe een aantal basic checks op een html response """
        assert isinstance(self, TestCase)
        html = str(response.content)
        self.assertContains(response, "<html")
        self.assertIn("lang=", html)
        self.assertIn("</html>", html)
        self.assertIn("<head>", html)
        self.assertIn("</head>", html)
        self.assertIn("<body ", html)
        self.assertIn("</body>", html)
        self.assertIn("<!DOCTYPE html>", html)

    def assert_template_used(self, response, template_names):
        """ Controleer dat de gevraagde templates gebruikt zijn """
        assert isinstance(self, TestCase)
        lst = list(template_names)
        for templ in response.templates:
            if templ.name in lst:
                lst.remove(templ.name)
        # for
        if len(lst):    # pragma: no cover
            msg = "Following templates should have been used: %s\n(actually used: %s)" % (repr(lst), repr([t.name for t in response.templates]))
            self.assertTrue(False, msg=msg)

    def e2e_assert_other_http_commands_not_supported(self, url, post=True, delete=True, put=True, patch=True):
        """ Test een aantal 'common' http methoden
            en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
            POST, DELETE, PATCH
        """
        assert isinstance(self, TestCase)

        # toegestane status_codes:
        #   302 (redirect)
        #   404 (not found)
        #   405 (not allowed)
        accepted_status_codes = (302, 404, 405)

        if post:
            resp = self.client.post(url)
            self.assertTrue(resp.status_code in accepted_status_codes)

        if delete:                            # pragma: no cover
            resp = self.client.delete(url)
            self.assertTrue(resp.status_code in accepted_status_codes)

        if put:                               # pragma: no cover
            resp = self.client.put(url)
            self.assertTrue(resp.status_code in accepted_status_codes)

        if patch:                             # pragma: no cover
            resp = self.client.patch(url)
            self.assertTrue(resp.status_code in accepted_status_codes)

    def assert_is_redirect(self, resp, expected_url):
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, expected_url)


# end of file
