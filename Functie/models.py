# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from NhbStructuur.models import NhbRegio, NhbRayon, NhbVereniging
from Account.models import Account, HanterenPersoonsgegevens
import datetime

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

    # welke accounts zijn gekoppeld aan deze functie
    accounts = models.ManyToManyField(Account,
                                      blank=True)   # mag leeg zijn / gemaakt worden

    # in principe vrije tekst
    beschrijving = models.CharField(max_length=50)

    # een aantal velden om de juiste Functie te kunnen koppelen

    # BKO, RKO, RCL, SEC, HWL, WL (mogelijk later RKWL, BKWL)
    rol = models.CharField(max_length=5)

    # email adres wat bij deze functie hoort
    bevestigde_email = models.EmailField(blank=True)
    nieuwe_email = models.EmailField(blank=True)

    # BKO/RKO/RCL: voor de 18 (Indoor) of 25 (25m 1pijl) competitie?
    # leeg voor functies op verenigingsniveau (SEC, HWL, WL)
    comp_type = models.CharField(max_length=2, default="", blank=True)

    # RKO only: rayon
    nhb_rayon = models.ForeignKey(NhbRayon, on_delete=models.PROTECT, null=True, blank=True)

    # RCL only: regio
    nhb_regio = models.ForeignKey(NhbRegio, on_delete=models.PROTECT, null=True, blank=True)

    # SEC/HWL/WL only: vereniging
    nhb_ver = models.ForeignKey(NhbVereniging, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        """ Geef een string terug voor gebruik in de admin interface """
        return self.beschrijving

    objects = models.Manager()      # for the editor only


def maak_functie(beschrijving, rol):
    """ Deze helper geeft het Functie object terug met de gevraagde parameters
        De eerste keer wordt deze aangemaakt.
    """
    functie, _ = Functie.objects.get_or_create(beschrijving=beschrijving, rol=rol)
    return functie      # caller kan zelf andere velden invullen


def maak_account_vereniging_secretaris(nhb_ver, account):
    """ Maak het NHB lid de secretaris van de NHB vereniging
        Retourneert True als het NHB lid aan de SEC functie toegevoegd is
    """

    # zoek de SEC functie van de vereniging erbij
    functie = Functie.objects.get(rol='SEC', nhb_ver=nhb_ver)

    # kijk of dit lid al in de groep zit
    if functie.accounts.filter(pk=account.pk).count() == 0:
        # nog niet gekoppeld aan de functie --> koppel dit account nu
        functie.accounts.add(account)
        return True

    return False


def account_needs_vhpg(account, show_only=False):
    """ Controleer of het Account een VHPG af moet leggen """

    if not account_needs_otp(account):
        # niet nodig
        return False, None

    if show_only:
        return True, None

    # kijk of de acceptatie recent al afgelegd is
    try:
        vhpg = HanterenPersoonsgegevens.objects.only('acceptatie_datum').get(account=account)
    except HanterenPersoonsgegevens.DoesNotExist:
        # niet uitgevoerd, wel nodig
        return True, None

    # elke 11 maanden moet de verklaring afgelegd worden
    # dit is ongeveer (11/12)*365 == 365-31 = 334 dagen
    opnieuw = vhpg.acceptatie_datum + datetime.timedelta(days=334)
    now = timezone.now()
    return opnieuw < now, vhpg


def account_needs_otp(account):
    """ Controleer of het Account OTP verificatie nodig heeft

        Returns: True or False
        Bepaalde rechten vereisen OTP:
            is_BB
            is_staff
            bepaalde functies
    """
    if account.is_authenticated:
        if account.is_BB or account.is_staff:
            return True

        # alle functies hebben OTP nodig
        if account.functie_set.count() > 0:
            return True

    return False

# end of file
