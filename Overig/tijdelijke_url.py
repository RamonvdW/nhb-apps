# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from uuid import uuid5, NAMESPACE_URL

uuid_namespace = uuid5(NAMESPACE_URL, 'Overig.Models.SiteUrls')


# dit gedoe met de dispatcher is om geen last te hebben van circulaire dependencies
# Overig.models gebruikt Account.Account en Account.AccountEmail
# als Account deze file includeert en wij Overig.models dan hebben we een circulaire dependency
SAVER = '__saver__'
RECEIVER_ACCOUNTEMAIL = 'accountemail'
dispatcher = dict()


def set_tijdelijke_url_receiver(topic, func):
    """ gebruikers van de tijdelijke url service kunnen hier hun ontvanger functie
        registreren die aangeroepen wordt als de url gebruikt wordt
        De functie moet 1 argument accepteren: het object waar de url op van toepassing is
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
        account email te bevestigen.
        Een SiteTijdelijkeUrl record wordt in de database gezet met de
        url_code en waar deze voor bedoeld is.
        De volledige url wordt terug gegeven.
    """
    url_code = _maak_url_code(**kwargs)
    dispatcher[SAVER](url_code, geldig_dagen=7, accountemail=accountemail)
    return reverse('Overig:tijdelijke-url', args=[url_code])

# end of file
