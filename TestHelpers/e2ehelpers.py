# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.contrib import auth
from django.core import management
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.db import connection
from Account.models import Account
from Account.operations import account_create
from Functie.view_vhpg import account_vhpg_is_geaccepteerd
from Mailer.models import MailQueue
from TestHelpers.e2estatus import validated_templates, included_templates, consistent_email_templates
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
        lst = [tmpl.name for tmpl in response.templates if tmpl.name not in included_templates and not tmpl.name.startswith('django/forms') and not tmpl.name.startswith('email_')]
        if len(lst) > 1:        # pragma: no cover
            print('[WARNING] e2ehelpers._get_useful_template_name: too many choices!!! %s' % repr(lst))
        return lst[0]

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
        if resp.status_code != 302:
            self.e2e_dump_resp(resp)
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
        # self._wissel_naar_rol('BB', '/functie/wissel-van-rol/')
        self._wissel_naar_rol('BB', '/plein/')

    def e2e_wisselnaarrol_sporter(self):
        self._wissel_naar_rol('sporter', '/plein/')

    def e2e_wisselnaarrol_gebruiker(self):
        self._wissel_naar_rol('geen', '/functie/wissel-van-rol/')

    WISSEL_VAN_ROL_EXPECTED_URL = {
        'SEC': '/vereniging/',
        'HWL': '/vereniging/',
        'WL' : '/vereniging/',
        'BKO': '/bondscompetities/##',
        'RKO': '/bondscompetities/##',
        'RCL': '/bondscompetities/##',
        'MO' : '/opleidingen/manager/',
        'SUP': '/feedback/inzicht/',
        'MWW': '/webwinkel/manager/',
        'MWZ': '/functie/wissel-van-rol/',      # '/kalender/'
    }

    def e2e_wissel_naar_functie(self, functie):
        resp = self.client.post('/functie/activeer-functie/%s/' % functie.pk)

        try:
            expected_url = self.WISSEL_VAN_ROL_EXPECTED_URL[functie.rol]
        except KeyError:
            expected_url = 'functie ontbreekt'

        # als er geen competitie is, dan verwijst deze alsnog naar wissel-van-rol
        if functie.rol in ('BKO', 'RKO', 'RCL'):
            if resp.status_code == 302 and not resp.url.startswith('/bondscompetities/'):
                expected_url = '/functie/wissel-van-rol/'

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

    def _interpreteer_resp(self, resp):
        long_msg = list()
        long_msg.append("status code: %s" % resp.status_code)
        long_msg.append(repr(resp))

        is_attachment = False
        if resp.status_code == 302:
            msg = "redirect to url: %s" % resp.url
            long_msg.append(msg)
            return msg, long_msg

        try:
            header = resp['Content-Disposition']
        except KeyError:
            pass
        else:
            is_attachment = header.startswith('attachment; filename')

            if is_attachment:
                msg = 'content is an attachment: %s...' % str(resp.content)[:20]
                long_msg.append(msg)
                return msg, long_msg

        content = str(resp.content)
        content = self._remove_debug_toolbar(content)
        if len(content) < 50:
            msg = "very short content: %s" % content
            long_msg.append(msg)
            return msg, long_msg

        is_404 = resp.status_code == 404
        if not is_404:
            is_404 = any(['plein/fout_404.dtl' in templ.name for templ in resp.templates])

        if is_404:
            pos = content.find('<meta path="')
            if pos > 0:
                # pagina bestaat echt niet
                sub = content[pos+12:pos+300]
                pos = sub.find('"')
                msg = '404 pagina niet gevonden: %s' % sub[:pos]
                long_msg.append(msg)
                return msg, long_msg

            # zoek de expliciete foutmelding
            pos = content.find('<code>')
            if pos > 0:
                sub = content[pos + 6:]
                pos = sub.find('</code>')
                msg = '404 met melding %s' % repr(sub[:pos])
                long_msg.append(msg)
                return msg, long_msg

        if not is_attachment:
            long_msg.append('templates used:')
            for templ in resp.templates:
                long_msg.append('   %s' % repr(templ.name))
            # for

        soup = BeautifulSoup(content, features="html.parser")
        long_msg.append(soup.prettify())

        return '', long_msg

    def e2e_dump_resp(self, resp):                        # pragma: no cover
        short_msg, long_msg = self._interpreteer_resp(resp)
        print("\ne2e_dump_resp:")
        print("\n".join(long_msg))
        return

    def extract_all_urls(self, resp, skip_menu=False, skip_smileys=True, skip_broodkruimels=True, data_urls=True):
        content = str(resp.content)
        content = self._remove_debug_toolbar(content)
        if skip_menu:
            # menu is the in the navbar at the top of the page
            # it ends with the nav-content-scrollbar div
            pos = content.find('<div class="nav-content-scrollbar">')
            if pos >= 0:                                                        # pragma: no branch
                content = content[pos:]
        else:
            # skip the headers
            pos = content.find('<body')
            if pos > 0:                                                         # pragma: no branch
                # strip head section
                content = content[pos:]

        if skip_broodkruimels:                                                  # pragma: no branch
            pos = content.find('class="broodkruimels-')
            if pos >= 0:
                remainder = content[pos:]
                content = content[:pos]             # behoud de navbar
                pos = remainder.find('</div>')
                content += remainder[pos+6:]

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

    @staticmethod
    def _get_error_msg_from_403_page(resp):                                         # pragma: no cover
        error_msg = '??403??'
        pagina = str(resp.content)
        pos = pagina.find('<code>')
        pos2 = pagina.find('</code>')
        if pos > 0 and pos2 > 0:
            error_msg = pagina[pos+6:pos2]
        elif 'We hebben geen extra informatie over deze situatie' in pagina:
            error_msg = '<not provided>'
        else:
            print('_get_error_msg_from_403_page: pagina=%s' % repr(pagina))
        return error_msg

    SAFE_LINKS = ('/plein/', '/bondscompetities/', '/records/', '/account/login/', '/account/logout/')

    def _test_link(self, link, template_name):
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
                error_msg = self._get_error_msg_from_403_page(resp)
                self.fail(msg='Found NOK href %s that gives code 403 with message "%s" on page %s' % (
                            repr(link), error_msg, template_name))

            if templ.name == 'plein/fout_404.dtl':                                  # pragma: no cover
                self.fail(msg='Found NOK href %s that gives code 404 on page %s' % (
                            repr(link), template_name))
        # for

    def assert_broodkruimels(self, content, template_name):
        # find the start
        pos = content.find('class="broodkruimels-link" href="')
        while pos > 0:
            content = content[pos+33:]
            link = content[:content.find('"')]
            self._test_link(link, template_name)
            pos = content.find('class="broodkruimels-link" href="')
        # while

    def assert_link_quality(self, content, template_name, is_email=False):
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
                            if not is_email and 'rel="noopener noreferrer"' not in link:  # pragma: no cover
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
            with subprocess.Popen(["java", "-jar", vnu_jar_location, tmp.name], stderr=subprocess.PIPE) as proc:
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

    def _assert_no_div_in_p(self, html, dtl):
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
                    msg = "Bad HTML (template: %s):" % dtl
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
                if p1 >= 0 and p2 >= 0:             # pragma: no cover
                    msg = 'Found grid col s10 + white (too much unused space on small) --> use separate div.white + padding:10px) in %s' % dtl
                    self.fail(msg)

            pos = text.find("class=")
        # while

    def _assert_inputs(self, html, dtl):
        pos = html.find('<input ')
        while pos > 0:
            inp = html[pos+7:]
            pos = html.find('<input ', pos+7)

            # find the end of the tag
            # dit is erg robust, maar werkt goed genoeg
            endpos = inp.find('>')
            inp = inp[:endpos].strip()
            spl = inp.split(' ')
            # print('inp: %s' % repr(spl))
            for part in spl:
                if '=' in part:
                    part_spl = part.split('=')
                    tag = part_spl[0]
                    # print('part_spl: %s' % repr(part_spl))
                    if tag not in ('value', 'autofocus') and part_spl[1] in ('""', "''"):
                        msg = 'Found input tag %s with empty value: %s' % (repr(tag), repr(inp))
                        self.fail(msg)
            # for
        # while

    def _assert_html_basics(self, html, dtl):
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

    def _assert_template_bug(self, html, dtl):
        pos = html.find('##BUG')
        if pos >= 0:
            msg = html[pos:]
            context = html[pos-30:]
            pos = msg.find('##', 3)
            msg = msg[:pos+2]
            context = context[:pos+30]
            self.fail(msg='Bug in template %s: %s\nContext: %s' % (repr(dtl), msg, context))

    def assert_html_ok(self, response):
        """ Doe een aantal basic checks op een html response """
        html = response.content.decode('utf-8')
        html = self._remove_debug_toolbar(html)

        dtl = self._get_useful_template_name(response)
        # print('useful template name:', dtl)
        if dtl not in validated_templates:
            validated_templates.append(dtl)

        self._assert_html_basics(html, dtl)

        self.assertNotIn('<script>', html, msg='Missing type="application/javascript" in <script> in %s' % dtl)

        self.assert_link_quality(html, dtl)
        self.assert_broodkruimels(html, dtl)
        self.assert_scripts_clean(html, dtl)
        self._assert_no_div_in_p(html, dtl)
        self._assert_no_col_white(html, dtl)
        self._assert_inputs(html, dtl)

        self._assert_template_bug(html, dtl)

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

    def assert_email_html_ok(self, mail: MailQueue):
        html = mail.mail_html
        template_name = mail.template_used

        if template_name not in validated_templates:          # pragma: no branch
            validated_templates.append(template_name)

        self._assert_html_basics(html, template_name)

        self.assertNotIn('<script>', html, msg='Unexpected script in e-mail HTML (template: %s)' % template_name)
        self.assert_link_quality(html, template_name, is_email=True)
        self._assert_no_div_in_p(html, template_name)

        if settings.TEST_VALIDATE_HTML:             # pragma: no cover
            issues = self._validate_html(html)
            if len(issues):
                msg = 'Invalid HTML (template: %s):\n' % template_name
                for issue in issues:
                    msg += "    %s\n" % issue
                # for
                self.fail(msg=msg)

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
            short_msg, long_msg = self._interpreteer_resp(resp)
            if short_msg:
                msg = short_msg + " in plaats van de juiste templates"
            else:
                print("\n".join(long_msg))
                msg = "Following templates should have been used: %s\n" % repr(lst)
                msg += "Actually used: %s" % repr([t.name for t in resp.templates])
                msg += "\n" + short_msg
            self.fail(msg=msg)

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
        if resp.status_code != 302:                     # pragma: no cover
            # geef een iets uitgebreider antwoord
            if resp.status_code == 200:
                short_msg, _ = self._interpreteer_resp(resp)
                msg = "no redirect but " + short_msg
            else:
                msg = "status_code: %s != 302" % resp.status_code
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)
        pos = expected_url.find('##')
        if pos > 0:
            self.assertTrue(resp.url.startswith(expected_url[:pos]))
        else:
            self.assertEqual(expected_url, resp.url)

    def assert_is_redirect_not_plein(self, resp):
        if resp.status_code != 302:                     # pragma: no cover
            # geef een iets uitgebreider antwoord
            msg = "status_code: %s != 302" % resp.status_code
            if resp.status_code == 200:
                self.e2e_dump_resp(resp)
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)

        self.assertNotEqual(resp.url, '/plein/')    # redirect naar plein is typisch een reject om rechten

    def assert_is_redirect_login(self, resp):
        if resp.status_code != 302:                     # pragma: no cover
            # geef een iets uitgebreider antwoord
            msg = "status_code: %s != 302" % resp.status_code
            if resp.status_code == 200:
                self.e2e_dump_resp(resp)
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)

        self.assertTrue(resp.url.startswith, '/account/login/')

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

    def assert403(self, resp, expected_msg='Geen toegang'):
        # controleer dat we op de speciale code-403 handler pagina gekomen zijn
        # of een redirect hebben gekregen naar de login pagina

        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')            # pragma: no cover

        if resp.status_code == 302:
            if resp.url != '/account/login/':                                       # pragma: no cover
                self.e2e_dump_resp(resp)
                self.fail(msg="Onverwachte redirect naar %s" % resp.url)
        else:
            if resp.status_code != 200:     # pragma: no cover
                self.e2e_dump_resp(resp)
                self.fail(msg="Onverwachte status code %s; verwacht: 200" % resp.status_code)

            self.assertEqual(resp.status_code, 200)
            self.assert_template_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))

            if expected_msg:                                                        # pragma: no branch
                pagina = str(resp.content)
                if expected_msg not in pagina:                                      # pragma: no cover
                    # haal de nuttige regel informatie uit de 403 pagina en toon die
                    pos = pagina.find('<code>')
                    pagina = pagina[pos+6:]
                    pos = pagina.find('</code>')
                    pagina = pagina[:pos]
                    self.fail(msg='403 pagina bevat %s in plaats van %s' % (repr(pagina), repr(expected_msg)))

    def assert404(self, resp, expected_msg=''):
        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')            # pragma: no cover

        # controleer dat we op de speciale code-404 handler pagina gekomen zijn
        if resp.status_code != 200:                                                 # pragma: no cover
            self.e2e_dump_resp(resp)
            self.fail(msg="Onverwachte status code %s; verwacht: 200" % resp.status_code)

        # controleer dat we op de speciale code-404 handler pagina gekomen zijn
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))

        if expected_msg:                                                            # pragma: no branch
            pagina = str(resp.content)
            if expected_msg not in pagina:                                          # pragma: no cover
                # haal de nuttige regel informatie uit de 404 pagina en toon die
                pos = pagina.find('<code>')
                if pos >= 0:
                    pagina = pagina[pos+6:]
                    pos = pagina.find('</code>')
                    pagina = pagina[:pos]
                self.fail(msg='404 pagina bevat %s; verwacht: %s' % (repr(pagina), repr(expected_msg)))
        else:                                                                       # pragma: no cover
            pagina = str(resp.content)
            pos = pagina.find('<code>')
            if pos >= 0:
                pagina = pagina[pos + 6:]
                pos = pagina.find('</code>')
                pagina = pagina[:pos]
            self.fail(msg='404 pagina, maar geen expected_msg! Inhoud pagina: %s' % repr(pagina))

    def _assert_bestand(self, resp, expected_content_type):
        if resp.status_code != 200:                                 # pragma: no cover
            self.e2e_dump_resp(resp)
            self.fail(msg="Onverwachte foutcode %s in plaats van 200" % resp.status_code)

        # check the headers that make this a download
        # print("response: ", repr([(a,b) for a,b in response.items()]))
        content_type_header = resp['Content-Type']
        self.assertEqual(expected_content_type, content_type_header)
        content_disposition_header = resp['Content-Disposition']
        self.assertTrue(content_disposition_header.startswith('attachment; filename='))

        # ensure the file is not empty
        self.assertTrue(len(str(resp.content)) > 30)

    def assert200_is_bestand_csv(self, resp):
        self._assert_bestand(resp, 'text/csv')

    def assert200_is_bestand_xlsx(self, resp):
        self._assert_bestand(resp, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def assert200_is_bestand_xlsm(self, resp):
        self._assert_bestand(resp, 'application/vnd.ms-excel.sheet.macroEnabled.12')

    def run_management_command(self, *args, report_exit_code=True):
        """ Helper om code duplicate te verminderen en bij een SystemExit toch de traceback (in stderr) te tonen """
        f1 = io.StringIO()
        f2 = io.StringIO()
        try:
            management.call_command(*args, stderr=f1, stdout=f2)
        except SystemExit as exc:
            if report_exit_code:                # pragma: no cover
                msg = '\nmanagement commando genereerde een SystemExit\n'
                msg += 'commando: %s\n' % repr(args)
                msg += 'stderr:\n'
                msg += f1.getvalue()
                msg = msg.replace('\n', '\n  ')
                raise self.failureException(msg) from exc
        return f1, f2

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

        return f1, f2

    def verwerk_bestel_mutaties(self, show_warnings=True, show_all=False, fail_on_error=True):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('bestel_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if fail_on_error:
            err_msg = f1.getvalue()
            if '[ERROR]' in err_msg:                        # pragma: no cover
                self.fail(msg='Onverwachte fout van bestel_mutaties:\n' + err_msg)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:                                                     # pragma: no branch
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

        return f1, f2

    @staticmethod
    def verwerk_betaal_mutaties(betaal_api):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        with override_settings(BETAAL_API=betaal_api):
            management.call_command('betaal_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        return f1, f2

    def assert_consistent_email_html_text(self, email: MailQueue, ignore=()):
        """ Check that the text version and html version of the e-mail are consistent in wording and contents """

        template_name = email.template_used
        consistent_email_templates.append(template_name)

        issues = list()

        html = email.mail_html[:]

        html = html[html.find('<body'):]
        html = html[:html.find('</body>')]

        # verwijder alle style=".."
        pos = html.find(' style="')
        while pos > 0:
            pos2 = html.find('"', pos+8)
            if pos2 > pos:                                                      # pragma: no branch
                html = html[:pos] + html[pos2 + 1:]

            pos = html.find(' style="')
        # while

        # euro teken vindbaar maken
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&euro;', '€')
        html = html.replace('&quot;', '"')

        th_matched = list()

        for line in email.mail_text.split('\n'):
            line = line.strip()     # remove spaces used for layout
            if len(line) <= 3:      # kleine teksten matchen mogelijk verkeer en slaan een gat
                # skip empty lines
                continue

            # print('check line: %s' % repr(line))

            zoek = '>' + line + '<'
            pos = html.find(zoek)
            if pos > 0:
                # verwijder de tekst maar behoud de > en <
                html = html[:pos + 1] + html[pos + len(zoek) - 1:]
                continue

            # misschien lukt het wel als we de zin opsplitsen in twee stukken
            pos = zoek.find(': ')
            if pos > 0:
                zoek1 = zoek[:pos+1]            # begint met > en eindigt met :
                zoek2 = zoek[pos+1:].strip()    # eindigt met <

                if zoek1 in ignore:
                    continue

                pos = html.find(zoek1)
                if pos > 0:
                    # verwijder de tekst maar behoud de >
                    html = html[:pos+1] + html[pos + len(zoek1):]
                else:
                    # misschien is het een table header zonder dubbele punt
                    zoek1b = zoek1[:-1]     # verwijder :
                    zoek_th = '<th' + zoek1b + '</th>'
                    pos = html.find(zoek_th)
                    if pos > 0:                                                 # pragma: no branch
                        # verwijder de header en de tag
                        html = html[:pos] + html[pos + len(zoek_th):]
                        th_matched.append(zoek_th)
                    elif zoek1b not in th_matched:                              # pragma: no cover
                        issues.append('Kan tekst %s niet vinden in html e-mail' % repr(zoek1))

                pos = html.find(zoek2)
                if pos > 0:                                                     # pragma: no branch
                    # verwijder de tekst maar behoud de <
                    html = html[:pos] + html[pos + len(zoek2) - 1:]
                else:                                                           # pragma: no cover
                    issues.append('Kan tekst %s niet vinden in html e-mail' % repr(zoek2))

                continue        # pragma: no cover

            if line[-1] == ':':
                # probeer een zonder de dubbele punt
                zoek = '>' + line[:-1] + '<'
                pos = html.find(zoek)
                if pos > 0:                                                     # pragma: no branch
                    # verwijder de tekst maar behoud de > en <
                    html = html[:pos + 1] + html[pos + len(zoek) - 1:]
                    continue

            if line[0] == '[' and line[-1] == ']':                              # pragma: no cover
                # [nr] staat in de html als nr.
                zoek = '>' + line[1:-1] + '.<'
                pos = html.find(zoek)
                if pos > 0:
                    # verwijder de tekst maar behoud de > en <
                    html = html[:pos + 1] + html[pos + len(zoek) - 1:]
                    continue

            # probeer als href
            if line.startswith('http://') or line.startswith('https://'):       # pragma: no branch
                zoek = ' href="%s"' % line
                pos = html.find(zoek)
                if pos > 0:
                    html = html[:pos] + html[pos + len(zoek):]
                    continue

            issues.append('Kan regel %s niet vinden in html e-mail' % repr(line))       # pragma: no cover
        # for

        # in html e-mail staat informatie soms in een extra kolom
        pos = html.find('<td>')
        while pos >= 0:
            pos2 = html.find('</td>')
            tekst = html[pos+4:pos2]
            html = html[:pos] + html[pos2+5:]       # verwijder deze cell

            tekst = tekst.replace('<span></span>', '')
            tekst = tekst.replace('<br>', '')
            if len(tekst) > 3:      # skip korten teksten zoals nummering
                # print('tekst: %s' % repr(tekst))
                if tekst not in email.mail_text:                                        # pragma: no cover
                    issues.append('Kan tekst %s niet vinden in text e-mail' % repr(tekst))

            pos = html.find('<td>')
        # while

        # verwijder referenties naar plaatjes
        pos = html.find('<img ')
        while pos > 0:
            pos2 = html.find('>', pos + 4)
            html = html[:pos] + html[pos2 + 1:]
            pos = html.find('<img ')
        # while

        # verwijder "href" en "target" parameters van een "a" tag
        pos = html.find('<a ')
        while pos > 0:
            pos2 = html.find('>', pos + 4)
            html = html[:pos + 2] + html[pos2:]     # behoud <a en >
            pos = html.find('<a ')
        # while

        html = html[html.find('<body>')+6:]

        # haal tag met inhoud weg
        for tag in ('th', 'h1', 'h2', 'a'):
            open_tag = '<' + tag + '>'
            sluit_tag = '</' + tag + '>'
            pos = html.find(open_tag)
            while pos > 0:
                pos2 = html.find(sluit_tag, pos + len(open_tag))
                html = html[:pos] + html[pos2 + len(sluit_tag):]
                pos = html.find(open_tag)
        # for

        html = html.replace('<br>', '')
        html = html.replace('<div>.</div>', '')     # was punt aan einde regel achter "a" tag

        for tag in ('p', 'span', 'a', 'code', 'div', 'td', 'tr', 'thead', 'table', 'body'):
            part = '<' + tag + '></' + tag + '>'
            html = html.replace(part, '')
        # for

        if html != '':                                                              # pragma: no cover
            issues.append('HTML e-mail bevat meer tekst: %s' % repr(html))
            issues.append('Volledige tekst email: %s' % repr(email.mail_text))

        if len(issues):                                                             # pragma: no cover
            issues.insert(0, '(e-mail template: %s)' % repr(template_name))
            issues.insert(0, 'E-mail bericht verschillen tussen html en tekst:')
            self.fail(msg="\n    ".join(issues))

# end of file
