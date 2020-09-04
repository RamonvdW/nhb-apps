# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from uuid import uuid5, NAMESPACE_URL

uuid_namespace = uuid5(NAMESPACE_URL, 'Overig.Models.SiteUrls')

# limiet: 20 tekens                12345678901234567890
RECEIVER_BEVESTIG_ACCOUNT_EMAIL = 'account_email'
RECEIVER_BEVESTIG_FUNCTIE_EMAIL = 'functie_email'
RECEIVER_ACCOUNT_WISSEL = 'account_wissel'
RECEIVER_WACHTWOORD_VERGETEN = 'wachtwoord_vergeten'     # 19 lang


class TijdelijkeUrlDispatcher(object):

    """ de dispatcher voorkomt circulaire dependencies tussen models """

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
        return self._dispatcher[topic]

    def set_saver(self, func):
        self._saver = func

    def get_saver(self):
        return self._saver


tijdelijkeurl_dispatcher = TijdelijkeUrlDispatcher()


def set_tijdelijke_url_receiver(topic, func):
    """ gebruikers van de tijdelijke url service kunnen hier hun ontvanger functie
        registreren die aangeroepen wordt als de url gebruikt wordt
        De functie moet 2 argument accepteren:
            een request object en
            het object waar de url op van toepassing is
        De functie moet de url terug geven voor een http-redirect
    """
    tijdelijkeurl_dispatcher.set_receiver(topic, func)


def set_tijdelijke_url_saver(func):
    """ intern gebruik door Overig.models om de url-saver functie te registreren """
    tijdelijkeurl_dispatcher.set_saver(func)


def _maak_url_code(**kwargs):
    """ Bereken een unieke code die we kunnen gebruiken in een URL
    """
    return uuid5(uuid_namespace, repr(kwargs)).hex


def maak_tijdelijke_url_account_email(accountemail, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        account e-mail te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_url_code(**kwargs, pk=accountemail.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_ACCOUNT_EMAIL, geldig_dagen=7, accountemail=accountemail)
    return settings.SITE_URL + reverse('Overig:tijdelijke-url', args=[url_code])


def maak_tijdelijke_url_functie_email(functie):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        functie e-mail te bevestigen.
    """
    url_code = _maak_url_code(pk=functie.pk, email=functie.nieuwe_email)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_BEVESTIG_FUNCTIE_EMAIL, geldig_dagen=7, functie=functie)
    return settings.SITE_URL + reverse('Overig:tijdelijke-url', args=[url_code])


def maak_tijdelijke_url_accountwissel(accountemail, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om eenmalig
        in te loggen als het gekozen account.
    """
    url_code = _maak_url_code(**kwargs, pk=accountemail.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_ACCOUNT_WISSEL, geldig_seconden=60, accountemail=accountemail)
    return settings.SITE_URL + reverse('Overig:tijdelijke-url', args=[url_code])


def maak_tijdelijke_url_wachtwoord_vergeten(accountemail, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden als het
        account wachtwoord vergeten is.
    """
    url_code = _maak_url_code(**kwargs, pk=accountemail.pk)
    func = tijdelijkeurl_dispatcher.get_saver()
    func(url_code, dispatch_to=RECEIVER_WACHTWOORD_VERGETEN, geldig_dagen=7, accountemail=accountemail)
    return settings.SITE_URL + reverse('Overig:tijdelijke-url', args=[url_code])


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
        # referentie = AccountEmail
        func = tijdelijkeurl_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoortbij_accountemail)

    elif obj.dispatch_to == RECEIVER_BEVESTIG_FUNCTIE_EMAIL:
        # referentie = Functie
        func = tijdelijkeurl_dispatcher.get_receiver(obj.dispatch_to)
        redirect = func(request, obj.hoortbij_functie)

    return redirect


def beschrijving_activiteit(obj):
    if obj.dispatch_to == RECEIVER_ACCOUNT_WISSEL:
        return "in te loggen als een andere gebruiker"

    if obj.dispatch_to in (RECEIVER_BEVESTIG_ACCOUNT_EMAIL,
                           RECEIVER_BEVESTIG_FUNCTIE_EMAIL):
        return "bevestig toegang tot e-mail"

    if obj.dispatch_to == RECEIVER_WACHTWOORD_VERGETEN:
        return "een nieuw wachtwoord in te stellen"

    return "????"


# end of file
