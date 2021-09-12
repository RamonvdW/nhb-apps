# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Routines om de database te vullen met een test set die gebruikt wordt in vele van de test cases """

from django.utils import timezone
from Account.models import Account, account_create
from Functie.models import VerklaringHanterenPersoonsgegevens
from NhbStructuur.models import NhbVereniging, NhbLid

# fixtures zijn overwogen, maar zijn lastig te onderhouden en geven geen recente datums (zoals voor VHPG)


class TestData(object):

    """ maak een standaard set data aan die in veel tests gebruikt kan worden

        gebruik:
            from django.test import TestCase
            from TestHelpers import testdata

            class MyTests(TestCase):

                @classmethod
                def setUpClass(cls):
                    super().setUpClass()
                    cls.testdata = testdata.TestData()
    """

    WACHTWOORD = "qewretrytuyi"  # sterk genoeg default wachtwoord

    def __init__(self):
        self.account_admin = None
        self.account_bb = None

    def maak_accounts(self):
        # admin
        self.account_admin = self._create_account('admin', 'admin@test.com', 'Admin')
        self.account_admin.is_staff = True
        self.account_admin.is_superuser = True
        self.account_admin.save()

        # maak een BB aan, nodig voor de competitie
        self.account_bb = self._create_account('bb', 'bb@test.com', 'Bond')
        self.account_bb.is_BB = True
        self.account_bb.save()

        self._accepteer_vhpg_voor_alle_accounts()

    def _create_account(self, username, email, voornaam):
        """ Maak een Account met AccountEmail aan in de database van de website """
        account_create(username, voornaam, '', self.WACHTWOORD, email, email_is_bevestigd=True)
        account = Account.objects.get(username=username)

        # zet OTP actief (een test kan deze altijd weer uit zetten)
        account.otp_code = "whatever"
        account.otp_is_actief = True
        account.save()

        return account

    @staticmethod
    def _accepteer_vhpg_voor_alle_accounts():
        """ accepteer de VHPG voor alle accounts """
        now = timezone.now()
        bulk = list()
        for account in Account.objects.all():
            vhpg = VerklaringHanterenPersoonsgegevens(
                        account=account,
                        acceptatie_datum=now)
            bulk.append(vhpg)
        # for
        VerklaringHanterenPersoonsgegevens.objects.bulk_create(bulk)


def maak_clubs_en_leden():
    # maak een BB aan, nodig om de competitie defaults in te zien
    self.account_bb = self.e2e_create_account('bb', 'bb@test.com', 'BB', accepteer_vhpg=True)
    self.account_bb.is_BB = True
    self.account_bb.save()

    _accepteer_vhpg_alle_accounts()
    # accepteer de VHPG voor alle accounts


def account_vhpg_is_geaccepteerd(account):
    """ onthoud dat de vhpg net geaccepteerd is door de gebruiker
    """
    # Deze functie wordt aangeroepen vanuit een POST handler
    # concurrency beveiliging om te voorkomen dat 2 records gemaakt worden
    obj, created = (VerklaringHanterenPersoonsgegevens
                    .objects
                    .update_or_create(account=account,
                                      defaults={'acceptatie_datum': timezone.now()}))



# end of file
