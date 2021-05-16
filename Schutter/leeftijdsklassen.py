# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" ondersteuning voor de leeftijdsklassen binnen de NHB applicaties """

from django.utils import timezone
from BasisTypen.models import LeeftijdsKlasse, IndivWedstrijdklasse


def bereken_leeftijdsklassen(request):
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

    # pak het huidige jaar na conversie naar lokale tijdzone
    # zodat dit ook goed gaat in de laatste paar uren van het jaar
    now = timezone.now()  # is in UTC
    now = timezone.localtime(now)  # convert to active timezone (say Europe/Amsterdam)
    huidige_jaar = now.year

    c_pks = list()
    for obj in IndivWedstrijdklasse.objects.prefetch_related('leeftijdsklassen').all():
        for pk in list(obj.leeftijdsklassen.values_list('pk', flat=True)):
            if pk not in c_pks:
                c_pks.append(pk)
    # for

    account = request.user
    if account.is_authenticated:
        if account.nhblid_set.count() > 0:
            nhblid = account.nhblid_set.all()[0]

            leeftijd = huidige_jaar - nhblid.geboorte_datum.year
            is_jong = (leeftijd < 30)

            lkl = (LeeftijdsKlasse
                   .objects
                   .order_by('volgorde'))

            wlst = list()
            clst = list()
            # bereken de wedstrijdklassen en competitieklassen
            for n in (-1, 0, 1, 2, 3):
                wleeftijd = leeftijd + n
                cleeftijd = wleeftijd + 1

                wklasse = None
                cklasse = None
                for klasse in lkl:
                    if klasse.leeftijd_is_compatible(wleeftijd):
                        if leeftijd >= 50 or wklasse is None:
                            wklasse = klasse

                    if klasse.pk in c_pks:
                        if klasse.leeftijd_is_compatible(cleeftijd):
                            cklasse = klasse
                # for

                wlst.append(wklasse.klasse_kort)
                clst.append(cklasse.klasse_kort)
            # for

            return huidige_jaar, leeftijd, is_jong, wlst, clst

    # accounts die niet gekoppeld zijn aan een nhblid hebben deze variabelen niet gezet
    return None, None, False, None, None


# end of file
