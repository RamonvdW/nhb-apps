# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.conf import settings
from Account.models import get_account
from Account.operations.session_vars import zet_sessionvar_if_changed
from Functie.rol import rol_get_huidige_functie
from Mailer.operations import mailer_queue_email, render_email_template
from Taken.models import Taak
from datetime import timedelta


SESSIONVAR_TAAK_AANTAL_OPEN = "taak_aantal_open"
SESSIONVAR_TAAK_EVAL_AFTER = "taak_eval_after"

TAAK_EVAL_INTERVAL_MINUTES = 1

EMAIL_TEMPLATE_NIEUWE_TAAK = 'email_taken/nieuwe_taak.dtl'
EMAIL_TEMPLATE_HERINNERING = 'email_taken/herinnering.dtl'


def get_taak_functie_pks(request):
    account = get_account(request)
    functie_pks = list(account.functie_set.values_list('pk', flat=True))

    # huidige rol toevoegen, zodat taken van die rol er ook bij staan
    huidige_functie_pk = None
    _, huidige_functie = rol_get_huidige_functie(request)
    if huidige_functie:
        huidige_functie_pk = huidige_functie.pk
        if huidige_functie_pk not in functie_pks:
            functie_pks.append(huidige_functie_pk)

    return functie_pks, huidige_functie_pk


def cached_aantal_open_taken(request):
    """ geef terug hoeveel taken er open stonden bij de laatste evaluatie """
    try:
        aantal_open = request.session[SESSIONVAR_TAAK_AANTAL_OPEN]
    except KeyError:
        aantal_open = 0
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
        now_str = str(timezone.now().timestamp())
        if eval_after and now_str <= eval_after:
            return

    # update het aantal open taken in de sessie
    # en zet het volgende evaluatie moment
    next_eval = timezone.now() + timedelta(seconds=60*TAAK_EVAL_INTERVAL_MINUTES)
    eval_after = str(next_eval.timestamp())
    zet_sessionvar_if_changed(request, SESSIONVAR_TAAK_EVAL_AFTER, eval_after)

    functie_pks, _ = get_taak_functie_pks(request)

    aantal_open = (Taak
                   .objects
                   .exclude(is_afgerond=True)
                   .filter(toegekend_aan_functie__pk__in=functie_pks)
                   .count())

    zet_sessionvar_if_changed(request, SESSIONVAR_TAAK_AANTAL_OPEN, aantal_open)


def stuur_email_taak_herinnering(emailadres, aantal_open):
    """ Stuur een e-mail ter herinnering dat er een taak te wachten staat.
    """

    if aantal_open == 1:
        aantal_str = "stond er 1 taak open"
        taken_str = "is een taak die jouw aandacht nodig heeft"
    else:
        aantal_str = "stonden er %s taken open" % aantal_open
        taken_str = "zijn taken die jouw aandacht nodig hebben"

    context = {
        'site_url': settings.SITE_URL,
        'aantal_str': aantal_str,
        'taken_str': taken_str,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_HERINNERING)

    mailer_queue_email(emailadres,
                       'Er zijn taken voor jou',
                       mail_body)


def stuur_email_nieuwe_taak(emailadres, onderwerp, aantal_open):

    # op het moment van sturen..
    if aantal_open == 1:
        aantal_str = "stond er 1 taak open"
    else:
        aantal_str = "stonden er %s taken open" % aantal_open

    context = {
        'site_url': settings.SITE_URL,
        'aantal_str': aantal_str,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_NIEUWE_TAAK)

    mailer_queue_email(emailadres,
                       onderwerp,
                       mail_body)


def check_taak_bestaat(skip_afgerond=True, **kwargs):
    """ Kijk of een taak al bestaat. Gebruikt dit om niet onnodig dubbele taken aan te maken.

        Kies uit de volgende argumenten om op te filteren:

            toegekend_aan_functie = <Functie>

            deadline = <DateField>

            aangemaakt_door = <Account> (of None voor 'systeem')

            onderwerp = <tekst>

            beschrijving = <tekst>
    """
    qset = Taak.objects.filter(**kwargs).order_by('-deadline')     # nieuwste eerst

    if skip_afgerond:
        qset = qset.exclude(is_afgerond=True)

    # aantal = qset.count()

    return qset.first()


def maak_taak(**kwargs):
    """
        Maak een nieuwe taak aan en stuur een e-mail ter herinnering

        De benodigde argumenten (kwargs) zijn:

            toegekend_aan_functie = <Functie>

            deadline = <DateField>

            aangemaakt_door = <Account> (of None voor 'systeem')

            onderwerp = "korte beschrijving"

            beschrijving = "beschrijving van de taak - call for action of informatie"

            log = begin van het logboek, typisch "[%s] Taak aangemaakt" % now
    """

    taak = Taak(**kwargs)
    taak.save()

    functie = taak.toegekend_aan_functie

    # TODO: opt-out is nog niet in te stellen
    if not functie.optout_nieuwe_taak:
        functie.laatste_email_over_taken = timezone.now()
        functie.save(update_fields=['laatste_email_over_taken'])

        aantal_open = (Taak
                       .objects
                       .exclude(is_afgerond=True)
                       .filter(toegekend_aan_functie=functie)
                       .count())

        stuur_email_nieuwe_taak(functie.bevestigde_email, taak.onderwerp, aantal_open)


def herinner_aan_taken():
    """ Deze functie wordt aangeroepen vanuit de stuur_mails cli van de Mailer applicatie
        om herinneringsmails te maken voor openstaande taken (elke 15 min dus).
    """

    taken_functie = dict()      # [toegekend_aan_functie] = aantal

    for taak in Taak.objects.exclude(is_afgerond=True):
        try:
            taken_functie[taak.toegekend_aan_functie] += 1
        except KeyError:
            taken_functie[taak.toegekend_aan_functie] = 1
    # for

    now = timezone.now()

    for functie, aantal_open in taken_functie.items():

        # TODO: opt-out is nog niet in te stellen
        if functie.optout_herinnering_taken:
            # wil geen herinnering ontvangen
            continue

        if functie.laatste_email_over_taken:
            if functie.laatste_email_over_taken + timedelta(days=7) > now:
                # te vroeg om weer een mail te sturen
                continue

        functie.laatste_email_over_taken = now
        functie.save(update_fields=['laatste_email_over_taken'])

        stuur_email_taak_herinnering(functie.bevestigde_email, aantal_open)
    # for

# end of file
