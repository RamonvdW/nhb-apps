# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from Site.core.minify_dtl import minify_scripts, minify_css, remove_html_comments
from Site.core.static import static_safe
from html import unescape
import re


def _inline_styles(html):
    """ E-mail programs have the tendency to drop the <styles> section declared in the header,
        causing the layout to break. To avoid this, inlines the styles.

        <head>
            <style>
                table {
                    text-align: left;
                    border: 1px solid lightgrey;
                    border-collapse: collapse;
                    padding: 10px 0 10px 0;
                }
                th,td {
                    border: 1px solid lightgrey;
                    padding: 10px;
                }
                h1 {
                    margin: 30px 0 10px 0;
                    color: #0aa0e1;
                    font-size: large;
                }
            </style>
    """

    # convert the style definitions into a table
    pos1 = html.find('<style>')
    pos2 = html.find('</style>')
    styles = html[pos1+7:pos2]

    if not settings.ENABLE_MINIFY:          # pragma: no branch
        # late minification
        styles = minify_css(styles)

    html = html[:pos1] + html[pos2+8:]
    while len(styles) > 0:
        pos1 = styles.find('{')
        pos2 = styles.find('}')
        style = styles[pos1+1:pos2]
        tags = styles[:pos1].split(',')
        styles = styles[pos2+1:]

        for tag in tags:
            pos1 = html.find('<' + tag)
            while pos1 > 0:
                pos2 = html.find('>', pos1+1)
                html1 = html[:pos1]
                sub = html[pos1:pos2]
                html2 = html[pos2:]

                pos = sub.find(' style="')
                if pos >= 0:
                    # prepend with the extra styles
                    new_styles = list()
                    for sub_style in style.split(';'):
                        keyword, _ = sub_style.split(':')
                        if keyword not in sub:                  # pragma: no branch
                            # this one is new
                            new_styles.append(sub_style)
                    # for
                    sub = sub[:pos+8] + ";".join(new_styles) + ';' + sub[pos+8:]
                else:
                    # insert the styles
                    sub += ' style="' + style + '"'

                html = html1 + sub + html2
                pos1 = html.find('<' + tag, pos1+1)
            # while
        # for
    # while

    return html


def _minify_html(contents):

    clean = remove_html_comments(contents)

    clean = minify_scripts(clean)

    # remove /* css block comments */
    clean = re.sub(r'/\*(.*?)\*/', '', clean)

    # remove whitespace between html tags
    clean = re.sub(r'>\s+<', '><', clean)

    # remove newlines at the end
    while clean[-1] == '\n':
        clean = clean[:-1]
        
    return clean


def render_email_template(context, email_template_name):
    """
        Verwerk een django email template tot een mail body.
        De inhoud van context is beschikbaar voor het renderen van de template.

        Returns: email body in text, html + email_template_name
    """

    context['logo_url'] = settings.SITE_URL + static_safe('design/logo_with_text_khsn.png')
    # aspect ratio: 400x92 --> 217x50
    context['logo_width'] = 217
    context['logo_height'] = 50

    context['basis_when'] = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    context['basis_naam_site'] = settings.NAAM_SITE

    rendered_content = render_to_string(email_template_name, context)
    pos = rendered_content.find('<!DOCTYPE')
    text_content = rendered_content[:pos]
    html_content = rendered_content[pos:]

    if not settings.ENABLE_MINIFY:              # pragma: no branch
        text_content = remove_html_comments(text_content)

    # control where the newlines are: pipeline character indicates start of new line
    text_content = re.sub(r'\s+\|', '|', text_content)          # verwijder whitespace voor elke pipeline
    text_content = text_content.replace('\n', '')
    text_content = text_content[text_content.find('|')+1:]      # strip all before first pipeline, including pipeline
    text_content = text_content.replace('|', '\n')
    text_content = unescape(text_content)

    html_content = _inline_styles(html_content)
    if not settings.ENABLE_MINIFY:              # pragma: no branch
        html_content = _minify_html(html_content)

    return text_content, html_content, email_template_name


# end of file
