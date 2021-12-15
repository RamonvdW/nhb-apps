# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# reset the tweede factor koppeling voor een account

from django.core.management.base import BaseCommand
from Account.models import Account
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Reset de OTP / 2FA koppeling"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,  help="inlog naam")
        parser.add_argument('--reset_secret', action='store_true', help="Huidige OTP geheim verwijderen")

    def handle(self, *args, **options):
        username = options['username'][0]
        reset_secret = options['reset_secret']

        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
        else:
            if not account.otp_is_actief:
                self.stdout.write("Account %s heeft OTP niet aan staan" % repr(username))
            else:
                account.otp_is_actief = False
                if reset_secret:
                    account.otp_code = "x"
                account.save()
                self.stdout.write("Account %s moet nu opnieuw de OTP koppeling leggen" % repr(username))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="reset_otp (command line)",
                                   activiteit="Account %s moet nu opnieuw de OTP koppeling leggen" % repr(username))

# end of file
