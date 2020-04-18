# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de leeftijdsklassen binnen de NHB applicaties """

from django.utils import timezone
from Account.views import account_add_plugin_login
from BasisTypen.models import LeeftijdsKlasse

# unieke keys voor de server-side sessie variabelen
SESSIONVAR_IS_JONGE_SCHUTTER = 'leeftijdsklasse_is_jonge_schutter'
SESSIONVAR_HUIDIGE_JAAR = 'leeftijdsklasse_huidige_jaar'
SESSIONVAR_LEEFTIJD = 'leeftijdsklasse_leeftijd'
SESSIONVAR_WEDSTRIJDKLASSEN = 'leeftijdsklasse_wedstrijdklassen'        # jaar -1, 0, +1, +2, +3
SESSIONVAR_COMPETITIEKLASSEN = 'leeftijdsklasse_competitieklassen'      # jaar -1, 0, +1, +2, +3


def leeftijdsklassen_plugin_na_login(request, from_ip, account):
    """ zet een paar session variabelen die gebruikt worden om de rol te beheren
        deze functie wordt aangeroepen vanuit de Account.LoginView

        session variables
            gebruiker_rol_mag_wisselen: gebruik van de Plein.WisselVanRolView
    """

    if account.nhblid_set.count() > 0:
        nhblid = account.nhblid_set.all()[0]

        huidige_jaar = timezone.now().year      # TODO: check for correctness in last hours of the year (due to timezone)
        leeftijd = huidige_jaar - nhblid.geboorte_datum.year
        request.session[SESSIONVAR_HUIDIGE_JAAR] = huidige_jaar
        request.session[SESSIONVAR_LEEFTIJD] = leeftijd

        if leeftijd >= 30:
            request.session[SESSIONVAR_IS_JONGE_SCHUTTER] = False
        else:
            request.session[SESSIONVAR_IS_JONGE_SCHUTTER] = True

        wlst = list()
        clst = list()
        # bereken de wedstrijdklasse en competitieklassen
        for n in (-1, 0, 1, 2, 3):
            wleeftijd = leeftijd + n
            cleeftijd = wleeftijd + 1

            wklasse = LeeftijdsKlasse.objects.filter(max_wedstrijdleeftijd__gte=wleeftijd, geslacht='M').order_by('max_wedstrijdleeftijd')[0]
            wlst.append(wklasse.klasse_kort)

            cklasse = LeeftijdsKlasse.objects.filter(max_wedstrijdleeftijd__gte=cleeftijd, geslacht='M').order_by('max_wedstrijdleeftijd')[0]
            clst.append(cklasse.klasse_kort)
        # for

        request.session[SESSIONVAR_WEDSTRIJDKLASSEN] = tuple(wlst)
        request.session[SESSIONVAR_COMPETITIEKLASSEN] = tuple(clst)

    return None


def get_sessionvars_leeftijdsklassen(request):
    """ retourneert de eerder bepaalde informatie over de wedstrijdklasse
        voor jonge schutters (onder de 30 jaar).
        Retourneert:
            Huidige jaar, Leeftijd, False, None, None als het geen jonge schutter betreft
            Huidige jaar, Leeftijd, True, wlst, clst voor jonge schutters
                wlst en clst zijn een lijst van wedstrijdklassen voor
                de jaren -1, 0, +1, +2, +3 ten opzicht van Leeftijd
                Voorbeeld:
                    huidige jaar = 2019
                    leeftijd = 17
                    is_jong = True
                    wlst=(Cadet, Junior, Junior, Junior, Senior)
    """
    try:
        huidige_jaar = request.session[SESSIONVAR_HUIDIGE_JAAR]
    except KeyError:
        # accounts die niet gekoppeld zijn aan een nhblid hebben deze variabelen niet gezet
        return None, None, False, None, None

    leeftijd = request.session[SESSIONVAR_LEEFTIJD]
    is_jong = request.session[SESSIONVAR_IS_JONGE_SCHUTTER]
    wlst = request.session[SESSIONVAR_WEDSTRIJDKLASSEN]
    clst = request.session[SESSIONVAR_COMPETITIEKLASSEN]

    return huidige_jaar, leeftijd, is_jong, wlst, clst


# installeer de plugin
account_add_plugin_login(leeftijdsklassen_plugin_na_login)


# end of file
