# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import auth
from django.conf import settings
from Account.models import Account, account_create
from Functie.view_vhpg import account_vhpg_is_geaccepteerd
from bs4 import BeautifulSoup
from django.test import TestCase
import subprocess
import tempfile
import vnujar
import pyotp


# template names found by assert_html_ok
validated_templates = list()

# these templates are included by other templates
included_templates = (
    'plein/site_layout.dtl',
    'plein/menu.dtl',
    'plein/card.dtl',
    'plein/card_logo.dtl',
    'plein/andere-sites-van-de-nhb.dtl',
    'plein/ga-naar-live-server.dtl',
    'overig/site-feedback-sidebar.dtl',
    'logboek/common.dtl'
)

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

    def _get_useful_template_name(self, response):
        lst = [tmpl.name for tmpl in response.templates if tmpl.name not in included_templates and not tmpl.name.startswith('django/forms')]
        return ", ".join(lst)

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
        assert isinstance(self, TestCase)
        self.assertEqual(resp.status_code, 302)  # 302 = Redirect
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def e2e_login_and_pass_otp(self, account, wachtwoord=None):
        self.e2e_login(account, wachtwoord)
        # door de login is een cookie opgeslagen met het csrf token
        assert isinstance(self, TestCase)
        resp = self.client.post('/functie/otp-controle/', {'otp_code': pyotp.TOTP(account.otp_code).now()})
        assert isinstance(self, E2EHelpers)
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def _wissel_naar_rol(self, rol, expected_redirect):
        assert isinstance(self, TestCase)
        resp = self.client.post('/functie/activeer-rol/%s/' % rol)
        assert isinstance(self, E2EHelpers)
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
        assert isinstance(self, E2EHelpers)
        self.assert_is_redirect(resp, expected_redirect)

    def e2e_check_rol(self, rol_verwacht):
        assert isinstance(self, TestCase)
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
        assert isinstance(self, TestCase)

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
        assert isinstance(self, TestCase)
        pos = html.find('<script ')
        while pos >= 0:
            html = html[pos:]
            pos = html.find('</script>')
            script = html[:pos+9]

            pos = script.find('console.log')
            if pos >= 0:
                self.fail(msg='Detected console.log usage in script from template %s' % template_name)   # pragma: no cover

            html = html[pos+9:]
            pos = html.find('<script ')
        # while

    _VALIDATE_IGNORE = (
        'info warning: The “type” attribute is unnecessary for JavaScript resources.',
        'error: Attribute “loading” not allowed on element “img” at this point.'            # too new
    )

    def _validate_html(self, html):
        """ Run the HTML5 validator """
        issues = list()

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as tmp:
            tmp.write(html)
            tmp.flush()

            # credits to html5validator
            vnu_jar_location = vnujar.__file__.replace('__init__.pyc', 'vnu.jar').replace('__init__.py', 'vnu.jar')
            proc = subprocess.Popen(["java", "-jar", vnu_jar_location, tmp.name],
                                    stderr=subprocess.PIPE)
            proc.wait(timeout=5)
            # returncode is 0 als er geen problemen gevonden zijn
            if proc.returncode:
                lines = html.splitlines()

                # feedback staat in stderr
                msg = proc.stderr.read().decode('utf-8')

                # remove tmp filename from error message
                msg = msg.replace('"file:%s":' % tmp.name, '')
                for issue in msg.splitlines():
                    # extract location information (line.pos)
                    spl = issue.split(': ')     # 1.2091-1.2094
                    locs = spl[0].split('-')
                    l1, p1 = locs[0].split('.')
                    l2, p2 = locs[1].split('.')
                    if l1 == l2:
                        l1 = int(l1)
                        p1 = int(p1)
                        p2 = int(p2)
                        p1 -= 20
                        if p1 < 1:
                            p1 = 1
                        p2 += 20
                        line = lines[l1-1]
                        context = line[p1-1:p2]
                    else:
                        # TODO
                        context = ''
                        pass
                    clean = ": ".join(spl[1:])
                    if clean not in issues:
                        if clean not in self._VALIDATE_IGNORE:
                            clean += " ==> %s" % context
                            issues.append(clean)
                # for

        # tmp file is deleted here
        return issues

    _BLOCK_LEVEL_ELEMENTS = (
        'address', 'article', 'aside', 'canvas', 'figcaption', 'figure', 'footer',
        'blockquote', 'dd', 'div', 'dl', 'dt', 'fieldset',
        'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li',
        'main', 'nav', 'noscript', 'ol', 'p', 'pre', 'pre', 'section', 'table', 'tfoot', 'ul', 'video'
    )

    def _assert_no_div_in_p(self, response, html):
        pos = html.find('<p')
        while pos >= 0:
            html = html[pos+2:]
            pos = html.find('</p')
            sub = html[:pos]
            # see https://stackoverflow.com/questions/21084870/no-p-element-in-scope-but-a-p-end-tag-seen-w3c-validation
            for elem in self._BLOCK_LEVEL_ELEMENTS:
                elem_pos = sub.find('<' + elem)
                if elem_pos >= 0:
                    elem_pos -= 20
                    if elem_pos < 0:
                        elem_pos = 0
                    msg = "Bad HTML (template: %s):" % self._get_useful_template_name(response)
                    msg += "\n   Found block-level element '%s' inside 'p'" % elem
                    msg = msg + "\n   ==> " + sub[elem_pos:elem_pos+40]
                    assert isinstance(self, TestCase)
                    self.fail(msg=msg)
            # for
            html = html[pos+3:]
            pos = html.find('<p')
        # while

    def assert_html_ok(self, response):
        """ Doe een aantal basic checks op een html response """
        html = response.content.decode('utf-8')
        html = self._remove_debugtoolbar(html)

        dtl = self._get_useful_template_name(response)
        if dtl not in validated_templates:
            validated_templates.append(dtl)

        assert isinstance(self, TestCase)
        self.assertIn("<!DOCTYPE html>", html, msg='Missing DOCTYPE at start of %s' % dtl)
        self.assertIn("<html", html, msg='Missing <html in %s' % dtl)
        self.assertIn("<head", html, msg='Missing <head in %s' % dtl)
        self.assertIn("<body", html, msg='Missing <body in %s' % dtl)
        self.assertIn("</head>", html, msg='Missing </head> in %s' % dtl)
        self.assertIn("</body>", html, msg='Missing </body> in %s' % dtl)
        self.assertIn("</html>", html, msg='Missing </html> in %s' % dtl)
        self.assertIn("lang=", html, msg='lang= missing in %s' % dtl)
        self.assertNotIn('<th/>', html, msg='Illegal <th/> must be replaced with <th></th> in %s' % dtl)
        self.assertNotIn('<td/>', html, msg='Illegal <td/> must be replaced with <td></td> in %s' % dtl)
        self.assertNotIn('<thead><th>', html, msg='Missing <tr> between <thead> and <th> in %s' % dtl)

        assert isinstance(self, E2EHelpers)
        self.assert_link_quality(html, dtl)
        self.assert_scripts_clean(html, dtl)
        self._assert_no_div_in_p(response, html)

        urls = self.extract_all_urls(response)
        for url in urls:
            if url.find(" ") >= 0:
                assert isinstance(self, TestCase)
                self.fail(msg="Unexpected space in url %s on page %s" % (repr(url), dtl))
        # for

        if settings.TEST_VALIDATE_HTML:
            issues = self._validate_html(html)
            if len(issues):
                msg = 'Invalid HTML (template: %s):\n' % dtl
                for issue in issues:
                    msg += "    %s\n" % issue
                # for
                assert isinstance(self, TestCase)
                self.fail(msg=msg)

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
        assert isinstance(self, TestCase)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, expected_url)


# end of file
