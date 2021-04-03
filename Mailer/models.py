# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class MailQueue(models.Model):
    """ Database tabel waarin de te versturen emails staan """

    toegevoegd_op = models.DateTimeField()
    is_blocked = models.BooleanField(default=False)     # blocked door whitelist
    is_verstuurd = models.BooleanField(default=False)
    laatste_poging = models.DateTimeField()
    aantal_pogingen = models.PositiveSmallIntegerField(default=0)
    mail_to = models.CharField(max_length=150)
    mail_subj = models.CharField(max_length=100)
    mail_date = models.CharField(max_length=60)
    mail_text = models.TextField()
    log = models.TextField()

    def __str__(self):
        """ Lever een tekstuele beschrijving van een database record, voor de admin interface """
        msg = "[%s] to:%s subj:'%s'" % (self.toegevoegd_op.strftime('%Y-%m-%d %H:%M utc'),
                                        self.mail_to,
                                        self.mail_subj)
        if self.is_verstuurd:
            msg = "(verstuurd) " + msg
        return msg

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = verbose_name_plural = "Mail queue"

    objects = models.Manager()      # for the editor only


def mailer_queue_email(to_address, onderwerp, text_body, enforce_whitelist=True):
    """ Deze functie accepteert het verzoek om een mail te versturen en slaat deze op in de database
        Het feitelijk versturen van de email wordt door een achtergrondtaak gedaan
    """

    if not to_address:
        # geen e-mailadres opgegeven --> jammer dan
        return

    now = timezone.now()    # in utc

    # maak de date: header voor in de mail, in lokale tijdzone
    # formaat: Tue, 01 Jan 2020 20:00:03 +0100
    mail_date = timezone.localtime(now).strftime("%a, %d %b %Y %H:%M:%S %z")

    obj = MailQueue(toegevoegd_op=now,
                    laatste_poging=now,
                    mail_to=to_address,
                    mail_subj=onderwerp,
                    mail_date=mail_date,
                    mail_text=text_body)

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

    now = timezone.now()    # in utc
    recent = now - datetime.timedelta(days=1)

    if (MailQueue
        .objects
        .filter(toegevoegd_op__gt=recent,
                mail_to=settings.EMAIL_DEVELOPER_TO,
                mail_subj=settings.EMAIL_DEVELOPER_SUBJ,
                mail_text=tb)
        .count() == 0):

        # nog niet gerapporteerd in de afgelopen 24 uur
        mailer_queue_email(
                settings.EMAIL_DEVELOPER_TO,
                settings.EMAIL_DEVELOPER_SUBJ,
                tb,
                enforce_whitelist=False)


def mailer_opschonen(stdout):
    """ deze functie wordt typisch 1x per dag aangeroepen om de database
        tabellen van deze applicatie op te kunnen schonen.

        We verwijderen verstuurde emails van meer dan 3 maanden oud
    """

    now = timezone.now()
    max_age = now - datetime.timedelta(days=91)

    # verwijder mails die lang geleden verstuurd zijn / hadden moeten worden
    objs = (MailQueue
            .objects
            .filter(toegevoegd_op__lt=max_age))

    count = objs.count()
    if count > 0:
        stdout.write('[INFO] Verwijder %s oude emails' % count)
        objs.delete()


# end of file
