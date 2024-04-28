# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module kan een e-mail sturen via Postmark

    Het management commando stuur_emails vind verzoeken in de database
    en roept send_mail aan om deze te versturen.
"""


from django.conf import settings
from django.utils import timezone
from Mailer.report import emailadres_is_geblokkeerd
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
        'TextBody': obj.mail_text,
    }

    if obj.mail_html != '':
        data['HtmlBody'] = obj.mail_html

    headers = {
        'X-Postmark-Server-Token': settings.POSTMARK_API_KEY,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    flag_bad = False

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
                stdout.write("[WARNING] Mail niet kunnen versturen! response encoding:%s, status_code:%s" % (
                                repr(resp.encoding), repr(resp.status_code)))
                stdout.write("  full response: %s" % repr(resp.text))

            if '"ErrorCode":406,':
                # You tried to send to recipient(s) that have been marked as inactive.
                # Found inactive addresses: x@yyy.
                # Inactive recipients are ones that have generated a hard bounce, a spam complain,
                # or a manual suppression.
                obj.log += "[WARNING] ErrorCode 406 ontdekt in reactie, dus zet is_blocked = True\n"
                obj.is_blocked = True

                flag_bad = True

    obj.save()

    if flag_bad:
        emailadres_is_geblokkeerd(obj.mail_to)


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

    # voorkom problemen en dubbel zenden
    if not obj.is_verstuurd and obj.aantal_pogingen < 25:
        now = timezone.localtime(timezone.now())

        obj.laatste_poging = now
        obj.aantal_pogingen += 1
        obj.log += "[INFO] Nieuwe poging om %s\n" % now.strftime('%Y-%m-%d %H:%M:%S')
        obj.save()

        send_mail_postmark(obj, stdout, stderr)


# end of file
