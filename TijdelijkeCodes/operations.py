# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from TijdelijkeCodes.definities import (RECEIVER_BEVESTIG_ACCOUNT_EMAIL, RECEIVER_BEVESTIG_FUNCTIE_EMAIL,
                                        RECEIVER_BEVESTIG_GAST_EMAIL,
                                        RECEIVER_ACCOUNT_WISSEL, RECEIVER_WACHTWOORD_VERGETEN,
                                        RECEIVER_KAMPIOENSCHAP_JA, RECEIVER_KAMPIOENSCHAP_NEE)
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


tijdelijkeurl_dispatcher = TijdelijkeCodesDispatcher()


def set_tijdelijke_codes_receiver(topic, func):
    """ gebruikers van de tijdelijke codes service kunnen hier hun ontvanger functie
        registreren die aangeroepen wordt als de url gebruikt wordt
        De functie moet 2 argument accepteren:
            een django 'request' object en
            het object waar de url op van toepassing is (typisch account of functie)
        De functie moet de url terug geven voor een http-redirect
    """
    tijdelijkeurl_dispatcher.set_receiver(topic, func)


def set_tijdelijke_code_saver(func):
    """ intern gebruik door Overig.models om de url-saver functie te registreren """
    tijdelijkeurl_dispatcher.set_saver(func)


def _maak_unieke_code(**kwargs):
    """ Bereken een unieke code die we kunnen gebruiken in een URL
    """
    return uuid5(uuid_namespace, repr(kwargs)).hex


def maak_tijdelijke_code_account_email(account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        account e-mail te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_ACCOUNT_EMAIL, geldig_dagen=3, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_registreer_gast_email(gast, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        gast-account registratie e-mail te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_unieke_code(**kwargs, pk=gast.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_GAST_EMAIL, geldig_dagen=3, gast=gast)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_functie_email(functie):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        functie e-mail te bevestigen.
    """
    url_code = _maak_unieke_code(pk=functie.pk, email=functie.nieuwe_email)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_FUNCTIE_EMAIL, geldig_dagen=3, functie=functie)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_accountwissel(account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om eenmalig
        in te loggen als het gekozen account.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_ACCOUNT_WISSEL, geldig_seconden=60, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def maak_tijdelijke_code_wachtwoord_vergeten(account, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden als het
        account wachtwoord vergeten is.
    """
    url_code = _maak_unieke_code(**kwargs, pk=account.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_WACHTWOORD_VERGETEN, geldig_dagen=7, account=account)
    return settings.SITE_URL + reverse('TijdelijkeCodes:tijdelijke-url', args=[url_code])


def do_dispatch(request, obj):
    """ Deze functie wordt aangeroepen vanuit de view die de ontvangen url_code
        opgezocht heeft in de database.
            obj is een SiteTijdelijkeUrl
        Deze functie zoekt de callback van de juiste ontvanger op en roept deze aan.
    """
    redirect = None

    if obj.dispatch_to in (RECEIVER_ACCOUNT_WISSEL,
                           RECEIVER_BEVESTIG_ACCOUNT_EMAIL,
                           RECEIVER_WACHTWOORD_VERGETEN):
        # referentie = Account
        func = tijdelijkeurl_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoortbij_account)

    elif obj.dispatch_to == RECEIVER_BEVESTIG_GAST_EMAIL:
        # referentie = GastRegistratie
        func = tijdelijkeurl_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoortbij_gast)

    elif obj.dispatch_to == RECEIVER_BEVESTIG_FUNCTIE_EMAIL:
        # referentie = Functie
        func = tijdelijkeurl_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoortbij_functie)

    elif obj.dispatch_to in (RECEIVER_KAMPIOENSCHAP_JA,
                             RECEIVER_KAMPIOENSCHAP_NEE):
        # referentie = KampioenschapSchutterBoog
        wil_meedoen = (obj.dispatch_to == RECEIVER_KAMPIOENSCHAP_JA)
        func = tijdelijkeurl_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoortbij_kampioenschap, wil_meedoen)

    return redirect


def beschrijving_activiteit(obj):

    # Je hebt verzocht om ...

    if obj.dispatch_to == RECEIVER_ACCOUNT_WISSEL:
        return "in te loggen als een andere gebruiker"

    if obj.dispatch_to in (RECEIVER_BEVESTIG_ACCOUNT_EMAIL,
                           RECEIVER_BEVESTIG_FUNCTIE_EMAIL,
                           RECEIVER_BEVESTIG_GAST_EMAIL):
        return "een e-mailadres te bevestigen"

    if obj.dispatch_to == RECEIVER_WACHTWOORD_VERGETEN:
        return "een nieuw wachtwoord in te stellen"

    if obj.dispatch_to == RECEIVER_KAMPIOENSCHAP_JA:
        return "je beschikbaarheid voor een kampioenschap te bevestigen"

    if obj.dispatch_to == RECEIVER_KAMPIOENSCHAP_NEE:
        return "je af te melden voor een kampioenschap"

    return "????"


# end of file
