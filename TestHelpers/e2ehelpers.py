# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import auth
from django.core import management
from django.conf import settings
from django.test import TestCase, Client
from django.db import connection
from Account.models import Account
from Account.operations import account_create
from Functie.view_vhpg import account_vhpg_is_geaccepteerd
from TestHelpers.e2estatus import validated_templates, included_templates
from contextlib import contextmanager
from bs4 import BeautifulSoup
import subprocess
import traceback
import datetime
import tempfile
import vnujar
import pyotp
import time
import io


# debug optie: toon waar in de code de queries vandaan komen
REPORT_QUERY_ORIGINS = False


class MyQueryTracer(object):
    def __init__(self):
        self.trace = list()
        self.started_at = datetime.datetime.now()
        self.total_duration_us = 0
        self.stack_counts = dict()      # [stack] = count

    def __call__(self, execute, sql, params, many, context):
        call = {'sql': sql}
        # print('sql:', sql)            # query with some %s in it
        # print('params:', params)      # params for the %s ?
        # print('many:', many)          # true/false

        time_start = time.monotonic_ns()
        call['now'] = time_start

        call['stack'] = stack = list()
        for fname, linenr, base, code in traceback.extract_stack():
            if base != '__call__' and not fname.startswith('/usr/lib') and '/site-packages/' not in fname and 'manage.py' not in fname:
                stack.append((fname, linenr, base))
            elif base == 'render' and 'template/response.py' in fname:
                stack.append((fname, linenr, base))
        # for

        if REPORT_QUERY_ORIGINS:                        # pragma: no cover
            msg = ''
            for fname, linenr, base in stack:
                msg += '\n         %s:%s %s' % (fname[-30:], linenr, base)
            try:
                self.stack_counts[msg] += 1
            except KeyError:
                self.stack_counts[msg] = 1

        time_end = time.monotonic_ns()
        time_delta_ns = time_end - time_start
        duration_us = int(time_delta_ns / 1000)
        call['duration_us'] = duration_us
        self.total_duration_us += duration_us

        self.trace.append(call)

        execute(sql, params, many, context)


