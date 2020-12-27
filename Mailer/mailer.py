# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module kan een email sturen via Postmark

    Het management commando stuur_emails vind verzoeken in de database
    en roept send_mail aan om deze te versturen.
"""


from django.conf import settings
from django.utils import timezone
import requests


def send_mail_postmark(obj, stdout=None, stderr=None):

    """ Deze functie probeert een mail te versturen via PostMark.

        obj: MailQueue object
        stdout: Voor rapportage voortgang
        stderr: Voor melden van problemen
    """

    # API specs: https://postmarkapp.com/developer/api/email-api

    data = {
        'From': settings.EMAIL_FROM_ADDRESS,
        'To': obj.mail_to,
        'Subject': obj.mail_subj,
        'TextBody': obj.mail_text
    }

    headers = {
        'X-Postmark-Server-Token': settings.POSTMARK_API_KEY,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(
                        settings.POSTMARK_URL,
                        headers=headers,
                        json=data)
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
        obj.log += "[WARNING] Exceptie bij versturen: %s\n" % str(exc)
        if stderr:
            stderr.write("[ERROR] Exceptie bij versturen e-mail: %s" % str(exc))
    else:
        if resp.status_code == 200:
            # success!
            obj.log += "[INFO] Success (code 200)\n"
            obj.is_verstuurd = True
            if stdout:
                stdout.write("[INFO] Een mail verstuurd")
        else:
            obj.log += "[WARNING] Mail niet kunnen versturen\n"
            obj.log += "  response encoding:%s, status_code:%s\n" % (repr(resp.encoding), repr(resp.status_code))
            obj.log += "  full response: %s\n" % repr(resp.text)
            if stdout:
                stdout.write("[WARNING] Mail niet kunnen versturen! response encoding:%s, status_code:%s" % (repr(resp.encoding), repr(resp.status_code)))
                stdout.write("  full response: %s" % repr(resp.text))

    obj.save()


def send_mail(obj, stdout=None, stderr=None):
    """
        Deze functie doet 1 poging om een mail te versturen die in de database staat
        en werkt de velden bij: laatste_poging, aantal_pogingen, log, is_verstuurd

        Het filteren om te voorkomen dat retries snel na elkaar volgen moet buiten
        deze functie gedaan worden.

        obj: MailQueue object
        stdout, stderr: streams (van het management process) om
                        voortgang en foutmeldingen te rapporteren
                        deze kunnen in een log terecht komen
    """

    # check which service is active. Need none-empty API key
    has_postmark = hasattr(settings, 'POSTMARK_API_KEY') and settings.POSTMARK_API_KEY

    if has_postmark:

        # voorkom problemen en dubbel zenden
        if obj.is_verstuurd or obj.aantal_pogingen >= 25:
            return

        now = timezone.now()

        obj.laatste_poging = now
        obj.aantal_pogingen += 1
        obj.log += "[INFO] Nieuwe poging om %s\n" % str(now)
        obj.save()

        if has_postmark:
            send_mail_postmark(obj, stdout, stderr)

    # not configured for sending emails
    return

# end of file
