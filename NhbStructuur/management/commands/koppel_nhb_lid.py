# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# koppel een account aan een NhbLid vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from NhbStructuur.models import NhbLid


class Command(BaseCommand):
    help = "Koppel een account aan een NHB lid"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,
                            help="inlog naam")

    def handle(self, *args, **options):
        username = options['username'][0]

        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            self.stderr.write('Geen account met username %s gevonden' % repr(username))
        else:
            try:
                lid = NhbLid.objects.get(nhb_nr=username)
            except NhbLid.DoesNotExist:
                self.stderr.write('Geen lid met bondsnummer %s gevonden' % repr(username))
            else:
                lid.account = account
                lid.save(update_fields=['account'])

                self.stdout.write('Account %s gekoppeld aan bijbehorende NHB lid' % repr(username))

# end of file
