# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from Account.models import Account
from Competitie.models import KampioenschapSporterBoog
from Functie.models import Functie
from Registreer.models import GastRegistratie
from TijdelijkeCodes.definities import (RECEIVER_BEVESTIG_EMAIL_ACCOUNT, RECEIVER_BEVESTIG_EMAIL_FUNCTIE,
                                        RECEIVER_BEVESTIG_EMAIL_REG_GAST, RECEIVER_BEVESTIG_EMAIL_REG_LID,
                                        RECEIVER_ACCOUNT_WISSEL, RECEIVER_WACHTWOORD_VERGETEN,
                                        RECEIVER_DEELNAME_KAMPIOENSCHAP)
from TijdelijkeCodes.models import TijdelijkeCode
from uuid import uuid5, NAMESPACE_URL


uuid_namespace = uuid5(NAMESPACE_URL, 'TijdelijkeCodes.Models.TijdelijkeUrl')


class TijdelijkeCodesDispatcher(object):

    """ de dispatcher voorkomt circulaire dependencies tussen modellen en applicaties """

    def __init__(self):
        self._dispatcher = dict()       # [entry] = func
        self._backup = None
        self._saver = None

    def test_backup(self):
        self._backup = dict(self._dispatcher)

    def test_restore(self):
        self._dispatcher = self._backup
        self._backup = None

    def set_receiver(self, topic, func):
        self._dispatcher[topic] = func

    def get_receiver(self, topic):
        try:
            return self._dispatcher[topic]
        except KeyError:
            raise NotImplementedError('Receiver function not configured for topic %s' % repr(topic))

    def set_saver(self, func):
        self._saver = func

    def get_saver(self):
        return self._saver


tijdelijke_code_dispatcher = TijdelijkeCodesDispatcher()


def set_tijdelijke_codes_receiver(topic, func):
    """ gebruikers van de tijdelijke codes service kunnen hier hun ontvanger functie
        registreren die aangeroepen wordt als de url gebruikt wordt
        De functie moet 2 argument accepteren:
            een django 'request' object en
            het object waar de url op van toepassing is (typisch account of functie)
        De functie moet de url terug geven voor een http-redirect
    """
    tijdelijke_code_dispatcher.set_receiver(topic, func)


def set_tijdelijke_code_saver(func):
    """ intern gebruik door Overig.models om de url-saver functie te registreren """
    tijdelijke_code_dispatcher.set_saver(func)


def _maak_unieke_code(**kwargs):
    """ Bereken een unieke code die we kunnen gebruiken in een URL
    """
    return uuid5(uuid_namespace, repr(kwargs)).hex


def maak_tijdelijke_code_bevestig_email_account(account: Account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om
        toegang tot de (nieuwe) e-mail van een account te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_EMAIL_ACCOUNT, geldig_dagen=3, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_bevestig_email_registreer_lid(account: Account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om
        toegang tot de e-mail en het aanmaken van een account te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_EMAIL_REG_LID, geldig_dagen=3, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_bevestig_email_registreer_gast(gast: GastRegistratie, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om
        toegang tot de e-mail en het aanmaken van een gast-account te bevestigden.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_unieke_code(**kwargs, pk=gast.pk)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_EMAIL_REG_GAST, geldig_dagen=3, gast=gast)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_bevestig_email_functie(functie: Functie):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        toegang tot de (nieuwe) e-mail te bevestigen voor gebruik voor een functie.
    """
    url_code = _maak_unieke_code(pk=functie.pk, email=functie.nieuwe_email)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_EMAIL_FUNCTIE, geldig_dagen=3, functie=functie)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_accountwissel(account: Account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om eenmalig
        in te loggen als het gekozen account.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_ACCOUNT_WISSEL, geldig_seconden=60, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_wachtwoord_vergeten(account: Account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden als het
        account wachtwoord vergeten is.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_WACHTWOORD_VERGETEN, geldig_dagen=7, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_deelname_kampioenschap(kampioen: KampioenschapSporterBoog, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om deelname aan een kampioenschap
        door een specifieke KampioenschapSporterBoog te bevestigen of af te melden.
    """
    url_code = _maak_unieke_code(**kwargs, pk=kampioen.pk)
    func = tijdelijke_code_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_DEELNAME_KAMPIOENSCHAP, geldig_dagen=7, kampioen=kampioen)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def do_dispatch(request, obj: TijdelijkeCode):
    """ Deze functie wordt aangeroepen vanuit de POST handler die de ontvangen url_code opgezocht heeft in de database.
            obj is een TijdelijkeCode
        Deze functie zoekt de callback van de juiste ontvanger op en roept deze aan.
    """
    redirect = None

    if obj.dispatch_to in (RECEIVER_ACCOUNT_WISSEL,
                           RECEIVER_BEVESTIG_EMAIL_ACCOUNT,
                           RECEIVER_BEVESTIG_EMAIL_REG_LID,
                           RECEIVER_WACHTWOORD_VERGETEN):
        # referentie = Account
        func = tijdelijke_code_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoort_bij_account)

    elif obj.dispatch_to == RECEIVER_BEVESTIG_EMAIL_REG_GAST:
        # referentie = GastRegistratie
        func = tijdelijke_code_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoort_bij_gast_reg)

    elif obj.dispatch_to == RECEIVER_BEVESTIG_EMAIL_FUNCTIE:
        # referentie = Functie
        func = tijdelijke_code_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoort_bij_functie)

    elif obj.dispatch_to == RECEIVER_DEELNAME_KAMPIOENSCHAP:
        # referentie = KampioenschapSporterBoog
        func = tijdelijke_code_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoort_bij_kampioen)

    return redirect


def beschrijving_activiteit(obj):

    # Je hebt verzocht om ...

    if obj.dispatch_to == RECEIVER_ACCOUNT_WISSEL:
        return "in te loggen als een andere gebruiker"

    if obj.dispatch_to in (RECEIVER_BEVESTIG_EMAIL_ACCOUNT,
                           RECEIVER_BEVESTIG_EMAIL_FUNCTIE):
        return "een e-mailadres te bevestigen"

    if obj.dispatch_to == RECEIVER_BEVESTIG_EMAIL_REG_LID:
        return "een account aan te maken"

    if obj.dispatch_to == RECEIVER_BEVESTIG_EMAIL_REG_GAST:
        return "een gast-account aan te maken"

    if obj.dispatch_to == RECEIVER_WACHTWOORD_VERGETEN:
        return "een nieuw wachtwoord in te stellen"

    if obj.dispatch_to == RECEIVER_DEELNAME_KAMPIOENSCHAP:
        return "je beschikbaarheid voor een kampioenschap door te geven"

    return "????"


# end of file
