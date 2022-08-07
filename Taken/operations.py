# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.conf import settings
from Mailer.operations import mailer_queue_email, render_email_template
from Taken.models import Taak
from datetime import timedelta


SESSIONVAR_TAAK_AANTAL_OPEN = "taak_aantal_open"
SESSIONVAR_TAAK_EVAL_AFTER = "taak_eval_after"

TAAK_EVAL_INTERVAL_MINUTES = 1

EMAIL_TEMPLATE_NIEUWE_TAAK = 'email_taken/nieuwe_taak.dtl'
EMAIL_TEMPLATE_HERINNERING = 'email_taken/herinnering.dtl'


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
    else:
        if eval_after.find('.') < 0:
            # oud formaat - weggooien
            eval_after = None

    if not forceer:
        now_str = str(timezone.now().timestamp())
        if eval_after and now_str <= eval_after:
            return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    next_eval = timezone.now() + timedelta(seconds=60*TAAK_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.timestamp())
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

    if aantal_open == 1:
        aantal_str = "stond er 1 taak open"
        taken_str = "is een taak die jouw aandacht nodig heeft"
    else:
        aantal_str = "stonden er %s taken open" % aantal_open
        taken_str = "zijn taken die jouw aandacht nodig hebben"

    context = {
        'voornaam': email.account.get_first_name(),
        'site_url': settings.SITE_URL,
        'aantal_str': aantal_str,
        'taken_str': taken_str,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_HERINNERING)

    mailer_queue_email(email.bevestigde_email,
                       'Er zijn taken voor jou',
                       mail_body)


def stuur_nieuwe_taak_email(email, aantal_open):
    """ Stuur een e-mail dat er een nieuwe taak te wachten staat.
    """

    if aantal_open == 1:
        aantal_str = "stond er 1 taak open"
    else:
        aantal_str = "stonden er %s taken open" % aantal_open

    context = {
        'voornaam': email.account.get_first_name(),
        'site_url': settings.SITE_URL,
        'aantal_str': aantal_str,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_NIEUWE_TAAK)

    mailer_queue_email(email.bevestigde_email,
                       'Er is een nieuwe taak voor jou',
                       mail_body)


def check_taak_bestaat(**kwargs):
    """ Kijk of een taak al bestaat. Gebruikt dit om niet onnodig dubbele taken aan te maken.

        Kies uit de volgende argumenten om op te filteren:

            toegekend_aan = <Account>

            deadline = <DateField>

            aangemaakt_door = <Account> (of None voor 'systeem')

            beschrijving = "beschrijving van de taak - call for action of informatie"

            handleiding_pagina = Een van de settings.HANDLEIDING_xxx (of "")

            deelcompetitie = <DeelCompetitie> waar deze taak bij hoort, of None
    """
    aantal = (Taak
              .objects
              .exclude(is_afgerond=True)
              .filter(**kwargs)
              .count())
    return aantal > 0


def maak_taak(**kwargs):
    """
        Maak een nieuwe taak aan en stuur een e-mail ter herinnering

        De benodigde argumenten (kwargs) zijn:

            toegekend_aan = <Account>

            deadline = <DateField>

            aangemaakt_door = <Account> (of None voor 'systeem')

            beschrijving = "beschrijving van de taak - call for action of informatie"

            handleiding_pagina = Een van de settings.HANDLEIDING_xxx (of "")

            log = begin van het logboek, typisch "[%s] Taak aangemaakt" % now

            deelcompetitie = <DeelCompetitie> waar deze taak bij hoort, of None
    """

    taak = Taak(**kwargs)
    taak.save()

    email = taak.toegekend_aan.accountemail_set.all()[0]        # FUTURE: kan niet tegen Account zonder AccountEmail

    if not email.optout_nieuwe_taak:
        email.laatste_email_over_taken = timezone.now()
        email.save()

        aantal_open = (Taak
                       .objects
                       .exclude(is_afgerond=True)
                       .filter(toegekend_aan=taak.toegekend_aan)
                       .count())

        stuur_nieuwe_taak_email(email, aantal_open)


def herinner_aan_taken():
    """ Deze functie wordt aangeroepen vanuit de stuur_emails cli om herinneringsmails
        te maken voor openstaande taken (elke 15 min dus).
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
            if email.laatste_email_over_taken + timedelta(days=7) > now:
                # te vroeg om weer een mail te sturen
                continue

        email.laatste_email_over_taken = now
        email.save()

        stuur_taak_email_herinnering(email, aantal_open)
    # for

# end of file
