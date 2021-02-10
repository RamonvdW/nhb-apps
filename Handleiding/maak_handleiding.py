# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Maak template bestanden vanuit de wiki export """

import os
import sys
import xml.etree.ElementTree as ET
import copy_of_settings


class MaakHandleiding(object):

    def __init__(self, templates_dir, debug_pagina):
        self.templates_dir = templates_dir
        self.debug_pagina = debug_pagina
        self.namespace = ""
        self.aangemaakte_paginas = list()
        self.aangemaakte_interne_links = dict()     # [target] = [pagina1, pagina2]

    def find_namespace(self, tag):
        pos = tag.find('}')
        self.namespace = tag[:pos+1]

    def write_template(self, fname, title, text):
        out = '''{% extends 'plein/site_layout.dtl' %}
{% comment %}
                Copyright (c) 2020-2021 Ramon van der Winkel.
                All rights reserved.
                Licensed under BSD-3-Clause-Clear. See LICENSE file for details.
{% endcomment %}
{% load static %}
{% block title %}''' + title + '''{% endblock %}

{% block pagina %}
<div class="white" style="padding:10px 30px 10px 30px">
'''

        out += '<h4>' + title + '</h4>\n'

        print("[INFO] Converteer pagina %s" % fname)
        out += self.wiki_to_dtl(fname, text)

        out += '''
</div>

{% endblock %}

{% block menu %}
    {% include 'handleiding/menu.dtl' %}
{% endblock %}
'''

        file = open(os.path.join(self.templates_dir, fname + '.dtl'), 'w')
        file.write(out)
        file.close()

    def found_page(self, node):
        title = node.find(self.namespace + 'title')
        if title.text.startswith('Overleg gebruiker:'):
            return
        if title.text.startswith('Bestand:'):
            return
        if title.text == 'Nhbapps:Gebruiksvoorwaarden':
            return

        fname = title.text.replace(' ', '_')

        if self.debug_pagina and self.debug_pagina != fname:
            return

        if fname not in copy_of_settings.HANDLEIDING_PAGINAS:
            print("[WARNING] Pagina '%s' niet gevonden in settings.HANDLEIDING_PAGINAS" % fname)

        revision = node.find(self.namespace + 'revision')
        text = revision.find(self.namespace + 'text')

        self.write_template(fname, title.text, text.text)
        self.aangemaakte_paginas.append(fname)

    def run(self, export_file):
        print('[INFO] Lees %s' % export_file)
        tree = ET.parse(export_file)
        root = tree.getroot()
        self.find_namespace(root.tag)
        for page in root.findall(self.namespace + 'page'):
            self.found_page(page)
        # for

        # kijk of er pagina's verwacht worden die er nu niet zijn
        if not self.debug_pagina:
            for pagina in copy_of_settings.HANDLEIDING_PAGINAS:
                if pagina not in self.aangemaakte_paginas:
                    print("[ERROR] Pagina '%s' ontbreekt (genoemd in settings.HANDLEIDING_PAGINAS)" % pagina)
            # for

            for pagina, vanaf in self.aangemaakte_interne_links.items():
                if pagina not in self.aangemaakte_paginas:
                    print("[ERROR] Pagina '%s' ontbreekt (links staan op %s)" % (pagina, repr(vanaf)))

    def wiki_to_dtl(self, voor_pagina, text):
        # converteer wiki make-up naar django template language (.dtl)
        # alles wat gebruikt kan worden: https://www.mediawiki.org/wiki/Help:Formatting
        total_out = ""
        in_lijstje = False
        in_nummerlijstje = False
        in_italic = False
        in_bold = False
        in_code = False

        if self.debug_pagina:
            print('[DEBUG] wiki text:')
            print('---------')
            print(text)
            print('---------')

        # newline = nieuwe paragraaf
        out = ""
        for line in text.split('\n'):

            # doorgaan met een pre-formatted block
            if in_code:
                if len(line) >= 1 and line[0] == ' ':
                    out += "\n" + line
                    continue
                else:
                    out += '\n</pre>'
                    in_code = False

            if out:
                if self.debug_pagina:
                    print('[DEBUG] tdl out: %s' % out)
                total_out += out
                out = ""

            if self.debug_pagina:
                print('[DEBUG] wiki line: %s' % line)

            # vetdruk
            line = line.replace("'''''", '{%b%}{%i%}')
            line = line.replace("'''", '{%b%}')
            line = line.replace("''", '{%i%}')

            # bold
            spl = line.split('{%b%}')
            if len(spl) > 1:
                line = ""
                for part in spl[:-1]:
                    line += part
                    if in_bold:
                        line += '</b>'
                        in_bold = False
                    else:
                        line += '<b>'
                        in_bold = True
                # for
                line += spl[-1]

            # italic
            spl = line.split('{%i%}')
            if len(spl) > 1:
                line = ""
                for part in spl[:-1]:
                    line += part
                    if in_italic:
                        line += '</i>'
                        in_italic = False
                    else:
                        line += '<i>'
                        in_italic = True
                # for
                line += spl[-1]

            # print('[DEBUG] tussenresultaat: %s' % line)

            line = line.replace('{%', '<')
            line = line.replace('%}', '>')

            # interne links
            pos = line.find('[[')
            if pos >= 0:
                temp1 = line[:pos]
                line = line[pos+2:]
                pos = line.find(']]')
                link = line[:pos]
                temp3 = line[pos+2:]
                if link[:7].lower() == 'http://' or link[:8].lower() == 'https://':
                    print('[WARNING] Interne link zou externe link moeten zijn (enkele brackets): %s' % link)
                    url = link.split(' ')[0]
                    label = link[len(url)+1:]
                    temp2 = ('<a class="btn-nhb-blauw" href="' + url + '" target="_blank" rel="noopener noreferrer">'
                             + '<i class="material-icons-round left">open_in_new</i>'
                             + label + '</a>')
                elif link[:5] == 'File:':
                    # display image
                    if self.debug_pagina:
                        print('[DEBUG] Referentie naar plaatje gevonden: %s' % repr(link))
                    link = link[5:]
                    url = link.split('|')[0]
                    label = link[len(url)+1:]
                    width = None
                    if "px|" in label:
                        spl = label.split('|')
                        if len(spl) != 2 or spl[0][:-2] == 'px':
                            print('[WARNING] Expected width in %s --> got %s' % (label, repr(spl)))
                        else:
                            width = spl[0][:-2]
                            label = spl[1]

                    temp2 = '<img src="{% static ' + "'handleiding/" + url + "'" + ' %}"'

                    if width:
                        temp2 += ' width="%s"' % width
                    temp2 += ' alt="%s">' % label

                    # TODO: check dat static content beschikbaar is

                else:
                    if self.debug_pagina:
                        print('[DEBUG] Interne link gevonden: %s' % repr(link))
                    # converteer interne link naar andere handleiding pagina
                    fname = link.replace(' ', '_')
                    try:
                        self.aangemaakte_interne_links[fname].append(voor_pagina)
                    except KeyError:
                        self.aangemaakte_interne_links[fname] = [voor_pagina]
                    temp2 = '<a href="/handleiding/' + fname + '/">' + link + '</a>'

                line = temp1 + temp2 + temp3
                # continue processing

            # externe links
            pos = line.find('[')
            if pos >= 0:
                temp = line[:pos]
                line = line[pos+1:]
                pos = line.find(']')
                link = line[:pos]
                line = temp + line[pos+1:]
                if self.debug_pagina:
                    print('[DEBUG] Externe link gevonden: %s' % repr(link))
                url = link.split(' ')[0]
                label = link[len(url) + 1:]
                out += ('<a class="btn-nhb-blauw" href="' + url + '" target="_blank" rel="noopener noreferrer">'
                        + '<i class="material-icons-round left">open_in_new</i>'
                        + label + '</a>')

            # horizontal divider
            if line == "----":
                out += '<hr>'
                continue

            # headings
            if line[:2] == '==':
                for marker, heading in (('==', 'h4'), ('===', 'h5'), ('====', 'h6')):
                    mlen = len(marker)
                    if line[:mlen+1] == marker + ' ' and line[-mlen-1:] == ' ' + marker:
                        line = '<' + heading + '>' + line[mlen+1:0-mlen-1] + '</' + heading + '>'
                # for

            # lijstjes
            if line[:2] == '* ':
                if not in_lijstje:
                    out += '<ul style="padding-left: 20px">\n'
                    in_lijstje = True
                out += '<li style="list-style-type: disc; padding-left: 0px">' + line[2:] + '</li>\n'
                continue

            if line[:2] == '# ':
                if not in_nummerlijstje:
                    out += '<ol style="padding-left: 20px">\n'
                    in_nummerlijstje = True
                out += '<li>' + line[2:] + '</li>\n'
                continue

            # beëindig lijstjes
            if in_lijstje:
                out += '</ul>\n'
                in_lijstje = False

            if in_nummerlijstje:
                out += '</ol>\n'
                in_nummerlijstje = False

            if len(line) >= 1 and line[0] == ' ':
                in_code = True
                out = '<pre class="handleiding_code">' + line
                continue

            # normale regel in paragraaf stijl zetten, tenzij het een block-level element is
            if line[:2] != '<h':
                line = '<p>' + line + '</p>'

            out = out + line + '\n'
        # for

        # beëindig lijstjes
        if in_lijstje:
            out += '</ul>\n'

        if in_nummerlijstje:
            out += '</ol>\n'

        if out:
            total_out += out

        return total_out


export_file = sys.argv[1]
templates_dir = sys.argv[2]
try:
    debug_pagina = sys.argv[3]
except IndexError:
    debug_pagina = ""

MaakHandleiding(templates_dir, debug_pagina).run(export_file)


# end of file
