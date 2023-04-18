# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account beheerder, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Maak een Account beheerder"

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
            account.is_staff = True
            account.save(update_fields=['is_staff'])

            # schrijf in het logboek
            schrijf_in_logboek(account=None,
                               gebruikte_functie="maak_beheerder (command line)",
                               activiteit="Account %s is beheerder gemaakt" % repr(username))

            self.stdout.write("Account %s is beheerder gemaakt" % repr(username))

# end of file
