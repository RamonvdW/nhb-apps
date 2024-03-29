# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account SEC van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Functie.models import Functie
from Vereniging.models import Vereniging
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Maak account SEC voor specifieke vereniging"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1, help="inlog naam")
        parser.add_argument('ver_nr', nargs=1, help='Verenigingsnummer')

    def get_account(self, username):
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            account = None
        return account

    def get_vereniging(self, ver_nr):
        try:
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            ver = None
        return ver

    def get_functie_sec(self, ver):
        try:
            functie = Functie.objects.get(rol='SEC', vereniging=ver)
        except Functie.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            functie = None
        return functie

    def handle(self, *args, **options):
        username = options['username'][0]
        account = self.get_account(username)

        ver_nr = options['ver_nr'][0]
        ver = self.get_vereniging(ver_nr)

        if account and ver:
            functie = self.get_functie_sec(ver)

            if functie:
                if functie.accounts.filter(pk=account.pk).count():
                    self.stdout.write('[WARNING] Account %s is al SEC van vereniging %s' % (repr(username), ver))
                else:
                    # maak dit account SEC
                    functie.accounts.add(account)

                    activiteit = "Account %s is SEC gemaakt van vereniging %s" % (repr(username), ver)

                    # schrijf in het logboek
                    schrijf_in_logboek(account=None,
                                       gebruikte_functie='maak_sec (command line)',
                                       activiteit=activiteit)
                    self.stdout.write(activiteit)

# end of file
