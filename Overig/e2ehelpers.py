# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import auth
from Account.models import Account, account_create
from Functie.view_vhpg import account_vhpg_is_geaccepteerd
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

    @staticmethod
    def _remove_debugtoolbar(html):
        """ removes the debug toolbar code """
        pos = html.find('<link rel="stylesheet" href="/static/debug_toolbar/css/print.css"')
        if pos > 0:     # pragma: no cover
            html = html[:pos] + '<!-- removed debug toolbar --></body></html>'
        return html

    def e2e_create_account(self, username, email, voornaam, accepteer_vhpg=False):
        """ Maak een Account met AccountEmail aan in de database van de website """
        account_create(username, voornaam, '', self.WACHTWOORD, email, True)
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

    def e2e_login_no_check(self, account, wachtwoord=None):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        if not wachtwoord:
            wachtwoord = self.WACHTWOORD
        assert isinstance(self, TestCase)
        resp = self.client.post('/account/login/', {'login_naam': account.username,
                                                    'wachtwoord': wachtwoord})
        return resp

    def e2e_login(self, account, wachtwoord=None):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        resp = self.e2e_login_no_check(account, wachtwoord)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def e2e_login_and_pass_otp(self, account, wachtwoord=None):
        self.e2e_login(account, wachtwoord)
        # door de login is een cookie opgeslagen met het csrf token
        assert isinstance(self, TestCase)
        resp = self.client.post('/functie/otp-controle/', {'otp_code': pyotp.TOTP(account.otp_code).now()})
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def _wissel_naar_rol(self, rol, expected_redirect):
        assert isinstance(self, TestCase)
        resp = self.client.post('/functie/activeer-rol/%s/' % rol)
        self.assert_is_redirect(resp, expected_redirect)

    def e2e_wisselnaarrol_it(self):
        self._wissel_naar_rol('IT', '/functie/wissel-van-rol/')

    def e2e_wisselnaarrol_bb(self):
        self._wissel_naar_rol('BB', '/competitie/')

    def e2e_wisselnaarrol_schutter(self):
        self._wissel_naar_rol('schutter', '/functie/wissel-van-rol/')

    def e2e_wisselnaarrol_gebruiker(self):
        self._wissel_naar_rol('geen', '/functie/wissel-van-rol/')

    def e2e_wissel_naar_functie(self, functie):
        assert isinstance(self, TestCase)
        resp = self.client.post('/functie/activeer-functie/%s/' % functie.pk)
        if functie.rol in ('SEC', 'HWL', 'WL'):
            expected_redirect = '/vereniging/'
        else:
            expected_redirect = '/functie/wissel-van-rol/'
        self.assert_is_redirect(resp, expected_redirect)

    def e2e_check_rol(self, rol_verwacht):
        resp = self.client.get('/functie/wissel-van-rol/')
        self.assertEqual(resp.status_code, 200)

        # <meta rol_nu="SEC" functie_nu="Secretaris vereniging 4444">
        page = str(resp.content)
        pos = page.find('<meta rol_nu=')
        if pos < 0:
            # informatie is niet aanwezig
            rol_nu = "geen meta"            # pragma: no cover
        else:
            spl = page[pos+14:pos+100].split('"')
            rol_nu = spl[0]
            # functie_nu = spl[2]
        if rol_nu != rol_verwacht:
            # print("e2e_check_rol: rol_nu=%s, functie_nu=%s" % (rol_nu, functie_nu))
            raise ValueError('Rol mismatch: rol_nu=%s, rol_verwacht=%s' % (rol_nu, rol_verwacht))

    def e2e_dump_resp(self, resp):                        # pragma: no cover
        print("status code:", resp.status_code)
        print(repr(resp))
        if resp.status_code == 302:
            print("redirect to url:", resp.url)
        content = str(resp.content)
        content = self._remove_debugtoolbar(content)
        if len(content) < 50:
            print("very short content:", content)
        else:
            soup = BeautifulSoup(content, features="html.parser")
            print(soup.prettify())

    def extract_all_urls(self, resp, skip_menu=False, skip_smileys=True):
        content = str(resp.content)
        content = self._remove_debugtoolbar(content)
        if skip_menu:
            # menu is the last part of the body
            pos = content.find('<div id="menu">')
            content = content[:pos]     # if not found, takes [:-1], which is OK

        # skip the headers
        pos = content.find('<body')
        if pos > 0:                             # pragma: no branch
            content = content[pos:]             # strip header

        urls = list()
        while len(content):
            # find the start of a new url
            pos1 = content.find('href="')
            pos2 = content.find('action="')
            if pos1 >= 0 and (pos2 == -1 or pos2 > pos1):
                content = content[pos1+6:]       # strip all before href
            elif pos2 >= 0 and (pos1 == -1 or pos1 > pos2):
                content = content[pos2+8:]       # strip all before action
            else:
                content = ""

            # find the end of the new url
            pos = content.find('"')
            if pos > 0:
                url = content[:pos]
                content = content[pos:]
                if url != "#":
                    if not (skip_smileys and url.startswith('/overig/feedback/')):
                        urls.append(url)
        # while
        return urls

    def extract_checkboxes(self, resp):
        content = str(resp.content)
        content = self._remove_debugtoolbar(content)
        checked = list()
        unchecked = list()
        pos = content.find('<input ')
        while pos >= 0:
            content = content[pos+7:]       # strip before and <input
            pos = content.find('>')

            is_checkbox = False
            is_checked = False
            name = ""
            for part in content[:pos].split(' '):
                spl = part.split('=')       # geeft altijd lijst, minimaal 1 entry
                if len(spl) == 2:
                    if spl[0] == "type" and "checkbox" in spl[1]:
                        is_checkbox = True
                    elif spl[0] == "name":
                        name = spl[1].replace('"', '')  # strip doublequotes
                elif spl[0] == "checked":
                    is_checked = True
            # for

            if is_checkbox:
                if is_checked:
                    checked.append(name)
                else:
                    unchecked.append(name)

            pos = content.find('<input ')
        # while
        return checked, unchecked

    def assert_link_quality(self, content, template_name):
        """ assert the quality of links
            - links to external sites must have target="_blank" and rel="noopener noreferrer"
            - links should not be empty
        """
        # strip head
        pos = content.find('<body')
        content = content[pos:]

        while len(content):
            # find the start of a new url
            pos = content.find('<a ')
            if pos >= 0:
                content = content[pos:]
                pos = content.find('</a>')
                link = content[:pos+4]
                content = content[pos+4:]
                # filter out website-internal links
                if link.find('href="/') < 0 and link.find('href="#') < 0 and link.find('href="mailto:') < 0:
                    if link.find('href=""') >= 0:   # pragma: no cover
                        self.fail(msg='Unexpected empty link %s on page %s' % (link, template_name))
                    else:
                        # remainder must be links that leave the website
                        # these must target a blank window
                        if 'target="_blank"' not in link:            # pragma: no cover
                            self.fail(msg='Missing target="_blank" in link %s on page %s' % (link, template_name))
                        if 'rel="noopener noreferrer"' not in link:  # pragma: no cover
                            self.fail(msg='Missing rel="noopener noreferrer" in link %s on page %s' % (link, template_name))
            else:
                content = ''
        # while

    def assert_scripts_clean(self, html, template_name):
        pos = html.find('<script ')
        while pos >= 0:
            html = html[pos:]
            pos = html.find('</script>')
            script = html[:pos+9]

            pos = script.find('console.log')
            if pos >= 0:        # pragma: no branch
                self.fail(msg='Detected console.log usage in script from template %s' % template_name)

            html = html[pos+9:]
            pos = html.find('<script ')
        # while

    def assert_html_ok(self, response):
        """ Doe een aantal basic checks op een html response """
        assert isinstance(self, TestCase)
        html = str(response.content)
        html = self._remove_debugtoolbar(html)
        self.assertContains(response, "<html")
        self.assertIn("lang=", html)
        self.assertIn("</html>", html)
        self.assertIn("<head>", html)
        self.assertIn("</head>", html)
        self.assertIn("<body ", html)
        self.assertIn("</body>", html)
        self.assertIn("<!DOCTYPE html>", html)
        self.assert_link_quality(html, response.templates[0].name)
        self.assert_scripts_clean(html, response.templates[0].name)

    def assert_is_bestand(self, response):
        assert isinstance(self, TestCase)

        # check the headers that make this a download
        # print("response: ", repr([(a,b) for a,b in response.items()]))
        content_type_header = response['Content-Type']
        self.assertEqual(content_type_header, 'text/csv')
        content_disposition_header = response['Content-Disposition']
        self.assertTrue(content_disposition_header.startswith('attachment; filename='))

        # ensure the file is not empty
        self.assertTrue(len(str(response.content)) > 30)

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
