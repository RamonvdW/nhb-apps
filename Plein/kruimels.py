# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse

# global translation of urlconf names to the breadcrumb labels
KRUIMEL2LABEL = {
    'Plein:plein': 'Home',
    'Plein:privacy': 'Privacy',
    'HistComp:allejaren': 'Historische competitie uitslagen',
    'HistComp:indiv': 'Individueel',
    'HistComp:team': 'Team',
    'Records:overzicht': 'Nederlandse Records',
    'Records:indiv': 'Individuele records',
    'Records:team': 'Team records',
    'Records:zoek': 'Zoek in records',
    'Overig:feedback-formulier': 'Feedback formulier',
    'Overig:feedback-bedankt': 'Bedankt',
    'Account:login': 'Login',
    'Account:uitgelogd': 'Uitgelogd',
    'Account:registreer': 'Registreer',
    'Account:aangemaakt': 'Aangemaakt',
    'Account:wachtwoord-vergeten': 'Wachtwoord vergeten'
}


def make_context_broodkruimels(context, *kruimels):
    """ Deze functie kan vanuit een class-based view get_context functie aangeroepen
       worden om de broodkruimels samen te stellen.
       kruimels: string met urlconf naam waar een reverse() op gedaan kan worden,
               of
                 tuple(label, url)

       voorbeelden:
           make_context_broodkruimels(context, 'Plein:plein')
           make_context_broodkruimels(context, ('Plein:plein', ('Titel', '/een/url/')))
   """
    #print("make_context_broodkruimels: kruimels=%s" % repr(kruimels))
    context['broodkruimels'] = list()
    for kruimel in kruimels:
        # print("   kruimel=%s" % repr(kruimel))
        if isinstance(kruimel, str):
            url = reverse(kruimel)      # TODO: handle NoReverseMatch exception
            try:
                label = KRUIMEL2LABEL[kruimel]
            except KeyError:
                label = '?label?'
            tup = (label, url)
        else:
            # pre-generated description + url
            tup = kruimel
        context['broodkruimels'].append(tup)
    # for

# end of file
