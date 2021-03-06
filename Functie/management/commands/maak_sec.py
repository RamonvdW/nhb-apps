# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account SEC van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Functie.models import Functie
from NhbStructuur.models import NhbVereniging
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Maak account SEC voor specifieke vereniging"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1, help="inlog naam")
        parser.add_argument('vereniging_nhb_nr', nargs=1, help='NHB nummer van de vereniging')

    def get_account(self, username):
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            account = None
        return account

    def get_vereniging(self, nhb_nr):
        try:
            nhb_ver = NhbVereniging.objects.get(nhb_nr=nhb_nr)
        except NhbVereniging.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            nhb_ver = None
        return nhb_ver

    def get_functie_sec(self, nhb_ver):
        try:
            functie = Functie.objects.get(rol='SEC', nhb_ver=nhb_ver)
        except Functie.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            functie = None
        return functie

    def handle(self, *args, **options):
        username = options['username'][0]
        account = self.get_account(username)

        vereniging_nhb_nr = options['vereniging_nhb_nr'][0]
        nhb_ver = self.get_vereniging(vereniging_nhb_nr)

        if account and nhb_ver:
            functie = self.get_functie_sec(nhb_ver)

            if functie:
                if functie.accounts.filter(pk=account.pk).count():
                    self.stderr.write('[WARNING] Account %s is al SEC van vereniging %s' % (repr(username), nhb_ver))
                else:
                    # maak dit account SEC
                    functie.accounts.add(account)

                    activiteit = "Account %s is SEC gemaakt van vereniging %s" % (repr(username), nhb_ver)

                    # schrijf in het logboek
                    schrijf_in_logboek(account=None,
                                       gebruikte_functie='maak_sec (command line)',
                                       activiteit=activiteit)
                    self.stdout.write(activiteit)

# end of file
