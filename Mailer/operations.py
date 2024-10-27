# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.db.transaction import TransactionManagementError
from django.template.loader import render_to_string
from django.templatetags.static import static
from Mailer.models import MailQueue
from SiteMain.core.minify_dtl import minify_scripts, minify_css, remove_html_comments
from html import unescape
import datetime
import re


def mailer_queue_email(to_address, onderwerp, mail_body, enforce_whitelist=True):
    """ Deze functie accepteert het verzoek om een mail te versturen en slaat deze op in de database
        Het feitelijk versturen van de e-mail wordt door een achtergrondtaak gedaan

        mail_body kan een string zijn, of een tuple van (text body, html body)

        Returns: True = success
                 False = failure because of to_address
    """

    if isinstance(mail_body, tuple):
        mail_text, mail_html, template_name = mail_body
    else:
        mail_text = mail_body
        mail_html = ''
        template_name = ''
    del mail_body

    # e-mailadres is verplicht
    if to_address:
        now = timezone.now()    # in utc

        # maak de date: header voor in de mail, in lokale tijdzone
        # formaat: Tue, 01 Jan 2020 20:00:03 +0100
        mail_date = timezone.localtime(now).strftime("%a, %d %b %Y %H:%M:%S %z")

        obj = MailQueue(toegevoegd_op=now,
                        laatste_poging=now,
                        mail_to=to_address,
                        mail_subj=onderwerp,
                        mail_date=mail_date,
                        mail_text=mail_text,
                        mail_html=mail_html,
                        template_used=template_name)

        # als er een whitelist is, dan moet het e-mailadres er in voorkomen
        if enforce_whitelist and len(settings.EMAIL_ADDRESS_WHITELIST) > 0:
            if to_address not in settings.EMAIL_ADDRESS_WHITELIST:
                # blokkeer het versturen
                # op deze manier kunnen we wel zien dat het bericht aangemaakt is
                obj.is_blocked = True

        obj.save()
        return True

    return False


def mailer_obfuscate_email(email):
    """ Helper functie om een email adres te maskeren
        voorbeeld: whatever@gmail.com --> wh####w@gmail.com
    """
    try:
        user, domein = email.rsplit("@", 1)
    except ValueError:
        return email
    voor = 2
    achter = 1
    if len(user) <= 4:
        voor = 1
        achter = 1
        if len(user) <= 2:
            achter = 0
    hekjes = (len(user) - voor - achter)*'#'
    new_email = user[0:voor] + hekjes
    if achter > 0:
        new_email += user[-achter:]
    new_email = new_email + '@' + domein
    return new_email


def mailer_email_is_valide(adres):
    """ Basic check of dit een valide e-mail adres is:
        - niet leeg
        - bevat @
        - bevat geen spatie
        - domein bevat minimaal 1 punt
        Uiteindelijk weet je pas of het een valide adres is als je er een e-mail naartoe kon sturen
        We proberen lege velden en velden met opmerkingen als "geen" of "niet bekend" te ontdekken.
    """
    # full rules: https://stackoverflow.com/questions/2049502/what-characters-are-allowed-in-an-email-address
    if adres and len(adres) >= 4 and '@' in adres and ' ' not in adres:
        for char in ('\t', '\n', '\r'):
            if char in adres:
                return False
        user, domein = adres.rsplit('@', 1)
        if '.' in domein:
            return True
    return False


def mailer_notify_internal_error(tb):
    """ Deze functie stuurt een mail over een internal server error,
        maar zorgt ervoor dat er maximaal 1 mail per dag wordt gestuurd
        over hetzelfde probleem.
    """

    # kijk of hetzelfde rapport de afgelopen 24 uur al verstuurd is
    now = timezone.now()    # in utc
    recent = now - datetime.timedelta(days=1)

    try:
        count = (MailQueue
                 .objects
                 .filter(toegevoegd_op__gt=recent,
                         mail_to=settings.EMAIL_DEVELOPER_TO,
                         mail_subj=settings.EMAIL_DEVELOPER_SUBJ,
                         mail_text=tb)
                 .count())

        if count == 0:
            # nog niet gerapporteerd in de afgelopen 24 uur
            mailer_queue_email(
                    settings.EMAIL_DEVELOPER_TO,
                    settings.EMAIL_DEVELOPER_SUBJ,
                    tb,
                    enforce_whitelist=False)

    except TransactionManagementError:      # pragma: no cover
        # hier kunnen we alleen komen tijdens een autotest, welke automatisch in een atomic transaction uitgevoerd
        # wordt nadat er een database fout opgetreden is.
        # dan kunnen we geen nieuwe queries meer doen om een mail op te slaan.
        pass


def inline_styles(html):
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

    context['logo_url'] = settings.SITE_URL + static('plein/logo_with_text_khsn.png')
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

    html_content = inline_styles(html_content)
    if not settings.ENABLE_MINIFY:              # pragma: no branch
        html_content = _minify_html(html_content)

    return text_content, html_content, email_template_name


# end of file
