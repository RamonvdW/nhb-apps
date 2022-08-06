# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from email.charset import Charset, QP
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from Mailer.models import MailQueue
import datetime
import email


def mailer_queue_email(to_address, onderwerp, mail_body, enforce_whitelist=True):
    """ Deze functie accepteert het verzoek om een mail te versturen en slaat deze op in de database
        Het feitelijk versturen van de email wordt door een achtergrondtaak gedaan
    """

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
                        mail_text=mail_body)

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
        - domein bevat een .
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

    cs_utf8_qp = Charset('utf-8')
    cs_utf8_qp.body_encoding = QP

    rendered_content = render_to_string(email_template_name, context)

    pos = rendered_content.find('<!DOCTYPE')

    text_content = rendered_content[:pos].strip()   # remove leading & trailing newlines

    html_content = rendered_content[pos:]

    text_msg = MIMENonMultipart('plain', 'utf-8')
    text_msg.set_payload(text_content, cs_utf8_qp)

    html_msg = MIMENonMultipart('html',  'utf-8')
    html_msg.set_payload(html_content, cs_utf8_qp)

    msg = MIMEMultipart(_subtype='alternative', encoding='utf-8')
    msg.attach(text_msg)
    msg.attach(html_msg)

    out = msg.as_string()
    # print('out:\n---\n%s\n---' % out)
    return out

# end of file
