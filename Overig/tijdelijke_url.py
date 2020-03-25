# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from uuid import uuid5, NAMESPACE_URL

uuid_namespace = uuid5(NAMESPACE_URL, 'Overig.Models.SiteUrls')


# dit gedoe met de dispatcher is om geen last te hebben van circulaire dependencies
# Overig.models gebruikt Account.Account en Account.AccountEmail
# als Account deze file importeert en wij Overig.models dan hebben we een circulaire dependency
SAVER = '__saver__'
RECEIVER_BEVESTIG_EMAIL = 'bevestig_email'
RECEIVER_SELECTEER_SCHUTTER = 'selecteer_schutter'

dispatcher = dict()


def set_tijdelijke_url_receiver(topic, func):
    """ gebruikers van de tijdelijke url service kunnen hier hun ontvanger functie
        registreren die aangeroepen wordt als de url gebruikt wordt
        De functie moet 2 argument accepteren:
            een request object en
            het object waar de url op van toepassing is
        De functie moet de url terug geven voor een http-redirect
    """
    if topic != SAVER:
        dispatcher[topic] = func


def set_tijdelijke_url_saver(func):
    """ intern gebruik door Overig.models om de url-saver functie te registereren """
    dispatcher[SAVER] = func


def _maak_url_code(**kwargs):
    """ Bereken een unieke code die we kunnen gebruiken in een URL
    """
    return uuid5(uuid_namespace, repr(kwargs)).hex


def maak_tijdelijke_url_accountemail(accountemail, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om een
        account e-mail te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_url_code(**kwargs)
    dispatcher[SAVER](url_code, dispatch_to="bevestig_email", geldig_dagen=7, accountemail=accountemail)
    return settings.SITE_URL + reverse('Overig:tijdelijke-url', args=[url_code])


def maak_tijdelijke_url_selecteer_schutter(accountemail, **kwargs):
    """ Maak een tijdelijke URL aan die gebruikt kan worden om eenmalig
        in te loggen als het gekozen account.
    """
    url_code = _maak_url_code(**kwargs)
    dispatcher[SAVER](url_code, dispatch_to="selecteer_schutter", geldig_seconden=60, accountemail=accountemail)
    return settings.SITE_URL + reverse('Overig:tijdelijke-url', args=[url_code])


def do_dispatch(request, obj):
    """ Deze functie wordt aangeroepen vanuit de view die de ontvangen url_code
        opgezocht heeft in de database.
        Deze functie zoekt de callback van de juiste ontvanger op en roept deze aan.
    """

    redirect = None

    if obj.dispatch_to == "selecteer_schutter":
        func = dispatcher[RECEIVER_SELECTEER_SCHUTTER]
        redirect = func(request, obj.hoortbij_accountemail)

    elif obj.dispatch_to == "bevestig_email":
        func = dispatcher[RECEIVER_BEVESTIG_EMAIL]
        redirect = func(request, obj.hoortbij_accountemail)

    # TODO: verwijder onderstaande legacy methode na 2020-04-02
    elif obj.hoortbij_accountemail:
        func = dispatcher[RECEIVER_BEVESTIG_EMAIL]
        redirect = func(request, obj.hoortbij_accountemail)

    return redirect

# end of file
