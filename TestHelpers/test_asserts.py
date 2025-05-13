# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import UnreadablePostError, HttpResponse
from django.test import TestCase
from Mailer.models import MailQueue
from TestHelpers.template_status import consistent_email_templates, included_templates, validated_templates
from TestHelpers.validate_html import validate_html
from TestHelpers.validate_js import validate_javascript
from Site.core.minify_dtl import minify_scripts, minify_html
from bs4 import BeautifulSoup
import json
import re


# debug optie: toon waar in de code de queries vandaan komen
FAIL_UNSAFE_DATABASE_MODIFICATION = False

MATERIAL_ICON_GLYPH_NAMES = 'Plein/fonts/reduce/needed-glyphs_material-icons-round.txt'

GLYPH_NAMES_PRESENT = list()
with open(MATERIAL_ICON_GLYPH_NAMES, 'r') as f:
    GLYPH_NAMES_PRESENT.extend([name.strip() for name in f.readlines()])
# with


class MyTestAsserts(TestCase):

    """ Helpers om de response pagina's te controleren op status en inhoud

        mixin class voor django.test.TestCase
    """

    @staticmethod
    def remove_debug_toolbar(html):
        """ removes the debug toolbar code """
        pos = html.find('<link rel="stylesheet" href="/static/debug_toolbar/css/print.css"')
        if pos > 0:     # pragma: no cover
            html = html[:pos] + '<!-- removed debug toolbar --></body></html>'
        return html

    @staticmethod
    def _get_template_names_used(resp: HttpResponse):
        names = list()
        if hasattr(resp, "templates"):      # pragma: no branch
            names = [template.name
                     for template in resp.templates]
            # for
        return names

    def get_useful_template_name(self, resp: HttpResponse):
        names = [name
                 for name in self._get_template_names_used(resp)
                 if (name not in included_templates
                     and not name.startswith('django/forms')
                     and not name.startswith('email_'))]
        if len(names) == 0:       # pragma: no cover
            return 'no template!'
        if len(names) > 1:        # pragma: no cover
            self.fail('Too many choices for template name: %s' % repr(names))
        return names[0]

    def interpreteer_resp(self, resp: HttpResponse):          # pragma: no cover
        long_msg = [
            "status code: %s" % resp.status_code,
            repr(resp)
        ]

        is_attachment = False
        if resp.status_code == 302 and hasattr(resp, 'url'):
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

        # convert bytestring to a normal string
        content = resp.content.decode('utf-8')

        content = self.remove_debug_toolbar(content)
        if len(content) < 50:
            msg = "very short content: %s" % content
            long_msg.append(msg)
            return msg, long_msg

        is_404 = resp.status_code == 404
        if not is_404:
            is_404 = any(['plein/fout_404.dtl' in name
                          for name in self._get_template_names_used(resp)])

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
            for name in self._get_template_names_used(resp):
                long_msg.append('   %s' % repr(name))
            # for

        soup = BeautifulSoup(content, features="html.parser")
        long_msg.append(soup.prettify())

        all_parts = long_msg[:]
        long_msg = list()
        for part in all_parts:
            # remove empty line indicators
            part = part.replace('\\n', '\n').rstrip()

            # remove single-line <!-- html comments -->
            pos = part.find('<!--')
            while pos >= 0:
                end_pos = part.find('-->', pos)
                if end_pos < 0:
                    pos = len(part)
                part = part[:pos] + part[end_pos+3:]
                pos = part.find('<!--')
            # while

            # remove empty lines
            part = re.sub(r'\n\s+\n', '\n', part)

            # remove empty lines
            part = re.sub(r'\n\n', '\n', part)

            long_msg.append(part)
        # for

        return "?? (long msg follows):\n" + "\n".join(long_msg), long_msg

    def dump_resp(self, resp):                        # pragma: no cover
        short_msg, long_msg = self.interpreteer_resp(resp)
        print("\nresp:")
        print("\n".join(long_msg))

    def extract_all_urls(self, resp: HttpResponse,
                         skip_menu=False, skip_smileys=True, skip_broodkruimels=True,
                         skip_hash_links=True, report_dupes=True, skip_external=True):
        content = str(resp.content)
        content = self.remove_debug_toolbar(content)
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
            could_be_part_url = False
            if pos1 >= 0 and (pos2 == -1 or pos2 > pos1) and (pos3 == -1 or pos3 > pos1):
                content = content[pos1+6:]       # strip all before href
            elif pos2 >= 0 and (pos1 == -1 or pos1 > pos2) and (pos3 == -1 or pos3 > pos2):
                content = content[pos2+8:]       # strip all before action
            elif pos3 >= 0:
                content = content[pos3+10:]      # strip all before data-url
                could_be_part_url = True
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
                        if not (could_be_part_url and url[0].count('/') == 0):
                            if not (skip_hash_links and url[0] == '#'):
                                if not (skip_external and url[:4] == 'http'):
                                    if report_dupes or url not in urls:     # pragma: no branch
                                        urls.append(url)
        # while
        urls.sort()     # ensure consistent order
        return urls

    def extract_checkboxes(self, resp):
        content = str(resp.content)
        content = self.remove_debug_toolbar(content)
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
    def get_error_msg_from_403_page(resp):                                         # pragma: no cover
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
                if link.find('href="') >= 0:                                                # pragma: no branch
                    # filter out website-internal links
                    if link.find('href="/') < 0 and link.find('href="#') < 0:
                        if link.find('href=""') >= 0 or link.find('href="mailto:"') >= 0:   # pragma: no cover
                            self.fail(msg='Unexpected empty link %s on page %s' % (
                                        link, template_name))
                        elif link.find('href="mailto:') < 0 and link.find('javascript:history.go(-1)') < 0:
                            # remainder must be links that leave the website
                            # these must target a blank window
                            if not is_email and 'target="_blank"' not in link:              # pragma: no cover
                                self.fail(msg='Missing target="_blank" in link %s on page %s' % (
                                            link, template_name))
                            if not is_email and 'rel="noopener noreferrer"' not in link:    # pragma: no cover
                                self.fail(msg='Missing rel="noopener noreferrer" in link %s on page %s' % (
                                            link, template_name))
            else:
                content = ''
        # while

    def assert_scripts_clean(self, html, template_name):
        pos = html.find('<script')
        while pos >= 0:
            html = html[pos:]
            pos = html.find('</script>')
            script = html[:pos+9]

            if 'type="application/json"' not in script:
                if settings.TEST_VALIDATE_JAVASCRIPT:   # pragma: no cover
                    issues = validate_javascript(script)
                    if len(issues):
                        msg = 'Invalid script (template: %s):\n' % template_name
                        for issue in issues:
                            msg += "    %s\n" % issue
                        # for
                        self.fail(msg=msg)

                    if not settings.ENABLE_MINIFY:          # pragma: no branch
                        # not already minified by dtl loader, so do now to remove comments
                        script = minify_scripts(script)

                    pos = script.find('console.log')
                    if pos >= 0:                    # pragma: no cover
                        self.fail(msg='Detected console.log usage in script from template %s' % template_name)

            pos = script.find('/*')
            if pos >= 0:                    # pragma: no cover
                self.fail(msg='Found block comment in script from template %s' % template_name)

            # tel het aantal newlines in het script
            if script.count('\n') >= 3:     # pragma: no cover
                self.fail(msg='Missing semi-colons in script in template %s' % template_name)

            html = html[pos+9:]
            pos = html.find('<script ')
        # while

    def assert_event_handlers_clean(self, html, template_name):
        """ check all javascript embedded in event handlers
            example: onsubmit="document.getElementById('submit_knop').disabled=true; return true;"
        """

        if not settings.TEST_VALIDATE_JAVASCRIPT:  # pragma: no cover
            return

        # search for all possible event handlers, not just a few known ones
        pos = html.find('on')
        while pos >= 0:
            if pos > 0 and html[pos-1].isalnum():
                # "on" is part of a word, so skip
                html = html[pos:]
            else:
                html = html[pos:]
                pos = html.find('="')
                if 3 <= pos <= 14:      # oncontextmenu="
                    event_name = html[:pos]
                    if ' ' not in event_name and '<' not in event_name and ':' not in event_name:
                        # print('event: %s' % repr(event_name))

                        # extract the javascript
                        html = html[pos+2:]
                        pos = html.find('"')
                        script = html[:pos]
                        html = html[pos:]
                        # print('script: %s' % repr(script))

                        # wrap the snippet in a reasonable script
                        script = "<script>function %s() { %s }</script>" % (event_name, script)

                        issues = validate_javascript(script)
                        if len(issues):         # pragma: no cover
                            msg = 'Invalid script (template: %s):\n' % template_name
                            for issue in issues:
                                msg += "    %s\n" % issue
                            # for
                            self.fail(msg=msg)

            pos = html.find('on', 1)
        # while

    _BLOCK_LEVEL_ELEMENTS = (
        'address', 'article', 'aside', 'canvas', 'figcaption', 'figure', 'footer',
        'blockquote', 'dd', 'div', 'dl', 'dt', 'fieldset',
        'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li',
        'main', 'nav', 'noscript', 'ol', 'p', 'pre', 'pre', 'section', 'table', 'tfoot', 'ul', 'video'
    )

    def html_assert_no_div_in_p(self, html, dtl):
        pos1 = html.find('<p ')
        pos2 = html.find('<p>')
        pos = min(pos1, pos2)
        if pos < 0:
            pos = max(pos1, pos2)

        while pos >= 0:
            html = html[pos+2:]
            pos = html.find('</p>')
            sub = html[:pos]
            # see https://stackoverflow.com/questions/21084870/no-p-element-in-scope-but-a-p-end-tag-seen-w3c-validation
            for elem in self._BLOCK_LEVEL_ELEMENTS:
                elem_pos = sub.find('<' + elem + ' ')   # prevent false-positive "<p class=" matching on "<path d="
                if elem_pos < 0:
                    elem_pos = sub.find('<' + elem + '>')
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

            pos1 = html.find('<p ')
            pos2 = html.find('<p>')
            pos = min(pos1, pos2)
            if pos < 0:
                pos = max(pos1, pos2)
        # while

    def html_assert_no_col_white(self, text, dtl):
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
                    msg = 'Found grid col s10 + white (too much unused space on small)'
                    msg += ' --> use separate div.white + padding:10px) in %s' % dtl
                    self.fail(msg)

            pos = text.find("class=")
        # while

    def html_assert_inputs(self, html, dtl):
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
                    if tag not in ('value', 'autofocus') and part_spl[1] in ('""', "''"):       # pragma: no cover
                        msg = 'Found input tag %s with empty value: %s in %s' % (repr(tag), repr(inp), repr(dtl))
                        self.fail(msg)
            # for
        # while

    def html_assert_basics(self, html, dtl):
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

    def html_assert_template_bug(self, html, dtl):
        pos = html.find('##BUG')
        if pos >= 0:                        # pragma: no cover
            msg = html[pos:]
            end_pos = msg.find('##', 3)     # find terminating ##
            msg = msg[:end_pos+2]
            context = html[pos-80:pos+80]
            self.fail(msg='Bug in template %s: %s\nContext: %s' % (repr(dtl), msg, context))

    def html_assert_form_csrf(self, html, dtl):
        """ controleer het type formulier en controleer juist gebruik van het csrf token """
        pos_method = html.find('method=')
        method = html[pos_method+7:pos_method+7+10]
        is_post = "POST" in method.upper()

        pos_csrf = html.find('csrfmiddlewaretoken')
        if is_post:
            if pos_csrf < 0:        # pragma: no cover
                self.fail(msg='Bug in template %s: missing csrf token inside form with method=post' % repr(dtl))
        else:
            if pos_csrf >= 0:       # pragma: no cover
                self.fail(msg='Bug in template %s: found csrf token inside form not using method=post' % repr(dtl))

    def html_assert_no_csrf(self, html, dtl):
        """ controleer geen oneigenlijk gebruik van het csrf_token """
        pos_csrf = html.find('csrfmiddlewaretoken')
        if pos_csrf >= 0:           # pragma: no cover
            self.fail('Bug in template %s: found csrf token usage outside form' % repr(dtl))

    def html_assert_no_csrf_except_in_script(self, html, dtl):
        # skip usage inside scripts
        pos_script = html.find('<script')
        while pos_script >= 0:
            self.html_assert_no_csrf(html[:pos_script], dtl)
            html = html[pos_script:]
            pos_script = html.find('</script')
            html = html[pos_script+8:]
        # while
        self.html_assert_no_csrf(html, dtl)

    def html_assert_csrf_token_usage(self, html, dtl):
        """ controleer het gebruik van csrf token """
        pos_form = html.find('<form')
        while pos_form >= 0:
            # controleer het hele formulier
            self.html_assert_no_csrf_except_in_script(html[:pos_form], dtl)
            html = html[pos_form:]

            form_end = html.find('</form>')
            self.html_assert_form_csrf(html[:form_end], dtl)

            html = html[form_end+7:]
            pos_form = html.find('<form')
        # while

        self.html_assert_no_csrf_except_in_script(html, dtl)

    def html_assert_dubbelklik_bescherming(self, html, dtl):
        """ controleer het gebruik onsubmit in forms

            <form action="{{ url_opslaan }}" method="post"
                  onsubmit="document.getElementById('submit_knop').disabled=true; return true;">

            <button class="btn-sv-rood" id="submit_knop" type="submit">
        """
        pos_form = html.find('<form')
        while pos_form >= 0:
            # controleer het hele formulier
            html = html[pos_form:]
            form_end = html.find('</form>')

            form = html[:form_end]

            # sommige forms zijn containers en worden met javascript afgehandeld
            # deze hebben geen action url
            if "action=" in form:
                # varianten:
                #  onsubmit="document.getElementById('submit_knop').disabled=true; return true;"
                #  onsubmit="document.getElementById('submit_knop1').disabled=true; return true;"
                #  onsubmit="submit_knop1.disabled=true; submit_knop2.disabled=true; return true;"
                #  onsubmit="document.getElementById('submit_knop').disabled=true; return true;"
                pos1 = form.find(' onsubmit="')
                if pos1 >= 0:
                    pos2 = form.find('"', pos1+11)
                    submit = form[pos1+11:pos2]
                    if '.disabled=true;' not in submit or 'return true;' not in submit:             # pragma: no cover
                        self.fail(
                            'Form onsubmit zonder met dubbelklik bescherming in template %s\n%s' % (repr(dtl),
                                                                                                    repr(submit)))

                    if 'document.getElementById(' not in submit:                                    # pragma: no cover
                        self.fail(
                            'Form onsubmit met slechte dubbelklik bescherming in template %s\n%s' % (repr(dtl),
                                                                                                     repr(submit)))

                pos_button = form.find('<button')
                button_count = 0
                pos1 = pos2 = -1
                while pos_button >= 0:
                    form = form[pos_button:]
                    button_end = form.find('</button>')
                    button = form[:button_end]
                    button_count += 1

                    pos1 = button.find(' id="submit_knop')
                    pos2 = button.find(' type="submit"')
                    if pos1 > 0 and pos2 > 0:
                        break   # from the while

                    form = form[button_end + 9:]
                    pos_button = form.find('<button')
                # while

                if button_count > 0:
                    if pos1 < 0 or pos2 < 0:                # pragma: no cover
                        msg = 'Form without dubbelklik bescherming in button template %s\n' % repr(dtl)
                        msg += 'button_count=%s, pos1=%s, pos2=%s' % (button_count, pos1, pos2)
                        self.fail(msg)

            html = html[form_end+7:]
            pos_form = html.find('<form')
        # while

    def html_assert_notranslate(self, html, dtl):
        """ control gebruik notranslate class, bijvoorbeeld bij material-icons
        """
        pos_class = html.find(' class="')
        while pos_class > 0:
            pos_end = html.find('"', pos_class+8)
            if pos_end < 0:     # pragma: no cover
                pos_end = len(html)
            class_str = html[pos_class+1:pos_end+1]

            if 'notranslate' not in class_str:
                if 'material-icons' in class_str:       # pragma: no cover
                    self.fail('Bug in template %s: missing "notranslate" in %s' % (repr(dtl), class_str))

            pos_class = html.find(' class="', pos_end)
        # while

    def html_assert_button_vs_hyperlink(self, html, dtl, skip_menu=True, skip_broodkruimels=True):
        """ controleer gebruik van <a> waar <button> gebruik moet worden.
        """
        html = self.remove_debug_toolbar(html)

        if skip_menu:                                                           # pragma: no branch
            # menu is the in the navbar at the top of the page
            # it ends with the nav-content-scrollbar div
            pos = html.find('<div class="nav-content-scrollbar">')
            if pos >= 0:                                                        # pragma: no branch
                html = html[pos:]

        if skip_broodkruimels:                                                  # pragma: no branch
            pos_kruimel = html.find('broodkruimels-link')
            while pos_kruimel > 0:
                html = html[pos_kruimel+18:]
                pos_kruimel = html.find('broodkruimels-link')
            # while

        pos_a = html.find('<a')
        while pos_a > 0:
            pos_end = html.find('</a>', pos_a+2)
            link = html[pos_a:pos_end+4]

            if link.find(' href="') < 0:                                        # pragma: no cover
                # geen href
                # print('link: %s' % repr(link))
                msg = "Link should <button> in %s:\n%s" % (dtl, link)
                self.fail(msg)

            pos_a = html.find('<a', pos_end+4)
        # while

    def html_assert_material_icons(self, html, dtl):
        pos = html.find('<i class=')
        while pos > 0:
            pos2 = html.find('</i>', pos+1)
            if pos2 > 0:                                                        # pragma: no branch
                tag_i = html[pos:pos2]
                if 'material-icons' in tag_i:
                    # class secondary-content is used to dynamically plug an icon from within a script
                    if 'secondary-content' not in tag_i:
                        pos2 = tag_i.rfind('>')
                        icon_name = tag_i[pos2+1:]
                        # print('icon_name: %s' % repr(icon_name))
                        if icon_name not in GLYPH_NAMES_PRESENT:                # pragma: no cover
                            self.fail('Bug in template %s: Material Icon name %s is not in the reduced font!' % (
                                        repr(dtl), repr(icon_name)))

            pos = html.find('<i class=', pos+1)
        # while

    def html_assert_no_kort_break(self, html, dtl):
        # strip all script sections because || is a valid javascript operator
        clean_html = ''
        pos = html.find('<script')
        while pos >= 0:
            clean_html += html[:pos]
            pos2 = html.find('</script>', pos)
            html = html[pos2+9:]
            pos = html.find('<script')
        # while
        self.assertNotIn('||', html, msg='Mogelijk vergeten om regel.korte_beschrijving op te splitsen in %s' % dtl)

    def assert_html_ok(self, resp: HttpResponse):
        """ Doe een aantal basic checks op een html response """

        # check for files
        # 'Content-Disposition': 'attachment; filename="bond_alle.csv"'
        check = resp.get('Content-Disposition', '')
        if 'ATTACHMENT;' in str(check).upper():     # pragma: no cover
            self.fail('Found attachment instead of html page')

        html = resp.content.decode('utf-8')
        html = self.remove_debug_toolbar(html)

        if not settings.ENABLE_MINIFY:          # pragma: no branch
            # not already minified by dtl loader, so do now to remove comments
            html = minify_html(html)

        dtl = self.get_useful_template_name(resp)
        # print('useful template name:', dtl)
        if dtl not in validated_templates:
            validated_templates.append(dtl)

        self.html_assert_basics(html, dtl)

        # self.assertNotIn('<script>', html, msg='Missing type="application/javascript" in <script> in %s' % dtl)

        self.assert_link_quality(html, dtl)
        self.assert_scripts_clean(html, dtl)
        self.assert_event_handlers_clean(html, dtl)
        self.html_assert_no_div_in_p(html, dtl)
        self.html_assert_no_col_white(html, dtl)
        self.html_assert_button_vs_hyperlink(html, dtl)
        self.html_assert_inputs(html, dtl)
        self.html_assert_csrf_token_usage(html, dtl)
        self.html_assert_dubbelklik_bescherming(html, dtl)
        self.html_assert_notranslate(html, dtl)
        self.html_assert_template_bug(html, dtl)
        self.html_assert_material_icons(html, dtl)
        self.html_assert_no_kort_break(html, dtl)

        urls = self.extract_all_urls(resp)
        for url in urls:
            if url.find(" ") >= 0:                  # pragma: no cover
                self.fail(msg="Unexpected space in url %s on page %s" % (repr(url), dtl))
        # for

        if settings.TEST_VALIDATE_HTML:             # pragma: no cover
            issues = validate_html(html)
            if len(issues):
                msg = 'Invalid HTML (template: %s):\n' % dtl
                for issue in issues:
                    msg += "    %s\n" % issue
                # for
                self.fail(msg=msg)

        return html

    def is_fout_pagina(self, resp: HttpResponse):        # pragma: no cover
        is_fout = False
        if resp.status_code == 200:
            names = self._get_template_names_used(resp)
            is_fout = 'plein/fout_403.dtl' in names or 'plein/fout_404.dtl' in names
        return is_fout

    def get_templates_not_used(self, resp: HttpResponse, template_names: tuple | list) -> list:
        """ returns the names of templates not used in the render of the response """
        used_names = self._get_template_names_used(resp)
        # Note: used_names contains additional template names that we don't want to return (like site_layout_fonts.dtl)
        return [name
                for name in template_names
                if name not in used_names]

    def assert_template_used(self, resp: HttpResponse, template_names: tuple | list):
        """ Controleer dat de gevraagde templates gebruikt zijn """
        lst = self.get_templates_not_used(resp, template_names)
        if len(lst):    # pragma: no cover
            short_msg, long_msg = self.interpreteer_resp(resp)
            if short_msg:
                msg = short_msg + " in plaats van de juiste templates"
            else:
                print("\n".join(long_msg))
                msg = "Following templates should have been used: %s\n" % repr(lst)
                msg += "Actually used: %s" % repr(self._get_template_names_used(resp))
                msg += "\n" + short_msg
            self.fail(msg=msg)

    def assert_is_redirect(self, resp, expected_url):
        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')            # pragma: no cover

        if resp.status_code != 302:                     # pragma: no cover
            # geef een iets uitgebreider antwoord
            if resp.status_code == 200:
                short_msg, _ = self.interpreteer_resp(resp)
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
                self.dump_resp(resp)
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)

        self.assertNotEqual(resp.url, '/plein/')    # redirect naar plein is typisch een reject om rechten

    def assert_is_redirect_login(self, resp, next_url=None):
        if resp.status_code != 302:                     # pragma: no cover
            # geef een iets uitgebreider antwoord
            msg = "status_code: %s != 302" % resp.status_code
            if resp.status_code == 200:
                self.dump_resp(resp)
                msg += "; templates used: %s" % repr([tmpl.name for tmpl in resp.templates])
            self.fail(msg=msg)

        self.assertTrue(resp.url.startswith, '/account/login/')
        if next_url:
            next_param = '?next=%s' % next_url
            if next_param not in resp.url:              # pragma: no cover
                msg = 'next url %s ontbreekt in %s' % (repr(next_url), repr(resp.url))
                self.fail(msg=msg)

    def check_concurrency_risks(self, tracer):
        found_delete = False
        found_insert = False
        found_update = False

        for call in tracer.trace:
            sql = call['sql']

            if sql.startswith('INSERT INTO '):
                found_insert = True

            elif sql.startswith('UPDATE '):
                found_update = True

            elif sql.startswith('DELETE FROM '):
                found_delete = True
        # for

        do_report = False
        if found_delete or found_insert or found_update:        # pragma: no branch
            if not tracer.modify_acceptable:                    # pragma: no cover
                do_report = True

        if do_report:           # pragma: no cover
            explain = list()
            explain.append('concurrency check (modify_acceptable: %s):' % tracer.modify_acceptable)
            explain.append('from: ' + tracer.found_code)

            renames = dict()        # [original_term] = new_term
            savepoint_nr = 0

            for call in tracer.trace:
                sql = call['sql']
                table_name = ''

                if sql.startswith('SELECT '):
                    pos1 = sql.find(' FROM "') + 5
                    pos2 = sql.find('"', pos1 + 2)
                    table_name = sql[pos1 + 2:pos2]
                    cmd = "SELECT"
                    if " FOR UPDATE" in sql:
                        cmd += '.. FOR UPDATE'

                elif sql.startswith('INSERT INTO '):
                    cmd = 'INSERT INTO'
                    pos1 = sql.find(' "')
                    pos2 = sql.find('"', pos1 + 2)
                    table_name = sql[pos1 + 2:pos2]

                elif sql.startswith('UPDATE '):
                    cmd = 'UPDATE'
                    pos1 = sql.find(' "')
                    pos2 = sql.find('"', pos1 + 2)
                    table_name = sql[pos1 + 2:pos2]

                elif sql.startswith('DELETE FROM '):
                    cmd = 'DELETE FROM'
                    pos1 = sql.find(' "')
                    pos2 = sql.find('"', pos1 + 2)
                    table_name = sql[pos1 + 2:pos2]

                elif sql.startswith('SAVEPOINT'):
                    try:
                        cmd = renames[sql]
                    except KeyError:
                        savepoint_nr += 1
                        cmd = renames[sql] = '#' + str(savepoint_nr)
                    cmd += ' savepoint'

                elif sql.startswith('RELEASE SAVEPOINT'):
                    cmd = renames[sql[8:]] + ' release'

                else:
                    cmd = '?? unknown sql: %s' % repr(sql)

                explain.append(cmd + ' ' + table_name)
            # for

            if FAIL_UNSAFE_DATABASE_MODIFICATION:
                self.fail(msg='Found database modification outside POST or background task:' +
                              '\n   ' +
                              '\n   '.join(explain))
            else:
                print('\n[WARNING] Found database modification outside POST or background task:' +
                      '\n   ' +
                      '\n   '.join(explain))

    def assert403(self, resp: HttpResponse, expected_msg='Geen toegang'):
        # controleer dat we op de speciale code-403 handler pagina gekomen zijn
        # of een redirect hebben gekregen naar de login pagina

        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')            # pragma: no cover

        if resp.status_code == 302 and hasattr(resp, 'url'):
            if resp.url != '/account/login/':                                       # pragma: no cover
                self.dump_resp(resp)
                self.fail(msg="Onverwachte redirect naar %s" % resp.url)
        else:
            if resp.status_code != 200:     # pragma: no cover
                self.dump_resp(resp)
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

    def assert404(self, resp: HttpResponse, expected_msg=''):
        if isinstance(resp, str):
            self.fail(msg='Verkeerde aanroep: resp parameter vergeten?')            # pragma: no cover

        # controleer dat we op de speciale code-404 handler pagina gekomen zijn
        if resp.status_code != 200:                                                 # pragma: no cover
            self.dump_resp(resp)
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

    def assert405(self, resp: HttpResponse):
        self.assertEqual(resp.status_code, 405)

    def assert_bestand(self, resp: HttpResponse, expected_content_type):
        if resp.status_code != 200:                                 # pragma: no cover
            self.dump_resp(resp)
            self.fail(msg="Onverwachte foutcode %s in plaats van 200" % resp.status_code)

        # check the headers that make this a download
        # print("response: ", repr([(a,b) for a,b in resp.items()]))
        content_type_header = resp['Content-Type']
        self.assertEqual(expected_content_type, content_type_header)
        content_disposition_header = resp['Content-Disposition']
        self.assertTrue(content_disposition_header.startswith('attachment; filename='))

        # ensure the file is not empty
        self.assertTrue(len(str(resp.content)) > 30)

    def assert200_json(self, resp: HttpResponse):
        if resp.status_code != 200:                                 # pragma: no cover
            self.dump_resp(resp)
            self.fail(msg="Onverwachte foutcode %s in plaats van 200" % resp.status_code)

        # print("response: ", repr([(a,b) for a,b in resp.items()]))
        content_type_header = resp['Content-Type']
        self.assertEqual(content_type_header, 'application/json')

        try:
            json_data = json.loads(resp.content)
        except (json.decoder.JSONDecodeError, UnreadablePostError) as exc:      # pragma: no cover
            # json_data = None
            self.fail('No valid JSON response (%s)' % str(exc))

        return json_data

    def assert200_is_bestand_csv(self, resp: HttpResponse):
        self.assert_bestand(resp, 'text/csv; charset=UTF-8')

    def assert200_is_bestand_tsv(self, resp: HttpResponse):
        self.assert_bestand(resp, 'text/tab-separated-values; charset=UTF-8')

    def assert200_is_bestand_xlsx(self, resp: HttpResponse):
        self.assert_bestand(resp, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # def assert200_is_bestand_xlsm(self, resp):
    #     self._assert_bestand(resp, 'application/vnd.ms-excel.sheet.macroEnabled.12')

    def assert_email_html_ok(self, mail: MailQueue, expected_template_name: str):
        html = mail.mail_html
        template_name = mail.template_used

        self.assertEqual(template_name, expected_template_name)

        if template_name not in validated_templates:          # pragma: no branch
            validated_templates.append(template_name)

        self.html_assert_basics(html, template_name)
        self.html_assert_template_bug(html, template_name)

        self.assertNotIn('<script>', html, msg='Unexpected script in e-mail HTML (template: %s)' % template_name)
        self.assert_link_quality(html, template_name, is_email=True)
        self.html_assert_no_div_in_p(html, template_name)

        if settings.TEST_VALIDATE_HTML:             # pragma: no cover
            issues = validate_html(html)
            if len(issues):
                msg = 'Invalid HTML (template: %s):\n' % template_name
                for issue in issues:
                    msg += "    %s\n" % issue
                # for
                self.fail(msg=msg)

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

        # verwijder opmaak uit de HTML die niet voorkomt in de plaintext versie
        html = html.replace('</code>', '')
        html = html.replace('<code>', '')

        # verwijder alle <a href="mailto:.."> en behoud alleen het e-mailadres
        pos = html.find('<a href="mailto:')
        while pos > 0:
            pos2 = html.find('"><code>', pos)
            if pos2 > 0:                                        # pragma: no cover
                pos3 = html.find('</code></a>', pos2)
                html = html[:pos3] + html[pos3+11:]
                html = html[:pos] + html[pos2+8:]
            else:
                # try without <code>
                pos2 = html.find('">', pos)
                pos3 = html.find('</a>', pos2)
                html = html[:pos3] + html[pos3+4:]
                html = html[:pos] + html[pos2+2:]

            # nog een?
            pos = html.find('<a href="mailto:')
        # while

        # check distance between euro signs
        if True:
            pos = 0
            prev_pos = 0
            while 0 <= pos < len(html):
                pos = html.find('€', pos+1)
                if pos > prev_pos and pos - prev_pos <= 5:      # pragma: no cover
                    issues.append('Euro signs close to each other in html: ' + html[prev_pos-10:pos+10])
                prev_pos = pos
            # while

            text = email.mail_text
            pos = 0
            prev_pos = 0
            while 0 <= pos < len(text):
                pos = text.find('€', pos+1)
                if pos > prev_pos and pos - prev_pos <= 5:      # pragma: no cover
                    issues.append('Euro signs close to each other in text: ' +
                                  text[prev_pos-10:pos+10].replace('\n', '\\n'))
                prev_pos = pos
            # while

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

                if zoek1 in ignore:             # pragma: no branch
                    continue

                # print('check zoek1=%s, zoek2=%s' % (repr(zoek1), repr(zoek2)))

                pos = html.find(zoek1)
                if pos > 0:
                    # verwijder de tekst maar behoud de >
                    html = html[:pos+1] + html[pos + len(zoek1):]
                else:
                    # misschien is het een table header zonder dubbele punt
                    zoek1b = zoek1[:-1]     # verwijder :
                    zoek_th = '<th' + zoek1b + '</th>'
                    # print('zoek_th=%s' % repr(zoek_th))
                    pos = html.find(zoek_th)
                    if pos > 0:                                                 # pragma: no branch
                        # verwijder de header en de tag
                        html = html[:pos] + html[pos + len(zoek_th):]
                        th_matched.append(zoek_th)
                    elif zoek_th not in th_matched:                              # pragma: no cover
                        zoek_td = '<td' + zoek1b + '</td>'
                        pos = html.find(zoek_td)
                        if pos > 0:  # pragma: no branch
                            # verwijder de header en de tag
                            html = html[:pos] + html[pos + len(zoek_td):]
                            th_matched.append(zoek_td)
                        elif zoek_td not in th_matched:                         # pragma: no cover
                            issues.append('{zoek1} Kan tekst %s niet vinden in html e-mail' % repr(zoek1))

                if zoek2 in ignore:     # pragma: no cover
                    continue

                pos = html.find(zoek2)
                if pos > 0:                                                     # pragma: no branch
                    # verwijder de tekst maar behoud de <
                    html = html[:pos] + html[pos + len(zoek2) - 1:]
                else:                                                           # pragma: no cover
                    issues.append('{zoek2} Kan tekst %s niet vinden in html e-mail' % repr(zoek2))

                continue        # pragma: no cover

            if line[-1] == ':':
                # probeer zonder de dubbele punt
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
                if pos > 0:                                                     # pragma: no branch
                    html = html[:pos] + html[pos + len(zoek):]
                    continue

            if line in ignore:                                                  # pragma: no cover
                continue

            issues.append('Kan regel %s niet vinden in html e-mail' % repr(line))       # pragma: no cover
        # for

        # in html e-mail staat informatie soms in een extra kolom
        pos = html.find('<td>')
        while pos >= 0:
            pos2 = html.find('</td>')
            tekst = html[pos+4:pos2]
            html = html[:pos] + html[pos2+5:]       # verwijder deze cell

            tekst = tekst.replace('<br>', '')
            tekst = tekst.replace('<span></span>', '')
            tekst = tekst.replace('</span>', '')
            tekst = tekst.replace('<span>', '')
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

                # capture extra space left behind in situation "Email: <a"
                if pos > 0 and html[pos-1] == ' ':              # pragma: no cover
                    pos -= 1
                html = html[:pos] + html[pos2 + len(sluit_tag):]
                pos = html.find(open_tag)
        # for

        html = html.replace('<br>', '')
        html = html.replace('<div>.</div>', '')     # was punt aan einde regel achter "a" tag

        for tag in ('span', 'a', 'code', 'p', 'div', 'td', 'tr', 'thead', 'table', 'body'):
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
