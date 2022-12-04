# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Mailer.operations import mailer_queue_email, render_email_template
from Overig.tijdelijke_url import maak_tijdelijke_url_functie_email
import datetime


EMAIL_TEMPLATE_ROLLEN_GEWIJZIGD = 'email_functie/rollen-gewijzigd.dtl'
EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL = 'email_functie/bevestig-toegang-email.dtl'


def maak_functie(beschrijving, rol):
    """ Deze helper geeft het Functie-object terug met de gevraagde parameters
        De eerste keer wordt deze aangemaakt.
    """
    functie, _ = Functie.objects.get_or_create(beschrijving=beschrijving, rol=rol)
    return functie      # caller kan zelf andere velden invullen


def functie_wijziging_stuur_email_notificatie(account, door_naam, functie_beschrijving, add=False, remove=False):

    """ Stuur een e-mail naar 'account' om te melden dat de rollen gewijzigd zijn

        Returns: True = success: e-mail is klaargezet
                 False = failure (typisch: geen bevestigd e-mailadres)
    """

    if add:
        actie = "Toegevoegde rol"
    elif remove:                    # pragma: no branch
        actie = 'Verwijderde rol'
    else:                           # pragma: no cover
        return False

    context = {
        'voornaam': account.get_first_name(),
        'actie': actie,
        'naam_site': settings.NAAM_SITE,
        'functie_beschrijving': functie_beschrijving,
        'contact_email': settings.EMAIL_BONDSBUREAU
    }

    if add and not account.otp_is_actief:
        context['uitleg_2fa'] = True
        context['url_handleiding_beheerders'] = settings.URL_PDF_HANDLEIDING_BEHEERDERS

    mail_body = render_email_template(context, EMAIL_TEMPLATE_ROLLEN_GEWIJZIGD)

    email = account.accountemail_set.all()[0]
    if email.email_is_bevestigd:
        if mailer_queue_email(email.bevestigde_email,                       # pragma: no branch
                              'Wijziging rollen op ' + settings.NAAM_SITE,
                              mail_body):
            # het is gelukt een mail klaar te zetten
            return True

    return False


def functie_vraag_email_bevestiging(functie):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_url_functie_email(functie)

    context = {
        'url': url,
        'naam_site': settings.NAAM_SITE,
        'contact_email': settings.EMAIL_BONDSBUREAU,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL)

    mailer_queue_email(functie.nieuwe_email,
                       'Bevestig gebruik e-mail voor rol',
                       mail_body,
                       enforce_whitelist=False)


def maak_account_vereniging_secretaris(nhb_ver, account):
    """ Geeft het account rechten om als secretaris van de vereniging de site te gebruiken
        Retourneert True als het account aan de SEC-functie toegevoegd is
    """

    # zoek de SEC-functie van de vereniging erbij
    functie = Functie.objects.get(rol='SEC', nhb_ver=nhb_ver)

    # kijk of dit lid al in de groep zit
    if functie.accounts.filter(pk=account.pk).count() == 0:
        # nog niet gekoppeld aan de functie --> koppel dit account nu

        # stuur eem e-mail, welke ook een link naar de handleiding kan bevatten
        if functie_wijziging_stuur_email_notificatie(account, 'Systeem', functie.beschrijving, add=True):
            # het is gelukt een e-mail te sturen, dus maak het koppeling definitief
            # (als het e-mailadres nog niet bevestigd is, dan blijven we het proberen)
            functie.accounts.add(account)
            return True

    return False


def account_needs_vhpg(account, show_only=False):
    """ Controleer of het Account een VHPG af moet leggen """

    if not account_needs_otp(account):
        # niet nodig
        return False, None

    if show_only:
        return True, None

    # kijk of de acceptatie recent al afgelegd is
    try:
        vhpg = VerklaringHanterenPersoonsgegevens.objects.only('acceptatie_datum').get(account=account)
    except VerklaringHanterenPersoonsgegevens.DoesNotExist:
        # niet uitgevoerd, wel nodig
        return True, None

    # elke 11 maanden moet de verklaring afgelegd worden
    # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
    opnieuw = vhpg.acceptatie_datum + datetime.timedelta(days=334)
    now = timezone.now()
    return opnieuw < now, vhpg


def account_needs_otp(account):
    """ Controleer of het Account OTP-verificatie nodig heeft

        Returns: True or False
        Bepaalde rechten vereisen OTP:
            is_BB
            is_staff
            bepaalde functies
    """
    if account.is_authenticated:                    # pragma: no branch
        if account.is_BB or account.is_staff:
            return True

        # alle functies hebben OTP nodig
        if account.functie_set.count() > 0:
            return True

    return False

# end of file
