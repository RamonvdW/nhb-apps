# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.templatetags.static import static
from Mailer.models import MailQueue
import datetime
import re


def mailer_queue_email(to_address, onderwerp, mail_body, enforce_whitelist=True):
    """ Deze functie accepteert het verzoek om een mail te versturen en slaat deze op in de database
        Het feitelijk versturen van de e-mail wordt door een achtergrondtaak gedaan

        mail_body kan een string zijn, of een tuple van (text body, html body)
    """

    if isinstance(mail_body, tuple):
        mail_text, mail_html = mail_body
    else:
        mail_text = mail_body
        mail_html = ''
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
                        mail_html=mail_html)

        # als er een whitelist is, dan moet het e-mailadres er in voorkomen
        if enforce_whitelist and len(settings.EMAIL_ADDRESS_WHITELIST) > 0:
            if to_address not in settings.EMAIL_ADDRESS_WHITELIST:
                # blokkeer het versturen
                # op deze manier kunnen we wel zien dat het bericht aangemaakt is
                obj.is_blocked = True

        obj.save()


def mailer_obfuscate_email(email):
    """ Helper functie om een email adres te maskeren
        voorbeeld: nhb.whatever@gmail.com --> nh####w@gmail.com
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


def render_email_template(context, email_template_name):
    """
        Verwerk een django email template tot een mail body.
        De inhoud van context is beschikbaar voor het renderen van de template.

        Returns: email body in text, html
    """

    context['logo_url'] = settings.SITE_URL + static('plein/logo_with_text_nhb_jubileum.png')
    context['logo_width'] = 213
    context['logo_height'] = 50

    context['basis_when'] = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    context['basis_naam_site'] = settings.NAAM_SITE

    rendered_content = render_to_string(email_template_name, context)
    pos = rendered_content.find('<!DOCTYPE')
    text_content = rendered_content[:pos]
    html_content = rendered_content[pos:]

    # control where the newlines are: pipeline character indicates start of new line
    text_content = re.sub('\s+\|', '|', text_content)          # verwijder whitespace voor elke pipeline
    text_content = text_content.replace('\n', '')
    text_content = text_content[text_content.find('|')+1:]      # strip all before first pipeline, including pipeline
    text_content = text_content.replace('|', '\n')

    return text_content, html_content

# end of file