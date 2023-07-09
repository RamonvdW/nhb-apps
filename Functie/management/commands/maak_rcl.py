# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Functie.models import Functie
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Maak account RCL voor specifieke competitie en regio"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1, help="inlog naam")
        parser.add_argument('afstand', nargs=1, help='Competitie type: 18 of 25')
        parser.add_argument('regio_nr', nargs=1, help='Regio nummer')

    def get_account(self, username):
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            account = None
        return account

    def get_functie_rcl(self, afstand, regio_nr):
        try:
            functie = Functie.objects.get(rol='RCL',
                                          comp_type=afstand,
                                          regio__regio_nr=regio_nr)
        except Functie.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
            functie = None
        return functie

    def handle(self, *args, **options):
        username = options['username'][0]
        account = self.get_account(username)

        regio_nr = options['regio_nr'][0]
        afstand = options['afstand'][0]
        functie = self.get_functie_rcl(afstand, regio_nr)

        if account and functie:
            if functie.accounts.filter(pk=account.pk).count():
                self.stdout.write('[WARNING] Account %s is al %s' % (repr(username), functie.beschrijving))
            else:
                # maak dit account RCL
                functie.accounts.add(account)

                activiteit = "Account %s is nu %s" % (repr(username), functie.beschrijving)

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie='maak_rcl (command line)',
                                   activiteit=activiteit)
                self.stdout.write(activiteit)

# end of file
