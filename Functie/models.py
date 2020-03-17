# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.contrib.auth.models import Group
from NhbStructuur.models import NhbRegio, NhbRayon, NhbVereniging


""" Deze module houdt bij wie beheerders zijn

    Functies: BKO, RKO, RCL, BKWL, RKWL, WL zijn functies
    (IT en BB: staan in het Account als is_staff en is_BB)
    
    Een Account is lid van een of meerdere functies
        Hiermee wordt het Account gekoppeld aan een Functie
        en krijgt de gebruiker 'rechten'
        
    Voorbeeld:
        Account = 'ramon'
        Account.functies = [Functie: 'RKO Rayon 1']
"""

"""
    Standaard functies zijn aangemaakt door de migratie functies van deze app
    BKO Indoor
    RKO Rayon 1 Indoor
    RKO Rayon 2 Indoor
    etc.
    RCL Regio 101 Indoor
    RCL Regio 102 Indoor
    etc.
    BKO 25m 1pijl
    etc.
"""


class Functie(models.Model):

    """ Deze klasse representeert een Functie met rechten """

    # in principe vrije tekst
    beschrijving = models.CharField(max_length=50)

    # een aantal velden om de juiste Functie te kunnen koppelen

    # BKO, RKO, RCL, CWZ, BKWL, RKWL, WL
    rol = models.CharField(max_length=5)

    # BKO/RKO/RCL: voor de 18 (Indoor) of 25 (25m 1pijl) competitie?
    # leeg voor CWZ
    comp_type = models.CharField(max_length=2, default="", blank=True)

    # RKO only: rayon
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT, null=True, blank=True)

    # RCL only: regio
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT, null=True, blank=True)

    # CWZ/WL only: vereniging
    nhb_ver = models.ForeignKey(NhbVereniging, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        """ Geef een string terug voor gebruik in de admin interface """
        return self.beschrijving

    @staticmethod
    def needs_otp():
        """ Deze functie wordt aangeroepen vanuit Account.models.account_needs_otp()
            Op dit moment geven we altijd True terug - dit kan in de toekomst verfijnd worden
        """
        return True


def maak_functie(beschrijving, rol):

    try:
        functie = Functie.objects.get(beschrijving=beschrijving, rol=rol)
    except Functie.DoesNotExist:
        # maak een nieuwe Functie aan
        functie = Functie()
        functie.beschrijving = beschrijving
        functie.rol = rol
        functie.save()

    return functie      # caller kan zelf andere velden invullen


def maak_cwz(nhb_ver, account):
    """ Maak het NHB lid een van de CWZ's van de NHB vereniging
        Retourneert True als het NHB lid in de CWZ groep gestopt is
    """

    # zoek de CWZ functie erbij
    functie = Functie.objects.get(rol="CWZ", nhb_ver=nhb_ver)

    # kijk of dit lid al in de groep zit
    if len(account.functies.filter(pk=functie.pk)) == 0:
        # nog niet gekoppeld aan de functie --> koppel dit account nu
        account.functies.add(functie)
        return True

    return False


# end of file
