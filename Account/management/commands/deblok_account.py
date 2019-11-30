# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# deblokkeer een account, vanaf de command line

import argparse
from django.core.management.base import BaseCommand
from Account.models import Account
from Logboek.models import schrijf_in_logboek
from django.utils import timezone


class Command(BaseCommand):
    help = "Deblokkeer een Account"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,
                            help="inlog naam")

    def handle(self, *args, **options):
        username = options['username'][0]
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
        else:
            if not account.is_geblokkeerd_tot or account.is_geblokkeerd_tot < timezone.now():
                self.stdout.write("Account %s is niet geblokkeerd" % repr(username))
            else:
                account.is_geblokkeerd_tot = timezone.now()
                account.verkeerd_wachtwoord_teller = 0
                account.save()
                self.stdout.write("Account %s is niet meer geblokkeerd" % repr(username))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="deblok_account (command line)",
                                   activiteit="Account %s niet meer geblokkeerd" % repr(username))

# end of file
