# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# zet het 2FA geheim van een account, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Zet het 2FA geheim van een account"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1,
                            help="inlog naam")
        parser.add_argument('geheim', nargs=1,
                            help="2FA geheim (16 of 32 tekens)")
        parser.add_argument('--zet-actief', action='store_true')

    def handle(self, *args, **options):
        username = options['username'][0]
        geheim = options['geheim'][0]

        if len(geheim) not in (16, 32):
            self.stderr.write("Foutief 2FA geheim: moet 16 of 32 tekens lang zijn")
            return

        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist as exc:
            self.stderr.write("%s" % str(exc))
        else:
            account.otp_code = geheim
            msg = "2FA is opgeslagen voor account %s" % repr(username)

            if options['zet_actief']:
                account.otp_is_actief = True
                msg += " en actief gezet"

            account.save(update_fields=['otp_is_actief', 'otp_code'])

            # schrijf in het logboek
            schrijf_in_logboek(account=None,
                               gebruikte_functie="zet_2fa_geheim (command line)",
                               activiteit="2FA geheim is opgeslagen voor account %s" % repr(username))

            self.stdout.write(msg)

# end of file
