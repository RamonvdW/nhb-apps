# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Deze module kan een email sturen via MailGun """

from django.conf import settings
from django.utils import timezone
import requests


def send_mail(obj):
    """ Deze functie probeert een mail te sturen die in de database staat
        en werkt de velden bij: laatste_poging, aantal_pogingen, log, is_verstuurd

        Het filteren om te voorkomen dat retries snel na elkaar volgen moet buiten
        deze functie gedaan worden.

        obj: MailQueue object
    """

    if not settings.MAILGUN_API_KEY:
        # not configured for sending emails
        return

    # voorkom problemen en dubbel zenden
    if obj.is_verstuurd or obj.aantal_pogingen >= 25:
        return

    now = timezone.now()

    obj.laatste_poging = now
    obj.aantal_pogingen += 1
    obj.log += "Nieuwe poging om %s\n" % str(now)
    obj.save()

    # format specs: https://tools.ietf.org/html/rfc2822
    data = {
        'from': settings.EMAIL_FROM_ADDRESS,
        'to': obj.mail_to,
        'date': obj.mail_date,
        'subject': obj.mail_subj,
        'text': obj.mail_text
    }

    try:
        resp = requests.post(
                        settings.MAILGUN_URL,
                        auth=('api', settings.MAILGUN_API_KEY),
                        data=data)
    except requests.exceptions.SSLError as exc:
        # TODO: error handling
        obj.log += "Exceptie bij versturen: %s\n" % str(exc)
        sys.stderr.write("Exceptie bij versturen: %s\n" % str(exc))
    else:
        if resp.status_code == 200:
            # success!
            obj.log += "Success (code 200)\n"
            obj.is_verstuurd = True
        else:
            obj.log += "Mislukt: response encoding:%s, status_code:%s\n" % (repr(resp.encoding), repr(resp.status_code))
            obj.log += "  full response: %s\n" % repr(resp.text)
            sys.stdout.write("Mislukt: response encoding:%s, status_code:%s" % (repr(resp.encoding), repr(resp.status_code)))
            sys.stdout.write("  full response: %s\n" % repr(resp.text))

    obj.save()

# end of file
