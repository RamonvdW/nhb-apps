# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account aan vanaf de commandline

from django.core.management.base import BaseCommand
from Account.operations import account_create, AccountCreateError
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Maak een Account aan"

    def add_arguments(self, parser):
        parser.add_argument('voornaam', nargs=1,
                            help="Voornaam")
        parser.add_argument('username', nargs=1,
                            help="inlog naam")
        parser.add_argument('password', nargs=1,
                            help="wachtwoord")
        parser.add_argument('email', nargs=1,
                            help="email")

    def handle(self, *args, **options):
        voornaam = options['voornaam'][0]
        username = options['username'][0]
        password = options['password'][0]
        email = options['email'][0]

        try:
            account_create(username, voornaam, '', password, email, True)
        except AccountCreateError as exc:
            self.stderr.write("%s" % str(exc))
        else:
            # schrijf in het logboek
            schrijf_in_logboek(account=None,
                               gebruikte_functie="maak_account (command line)",
                               activiteit="Aanmaken van account %s is gelukt" % repr(username))

            self.stdout.write("Aanmaken van account %s is gelukt" % repr(username))

# end of file
