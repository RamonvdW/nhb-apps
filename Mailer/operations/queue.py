# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Mailer.models import MailQueue


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


# end of file
