# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


from django.db import models
from BasisTypen.models import BoogType
from Account.models import Account, AccountEmail, AccountCreateError, account_is_email_valide
from NhbStructuur.models import NhbLid
from Overig.tijdelijke_url import maak_tijdelijke_url_accountemail
# mag niet afhankelijk zijn van Competitie


class AccountCreateNhbGeenEmail(Exception):
    """ Specifieke foutmelding omdat het NHB lid geen e-mail adres heeft """
    pass


class SchutterBoog(models.Model):
    """ Schutter met een specifiek type boog en zijn voorkeuren
        voor elk type boog waar de schutter interesse in heeft is er een entry
    """
    nhblid = models.ForeignKey(NhbLid, on_delete=models.CASCADE, null=True)

    # het type boog waar dit record over gaat
    boogtype = models.ForeignKey(BoogType, on_delete=models.CASCADE)

    # voorkeuren van de schutter: alleen interesse, of ook actief schieten?
    heeft_interesse = models.BooleanField(default=True)
    voor_wedstrijd = models.BooleanField(default=False)

    # voorkeur voor DT ipv 40cm blazoen (alleen voor 18m Recurve)
    voorkeur_dutchtarget_18m = models.BooleanField(default=False)

    # het account waar dit record bij hoort
    # (niet gebruiken!)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)

    class Meta:
        """ meta data voor de admin interface """
        verbose_name = "SchutterBoog"
        verbose_name_plural = "SchuttersBoog"

    def __str__(self):
        return "%s - %s" % (self.nhblid.nhb_nr, self.boogtype.beschrijving)


def account_create_nhb(nhb_nummer, email, nieuw_wachtwoord):
    """ Maak een nieuw account aan voor een NHB lid
        raises AccountError als:
            - er al een account bestaat
            - het nhb nummer niet valide is
            - het email adres niet bekend is bij de nhb
            - het email adres niet overeen komt
        geeft de url terug die in de email verstuurd moet worden
    """
    if Account.objects.filter(username=nhb_nummer).count() != 0:
        raise AccountCreateError('Account bestaat al')

    # zoek het email adres van dit NHB lid erbij
    try:
        nhb_nr = int(nhb_nummer)
    except ValueError:
        raise AccountCreateError('Onbekend NHB nummer')

    try:
        nhblid = NhbLid.objects.get(nhb_nr=nhb_nr)
    except NhbLid.DoesNotExist:
        raise AccountCreateError('Onbekend NHB nummer')

    if not account_is_email_valide(nhblid.email):
        raise AccountCreateNhbGeenEmail()

    if email != nhblid.email:
        raise AccountCreateError('De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    # maak het account aan
    account = Account()
    account.username = nhb_nummer
    account.set_password(nieuw_wachtwoord)
    account.nhblid = nhblid
    account.save()

    # maak het email record aan
    mail = AccountEmail()
    mail.account = account
    mail.email_is_bevestigd = False
    mail.bevestigde_email = ''
    mail.nieuwe_email = email
    mail.save()

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_url_accountemail(mail, nhb_nummer=nhb_nummer, email=email)
    return url


# end of file
