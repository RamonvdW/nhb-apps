# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# zet de is_BB vlag voor een account, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Logboek.models import schrijf_in_logboek


class Command(BaseCommand):
    help = "Geef een of meerdere accounts the is_BB vlag"

    def add_arguments(self, parser):
        parser.add_argument('--set_bb', default=False, action='store_true',
                            help="zet de BB vlag")
        parser.add_argument('--clr_bb',  default=False, action='store_true',
                            help="clear de BB vlag")
        parser.add_argument('username', nargs='+',
                            help="inlog naam / namen")

    def handle(self, *args, **options):
        if options['set_bb'] and options['clr_bb']:
            self.stderr.write('Kies --set_bb of --clr_bb, niet beide')
            return

        if not (options['set_bb'] or options['clr_bb']):
            self.stderr.write('Kies een van --set_bb of --clr_bb')
            return

        for username in options['username']:
            try:
                account = Account.objects.get(username=username)
            except Account.DoesNotExist as exc:
                self.stderr.write('Geen account met de inlog naam %s' % repr(username))
            else:
                if options['set_bb']:
                    if account.is_BB:
                        self.stdout.write('Account %s is al BB -- geen wijziging' % repr(username))
                    else:
                        account.is_BB = True
                        account.save(update_fields=['is_BB'])

                        # schrijf in het logboek
                        schrijf_in_logboek(account=None,
                                           gebruikte_functie="maak_bb (command line)",
                                           activiteit="Account %s is BB gemaakt" % repr(username))

                        self.stdout.write("Account %s is BB gemaakt" % repr(username))
                else:
                    if not account.is_BB:
                        self.stdout.write('Account %s is geen BB -- geen wijziging' % repr(username))
                    else:
                        account.is_BB = False
                        account.save(update_fields=['is_BB'])

                        # schrijf in het logboek
                        schrijf_in_logboek(account=None,
                                           gebruikte_functie="maak_bb (command line)",
                                           activiteit="Account %s is nu geen BB meer" % repr(username))

                        self.stdout.write("Account %s is nu geen BB meer" % repr(username))
        # for

# end of file
