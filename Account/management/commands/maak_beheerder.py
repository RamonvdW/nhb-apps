# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account aan vanaf de commandline

import argparse
from django.core.management.base import BaseCommand
from Account.models import Account


class Command(BaseCommand):
    help = "Maak een Account aan"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,
                            help="inlog naam")

    def handle(self, *args, **options):
        username = options['username'][0]
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stdout.write("%s" % str(exc))
            return
        else:
            account.is_staff = True
            account.is_superuser = True
            account.save()
            self.stdout.write("Account %s heeft nu de rechten voor 'beheerder'" % repr(username))

# end of file
