# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Account.models import get_account, Account
from Functie.definities import Rol
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Functie.rol import rol_get_huidige_functie
from Geo.models import Regio
from Mailer.operations import mailer_queue_email, render_email_template
from Sporter.models import get_sporter
from TijdelijkeCodes.operations import maak_tijdelijke_code_bevestig_email_functie
from Vereniging.models import Vereniging
import datetime

EMAIL_TEMPLATE_ROLLEN_GEWIJZIGD = 'email_functie/rollen-gewijzigd.dtl'
EMAIL_TEMPLATE_BEVESTIG_TOEGANG_EMAIL = 'email_functie/bevestig-toegang-email.dtl'


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

    if account.email_is_bevestigd:
        if mailer_queue_email(account.bevestigde_email,                       # pragma: no branch
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
    url = maak_tijdelijke_code_bevestig_email_functie(functie)

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


def koppel_account_aan_functie_sec(ver: Vereniging, account: Account):
    """ Geeft het account rechten om als secretaris van de vereniging de site te gebruiken
        Retourneert True als het account aan de SEC-functie toegevoegd is
    """

    # zoek de SEC-functie van de vereniging erbij
    functie = Functie.objects.get(rol='SEC', vereniging=ver)

    # kijk of dit lid al in de groep zit
    if functie.accounts.filter(pk=account.pk).count() == 0:
        # nog niet gekoppeld aan de functie --> koppel dit account nu

        # stuur eem e-mail, welke ook een link naar de handleiding kan bevatten
        if functie_wijziging_stuur_email_notificatie(account, 'Systeem', functie.beschrijving, add=True):
            # het is gelukt een e-mail te sturen, dus maak de koppeling definitief
            # (als het e-mailadres nog niet bevestigd is, dan blijven we het proberen)
            functie.accounts.add(account)
            return True

    return False


def account_needs_vhpg(account: Account, show_only=False):
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


def account_needs_otp(account: Account):
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


def get_request_regio_nr(request, allow_admin_regio=True):
    """ Geeft het regionummer van de ingelogde sporter terug,
        of 101 als er geen regio vastgesteld kan worden

        Als de gebruiker een rol gekozen heeft, neem dat het regionummer wat bij die rol past
    """
    regio_nr = 101

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.vereniging:
            # HWL, WL
            regio_nr = functie_nu.vereniging.regio.regio_nr
        elif functie_nu.regio:
            # RCL
            regio_nr = functie_nu.regio.regio_nr
        elif functie_nu.rayon:
            # RKO
            regio = (Regio
                     .objects
                     .filter(rayon=functie_nu.rayon,
                             is_administratief=False)
                     .order_by('regio_nr'))[0]
            regio_nr = regio.regio_nr

    elif rol_nu == Rol.ROL_SPORTER:
        # sporter
        account = get_account(request)
        sporter = get_sporter(account)
        if sporter and sporter.is_actief_lid and sporter.bij_vereniging:
            regio_nr = sporter.bij_vereniging.regio.regio_nr

    if regio_nr == 100 and not allow_admin_regio:
        regio_nr = 101

    return regio_nr


def get_request_rayon_nr(request):
    """ Geeft het rayon nummer van de ingelogde gebruiker/beheerder terug,
        of 1 als er geen rayon vastgesteld kan worden
    """
    rayon_nr = 1

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if functie_nu:
        if functie_nu.vereniging:
            # HWL, WL
            rayon_nr = functie_nu.vereniging.regio.rayon_nr
        elif functie_nu.regio:
            # RCL
            rayon_nr = functie_nu.regio.rayon_nr
        elif functie_nu.rayon:
            # RKO
            rayon_nr = functie_nu.rayon.rayon_nr

    elif rol_nu == Rol.ROL_SPORTER:
        if request.user.is_authenticated:                                    # pragma: no branch
            account = get_account(request)
            sporter = get_sporter(account)
            if sporter and sporter.is_actief_lid and sporter.bij_vereniging:
                rayon_nr = sporter.bij_vereniging.regio.rayon_nr

    return rayon_nr

# end of file
