# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account aan vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import account_create_username_wachtwoord_email, AccountCreateError


class Command(BaseCommand):
    help = "Maak een Account aan"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,
                            help="inlog naam")
        parser.add_argument('password', nargs=1,
                            help="wachtwoord")
        parser.add_argument('email', nargs=1,
                            help="email")

    def handle(self, *args, **options):
        username = options['username'][0]
        password = options['password'][0]
        email = options['email'][0]

        try:
            account_create_username_wachtwoord_email(username, password, email)
        except AccountCreateError as exc:
            self.stdout.write("%s" % str(exc))
        else:
            self.stdout.write("Aanmaken van account voor %s is gelukt" % repr(username))

# end of file
