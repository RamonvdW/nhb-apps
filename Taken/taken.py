# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.conf import settings
from Mailer.models import mailer_queue_email
from .models import Taak
from datetime import timedelta


SESSIONVAR_TAAK_AANTAL_OPEN = "taak_aantal_open"
SESSIONVAR_TAAK_EVAL_AFTER = "taak_eval_after"

TAAK_EVAL_INTERVAL_MINUTES = 5


def aantal_open_taken(request):
    """ geef terug hoeveel taken er open stonden bij de laatste evaluatie """
    try:
        aantal_open = request.session[SESSIONVAR_TAAK_AANTAL_OPEN]
    except KeyError:
        aantal_open = None
    return aantal_open


def eval_open_taken(request, forceer=False):
    """ voer elke paar minuten een evaluatie uit van het aantal taken
        dat open staat voor deze gebruiker
    """
    try:
        eval_after = request.session[SESSIONVAR_TAAK_EVAL_AFTER]
    except KeyError:
        eval_after = None

    if not forceer:
        now_str = str(timezone.now().toordinal())
        if eval_after and now_str <= eval_after:
            return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    next_eval = timezone.now() + timedelta(seconds=60*TAAK_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.toordinal())
    request.session[SESSIONVAR_TAAK_EVAL_AFTER] = eval_after

    aantal_open = (Taak
                   .objects
                   .exclude(is_afgerond=True)
                   .filter(toegekend_aan=request.user)
                   .count())
    request.session[SESSIONVAR_TAAK_AANTAL_OPEN] = aantal_open


def stuur_taak_email_herinnering(email, aantal_open):
    """ Stuur een e-mail ter herinnering dat er een taak te wachten staat.
    """

    text_body = ("Hallo %s!\n\n" % email.account.get_first_name()
                 + "Er zijn taken die jouw aandacht nodig hebben op %s\n" % settings.SITE_URL
                 + "Op het moment van sturen stonden er %s taken open.\n\n" % aantal_open
                 + "Bedankt voor je aandacht!\n"
                 + "Het bondsburo\n")

    mailer_queue_email(email.bevestigde_email,
                       'Er zijn taken voor jou',
                       text_body)


def stuur_nieuwe_taak_email(email, aantal_open):
    """ Stuur een e-mail ter herinnering dat er een taak te wachten staat.
    """

    text_body = ("Hallo %s!\n\n" % email.account.get_first_name()
                 + "Er is zojuist een nieuwe taak voor jou aangemaakt op %s\n" % settings.SITE_URL
                 + "Op het moment van sturen stonden er %s taken open.\n\n" % aantal_open
                 + "Bedankt voor je aandacht!\n"
                 + "Het bondsburo\n")

    mailer_queue_email(email.bevestigde_email,
                       'Er is een nieuwe taak voor jou',
                       text_body)


def maak_taak(**kwargs):
    """ Maak een nieuwe taak aan en stuur een e-mail ter herinnering """
    taak = Taak(**kwargs)
    taak.save()

    email = taak.toegekend_aan.accountemail_set.all()[0]

    if not email.optout_nieuwe_taak:
        now = timezone.now()

        if email.laatste_email_over_taken:
            if email.laatste_email_over_taken + timedelta(days=1) > now:
                # te vroeg om weer een mail te sturen
                return

        email.laatste_email_over_taken = now
        email.save()

        aantal_open = (Taak
                       .objects
                       .exclude(is_afgerond=True)
                       .filter(toegekend_aan=request.user)
                       .count())

        stuur_nieuwe_taak_email(email, aantal_open)


def herinner_aan_taken():
    """ Deze functie wordt aangeroepen vanuit de stuur_emails cli om herinneringsmails
        te maken voor openstaande taken.
    """

    taken = dict()      # [toegekend_aan] = aantal

    for taak in Taak.objects.exclude(is_afgerond=True):
        try:
            taken[taak.toegekend_aan] += 1
        except KeyError:
            taken[taak.toegekend_aan] = 1
    # for

    now = timezone.now()

    for account, aantal_open in taken.items():
        email = account.accountemail_set.all()[0]

        if email.optout_herinnering_taken:
            # wil geen herinneringen ontvangen
            continue

        if email.laatste_email_over_taken:
            if email.laatste_email_over_taken + timedelta(days=1) > now:
                # te vroeg om weer een mail te sturen
                continue

        email.laatste_email_over_taken = now
        email.save()

        stuur_taak_email_herinnering(email, aantal_open)
    # for

# end of file