class E2EHelpers(TestCase):

    """ Helpers voor het End-to-End testen, dus zoals de gebruiker de website gebruikt vanuit de browser

        mixin class voor django.test.TestCase
    """

    WACHTWOORD = "qewretrytuyi"     # sterk genoeg default wachtwoord

    client: Client                  # for code completion / code inspection

    def e2e_logout(self):
        # in case the test client behaves different from the real website, we can compensate here
        self.client.logout()

    @staticmethod
    def e2e_account_accepteert_vhpg(account):
        account_vhpg_is_geaccepteerd(account)

    @staticmethod
    def _remove_debug_toolbar(html):
        """ removes the debug toolbar code """
        pos = html.find('<link rel="stylesheet" href="/static/debug_toolbar/css/print.css"')
        if pos > 0:     # pragma: no cover
            html = html[:pos] + '<!-- removed debug toolbar --></body></html>'
        return html

    @staticmethod
    def _get_useful_template_name(response):
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

    def e2e_login_no_check(self, account, wachtwoord=None, follow=False):
        """ log in op de website via de voordeur, zodat alle rechten geëvalueerd worden """
        if not wachtwoord:
            wachtwoord = self.WACHTWOORD
        resp = self.client.post('/account/login/', {'login_naam': account.username,
                                                    'wachtwoord': wachtwoord},
                                follow=follow)
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
        resp = self.client.post('/functie/otp-controle/', {'otp_code': pyotp.TOTP(account.otp_code).now()})
        self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

    def _wissel_naar_rol(self, rol, expected_redirect):
        resp = self.client.post('/functie/activeer-rol/%s/' % rol)
        self.assert_is_redirect(resp, expected_redirect)

    def e2e_wisselnaarrol_bb(self):
        #self._wissel_naar_rol('BB', '/functie/wissel-van-rol/')
        self._wissel_naar_rol('BB', '/plein/')

    def e2e_wisselnaarrol_sporter(self):
        self._wissel_naar_rol('sporter', '/plein/')

    def e2e_wisselnaarrol_gebruiker(self):
        self._wissel_naar_rol('geen', '/functie/wissel-van-rol/')

    def e2e_wissel_naar_functie(self, functie):
        resp = self.client.post('/functie/activeer-functie/%s/' % functie.pk)

        if functie.rol in ('SEC', 'HWL', 'WL'):
            self.assert_is_redirect(resp, '/vereniging/')
        elif functie.rol in ('BKO', 'RKO', 'RCL') and resp.url.startswith('/bondscompetities/'):
            # als er geen competitie is, dan verwijst deze alsnog naar wissel-van-rol
            self.assert_is_redirect(resp, '/bondscompetities/##')
        else:
            self.assert_is_redirect(resp, '/functie/wissel-van-rol/')

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

    def e2e_dump_resp(self, resp):                        # pragma: no cover
        print("status code:", resp.status_code)
        print(repr(resp))
        if resp.status_code == 302:
            print("redirect to url:", resp.url)
        else:
            print('templates used:')
            for templ in resp.templates:
                print('   %s' % repr(templ.name))
            # for
        content = str(resp.content)
        content = self._remove_debug_toolbar(content)
        if len(content) < 50:
            print("very short content:", content)
        else:
            soup = BeautifulSoup(content, features="html.parser")
            print(soup.prettify())

    def extract_all_urls(self, resp, skip_menu=False, skip_smileys=True, skip_broodkruimels=True, data_urls=True):
        content = str(resp.content)
        content = self._remove_debug_toolbar(content)
        if skip_menu:
            # menu is the in the navbar at the top of the page
            # it ends with the nav-content-scrollbar div
            pos = content.find('<div class="nav-content-scrollbar">')
            if pos >= 0:
                content = content[pos:]
        else:
            # skip the headers
            pos = content.find('<body')
            if pos > 0:                             # pragma: no branch
                content = content[pos:]             # strip head section

        if skip_broodkruimels:
            pos = content.find('class="broodkruimels-')
            if pos >= 0:
                content = content[pos:]
                pos = content.find('</div>')
                content = content[pos:]

        urls = list()
        while len(content):
            # find the start of a new url
            pos1 = content.find('href="')
            pos2 = content.find('action="')
            pos3 = content.find('data-url="')
            if pos1 >= 0 and (pos2 == -1 or pos2 > pos1) and (pos3 == -1 or pos3 > pos1):
                content = content[pos1+6:]       # strip all before href
            elif pos2 >= 0 and (pos1 == -1 or pos1 > pos2) and (pos3 == -1 or pos3 > pos2):
                content = content[pos2+8:]       # strip all before action
            elif pos3 >= 0:
                content = content[pos3+10:]      # strip all before data-url
            else:
                # all interesting aspects handled
                content = ""

            # find the end of the new url
            pos = content.find('"')
            if pos > 0:
                url = content[:pos]
                content = content[pos:]
                if url != "#":
                    if not (skip_smileys and url.startswith('/feedback/')):
                        urls.append(url)
        # while
        return urls

    def extract_checkboxes(self, resp):
        content = str(resp.content)
        content = self._remove_debug_toolbar(content)
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
                        name = spl[1].replace('"', '')  # strip double-quotes
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

    SAFE_LINKS = ('/plein/', '/sporter/', '/bondscompetities/', '/records/', '/account/login/', '/account/logout/')

    def _test_link(self, link, template_name):
        """ make sure the link works """
        if link in self.SAFE_LINKS or link.startswith('/feedback/') or link.startswith('#'):
            return

        resp = self.client.head(link)
        if resp.status_code != 200:
            self.fail(msg='Link not usable (code %s) on page %s (%s)' % (resp.status_code, template_name, link))

    def assert_broodkruimels(self, content, template_name):
        # find the start
        pos = content.find('class="broodkruimels-link" href="')
        while pos > 0:
            content = content[pos+33:]
            link = content[:content.find('"')]
            self._test_link(link, template_name)
            pos = content.find('class="broodkruimels-link" href="')
        # while

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
                # check the link (skip if plain button with onclick handler)
                if link.find('href="') >= 0:
                    # filter out website-internal links
                    if link.find('href="/') < 0 and link.find('href="#') < 0:
                        if link.find('href=""') >= 0 or link.find('href="mailto:"') >= 0:   # pragma: no cover
                            self.fail(msg='Unexpected empty link %s on page %s' % (link, template_name))
                        elif link.find('href="mailto:') < 0 and link.find('javascript:history.go(-1)') < 0:
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
            if pos >= 0:
                self.fail(msg='Detected console.log usage in script from template %s' % template_name)   # pragma: no cover

            pos = script.find('/*')
            if pos >= 0:
                self.fail(msg='Found block comment in script from template %s' % template_name)     # pragma: no cover

            html = html[pos+9:]
            pos = html.find('<script ')
        # while

    _VALIDATE_IGNORE = (
        'info warning: The “type” attribute is unnecessary for JavaScript resources.',
        'error: Attribute “loading” not allowed on element “img” at this point.'            # too new
    )

    def _validate_html(self, html):                 # pragma: no cover
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
                if elem_pos >= 0:                   # pragma: no cover
                    elem_pos -= 20
                    if elem_pos < 0:
                        elem_pos = 0
                    msg = "Bad HTML (template: %s):" % self._get_useful_template_name(response)
                    msg += "\n   Found block-level element '%s' inside 'p'" % elem
                    msg = msg + "\n   ==> " + sub[elem_pos:elem_pos+40]
                    self.fail(msg)
            # for
            html = html[pos+3:]
            pos = html.find('<p')
        # while

    def _assert_no_col_white(self, text, dtl):
        pos = text.find("class=")
        while pos > 0:
            text = text[pos + 6:]

            # find the end of this tag
            pos = text.find('>')
            klass = text[:pos]

            if klass.find("z-depth") < 0:
                p1 = klass.find("col s10")
                p2 = klass.find("white")
                if p1 >= 0 and p2 >= 0:
                    msg = 'Found grid col s10 + white (too much unused space on small) --> use separate div.white + padding:10px) in %s' % dtl
                    self.fail(msg)

            pos = text.find("class=")
        # while

    def assert_html_ok(self, response):
        """ Doe een aantal basic checks op een html response """
        html = response.content.decode('utf-8')
        html = self._remove_debug_toolbar(html)

        dtl = self._get_useful_template_name(response)
        # print('useful template names:', dtl)
        if dtl not in validated_templates:
            validated_templates.append(dtl)

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
        self.assertNotIn('<script>', html, msg='Missing type="application/javascript" in <script> in %s' % dtl)

        self.assert_link_quality(html, dtl)
        self.assert_broodkruimels(html, dtl)
        self.assert_scripts_clean(html, dtl)
        self._assert_no_div_in_p(response, html)
        self._assert_no_col_white(html, dtl)

        urls = self.extract_all_urls(response)
        for url in urls:
            if url.find(" ") >= 0:                  # pragma: no cover
                self.fail(msg="Unexpected space in url %s on page %s" % (repr(url), dtl))
        # for

        if settings.TEST_VALIDATE_HTML:             # pragma: no cover
            issues = self._validate_html(html)
            if len(issues):
                msg = 'Invalid HTML (template: %s):\n' % dtl
                for issue in issues:
                    msg += "    %s\n" % issue
                # for
                self.fail(msg=msg)

    def assert_is_bestand(self, response):
        # check the headers that make this a download
        # print("response: ", repr([(a,b) for a,b in response.items()]))
        content_type_header = response['Content-Type']
        self.assertEqual(content_type_header, 'text/csv')
        content_disposition_header = response['Content-Disposition']
        self.assertTrue(content_disposition_header.startswith('attachment; filename='))

        # ensure the file is not empty
        self.assertTrue(len(str(response.content)) > 30)

    @staticmethod
    def _get_templates_not_used(resp, template_names):
        """ returns True when any of the templates have not been used """
        lst = list(template_names)
        for templ in resp.templates:
            if templ.name in lst:
                lst.remove(templ.name)
        # for
        return lst

    def _is_fout_pagina(self, resp):        # pragma: no cover
        if resp.status_code == 200:
            lst = self._get_templates_not_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))
            if len(lst) == 0:
                return True
            lst = self._get_templates_not_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))
            if len(lst) == 0:
                return True
        return False

    def assert_template_used(self, resp, template_names):
        """ Controleer dat de gevraagde templates gebruikt zijn """
        lst = self._get_templates_not_used(resp, template_names)
        if len(lst):    # pragma: no cover
            self.e2e_dump_resp(resp)
            msg = "Following templates should have been used: %s\n" % repr(lst)
            msg += "Actually used: %s" % repr([t.name for t in resp.templates])
            self.assertTrue(False, msg=msg)

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

    def e2e_assert_other_http_commands_not_supported(self, url, post=True, delete=True, put=True, patch=True):
        """ Test een aantal 'common' http methoden
            en controleer dat deze niet ondersteund zijn (status code 405 = not allowed)
            POST, DELETE, PATCH
        """
        # toegestane status_codes:
        #   302 (redirect)
        #   403 (not allowed)
        #   404 (not found)
        #   405 (not allowed)
        accepted_status_codes = (302, 403, 404, 405)

        if post:
            resp = self.client.post(url)
            if resp.status_code not in accepted_status_codes and not self._is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij POST command' % resp.status_code)     # pragma: no cover

        if delete:                            # pragma: no cover
            resp = self.client.delete(url)
            if resp.status_code not in accepted_status_codes and not self._is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij DELETE command' % resp.status_code)

        if put:                               # pragma: no cover
            resp = self.client.put(url)
            if resp.status_code not in accepted_status_codes and not self._is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij PUT command' % resp.status_code)

        if patch:                             # pragma: no cover
            resp = self.client.patch(url)
            if resp.status_code not in accepted_status_codes and not self._is_fout_pagina(resp):
                self.fail(msg='Onverwachte status code %s bij PATCH command' % resp.status_code)

    def assert_is_redirect(self, resp, expected_url):
        if resp.status_code != 302:  # pragma: no cover
            # geef een iets uitgebreider antwoord
            msg = "status_code: %s != 302" % resp.status_code
            if resp.status_code == 200:
                self.e2e_dump_resp(resp)
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)
        pos = expected_url.find('##')
        if pos > 0:
            self.assertTrue(resp.url.startswith(expected_url[:pos]))
        else:
            self.assertEqual(resp.url, expected_url)

    def assert_is_redirect_not_plein(self, resp):
        if resp.status_code != 302:                     # pragma: no cover
            # geef een iets uitgebreider antwoord
            msg = "status_code: %s != 302" % resp.status_code
            if resp.status_code == 200:
                self.e2e_dump_resp(resp)
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)

        self.assertNotEqual(resp.url, '/plein/')    # redirect naar plein is typisch een reject om rechten

    @staticmethod
    def _find_statement(query, start):                  # pragma: no cover
        best = -1
        word_len = 0
        for word in (  # 'SELECT', 'DELETE FROM', 'INSERT INTO',
                     ' WHERE ', ' LEFT OUTER JOIN ', ' INNER JOIN ', ' LEFT JOIN ', ' JOIN ',
                     ' ORDER BY ', ' GROUP BY ', ' ON ', ' FROM ', ' VALUES '):
            pos = query.find(word, start)
            if pos >= 0 and (best == -1 or pos < best):
                best = pos
                word_len = len(word)
        # for
        return best, word_len

    def _reformat_sql(self, prefix, query):       # pragma: no cover
        start = 0
        pos, word_len = self._find_statement(query, start)
        prefix = prefix[:-1]        # because pos starts with a space
        while pos >= 0:
            query = query[:pos] + prefix + query[pos:]
            start = pos + word_len + len(prefix)
            pos, word_len = self._find_statement(query, start)
        # while
        return query

    @contextmanager
    def assert_max_queries(self, num, check_duration=True):
        tracer = MyQueryTracer()
        try:
            with connection.execute_wrapper(tracer):
                yield
        finally:
            if check_duration:
                duration = datetime.datetime.now() - tracer.started_at
                duration_seconds = duration.seconds + (duration.microseconds / 1000000.0)
            else:
                duration_seconds = 0.0

            count = len(tracer.trace)

            if num == -1:                         # pragma: no cover
                print('Operation resulted in %s queries' % count)

            elif count > num:                     # pragma: no cover
                queries = 'Captured queries:'
                prefix = '\n       '
                limit = 200     # begrens aantal queries dat we printen
                for i, call in enumerate(tracer.trace, start=1):
                    if i > 1:
                        queries += '\n'
                    queries += prefix + str(call['now'])
                    queries += '\n [%d]  ' % i
                    queries += self._reformat_sql(prefix, call['sql'])
                    queries += prefix + '%s µs' % call['duration_us']
                    queries += '\n'
                    for fname, linenr, base in call['stack']:
                        queries += prefix + '%s:%s   %s' % (fname, linenr, base)
                    # for
                    limit -= 1
                    if limit <= 0:
                        break
                # for

                msg = "Too many queries: %s; maximum %d. " % (count, num)
                self.fail(msg=msg + queries)

            if count <= num:
                # kijk of het wat minder kan
                if num > 20:
                    ongebruikt = num - count
                    if ongebruikt / num > 0.25:                                     # pragma: no cover
                        self.fail(msg="Maximum (%s) has a lot of margin. Can be set as low as %s" % (num, count))

            if duration_seconds > 1.5:                                              # pragma: no cover
                print("Operation took suspiciously long: %.2f seconds (%s queries took %.2f ms)" % (
                                    duration_seconds, len(tracer.trace), tracer.total_duration_us / 1000.0))

            if len(tracer.trace) > 500:                                             # pragma: no cover
                print("Operation required a lot of database interactions: %s queries" % len(tracer.trace))

        if REPORT_QUERY_ORIGINS:                                                    # pragma: no cover
            # sorteer op aantal aanroepen
            counts = list()
            for msg, count in tracer.stack_counts.items():
                tup = (count, msg)
                counts.append(tup)
            # for
            counts.sort(reverse=True)       # hoogste eerst
            first = True
            for count, msg in counts:
                if count > 1:
                    if first:
                        first = False
                        print('-----')
                    print('%5s %s' % (count, msg[7:]))

    def assert403(self, resp, expected_msg=''):
        # controleer dat we op de speciale code-403 handler pagina gekomen zijn
        # of een redirect hebben gekregen naar de login pagina

        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')          # pragma: no cover

        if resp.status_code == 302:
            if resp.url != '/account/login/':
                self.e2e_dump_resp(resp)
                self.fail(msg="Onverwachte redirect naar %s" % resp.url)
        else:
            if resp.status_code != 200:     # pragma: no cover
                self.e2e_dump_resp(resp)
                self.fail(msg="Onverwachte status code %s; verwacht: 200" % resp.status_code)

            self.assertEqual(resp.status_code, 200)
            self.assert_template_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))

            if expected_msg:
                pagina = str(resp.content)
                if expected_msg not in pagina:                                          # pragma: no cover
                    # haal de nuttige regel informatie uit de 403 pagina en toon die
                    pos = pagina.find('<code>')
                    pagina = pagina[pos+6:]
                    pos = pagina.find('</code>')
                    pagina = pagina[:pos]
                    self.fail(msg='403 pagina bevat %s in plaats van %s' % (repr(pagina), repr(expected_msg)))

    def assert404(self, resp, expected_msg=''):
        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')          # pragma: no cover

        # controleer dat we op de speciale code-404 handler pagina gekomen zijn
        if resp.status_code != 200:     # pragma: no cover
            self.e2e_dump_resp(resp)
            self.fail(msg="Onverwachte status code %s; verwacht: 200" % resp.status_code)

        # controleer dat we op de speciale code-404 handler pagina gekomen zijn
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))

        if expected_msg:
            pagina = str(resp.content)
            if expected_msg not in pagina:                                          # pragma: no cover
                # haal de nuttige regel informatie uit de 404 pagina en toon die
                pos = pagina.find('<code>')
                pagina = pagina[pos+6:]
                pos = pagina.find('</code>')
                pagina = pagina[:pos]
                self.fail(msg='404 pagina bevat %s; verwacht: %s' % (repr(pagina), repr(expected_msg)))
        else:
            pagina = str(resp.content)
            pos = pagina.find('<code>')
            pagina = pagina[pos + 6:]
            pos = pagina.find('</code>')
            pagina = pagina[:pos]
            print('\nassert404: geen expected msg! Inhoud pagina: %s' % repr(pagina))

    def assert200_file(self, resp):
        if resp.status_code != 200:                                 # pragma: no cover
            self.e2e_dump_resp(resp)
            self.fail(msg="Onverwachte foutcode %s in plaats van 200" % resp.status_code)

        header = resp['Content-Disposition']
        if not header.startswith('attachment; filename'):           # pragma: no cover
            self.fail(msg="Response is geen file attachment")

    def verwerk_regiocomp_mutaties(self, show_warnings=True, show_all=False):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('regiocomp_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        err_msg = f1.getvalue()
        if '[ERROR]' in err_msg:                        # pragma: no cover
            self.fail(msg='Onverwachte fout van regiocomp_mutaties:\n' + err_msg)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

    def verwerk_bestel_mutaties(self, show_warnings=True, show_all=False):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('bestel_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        err_msg = f1.getvalue()
        if '[ERROR]' in err_msg:                        # pragma: no cover
            self.fail(msg='Onverwachte fout van bestel_mutaties:\n' + err_msg)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

# end of file
