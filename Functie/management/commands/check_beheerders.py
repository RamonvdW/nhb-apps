# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# toon de beheerders van elke functies en eventuele bijzonderheden

from django.conf import settings
from django.core.management.base import BaseCommand
from Functie.models import Functie
from Sporter.models import Sporter


class Command(BaseCommand):
    help = "Check aan de functies gekoppelde beheerders"

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help="Toon alle")
        parser.add_argument('--otp_uit', action='store_true', help="Zet 2FA uit waar niet meer nodig")

    def handle(self, *args, **options):

        toon_alle = options['all']
        otp_uit = options['otp_uit']

        for functie in (Functie
                        .objects
                        .prefetch_related('accounts')
                        .select_related('vereniging')
                        .exclude(vereniging__ver_nr=settings.EXTERN_VER_NR)
                        .order_by('vereniging', 'rol')):

            functie_getoond = False

            account_pks = list(functie.accounts.values_list('pk', flat=True))
            for sporter in Sporter.objects.filter(account__in=account_pks).select_related('bij_vereniging'):
                let_op = ''
                if not sporter.bij_vereniging or not sporter.is_actief_lid:
                    # deze melding komt na 15 januari
                    let_op = 'LET OP: geen lid meer bij een vereniging'
                elif functie.vereniging and sporter.bij_vereniging != functie.vereniging:
                    # functie voor beheerder van een vereniging
                    # lid is overgestapt
                    let_op = 'LET OP: geen lid bij deze vereniging'

                if toon_alle or len(let_op) > 0:
                    if not functie_getoond:                                         # pragma: no branch
                        self.stdout.write('Functie: %s' % functie.beschrijving)
                        functie_getoond = True

                    self.stdout.write('  [%s] %s  %s' % (sporter.lid_nr, sporter.volledige_naam(), let_op))
            # for
        # for

        # zoek accounts zonder functie koppelen maar (nog) wel tweede factor actief
        self.stdout.write('\nActieve leden met 2FA maar niet meer gekoppeld aan een functie:')
        count = 0
        for sporter in (Sporter
                        .objects
                        .select_related('account')
                        .filter(account__otp_is_actief=True)
                        .exclude(account__is_BB=True)
                        .exclude(account__is_staff=True)
                        .prefetch_related('account__functie_set')
                        .order_by('lid_nr')):

            account = sporter.account
            if account.functie_set.count() == 0:
                let_op = ''
                if not sporter.is_actief_lid:
                    let_op = 'LET OP: geen actief lid'
                self.stdout.write('  %s  %s' % (sporter.lid_nr_en_volledige_naam(), let_op))
                count += 1
                if otp_uit:
                    account.otp_is_actief = False
                    account.save(update_fields=['otp_is_actief'])
        # for
        if not count:
            self.stdout.write('  Geen')
        else:
            if not otp_uit:
                self.stdout.write('Gebruik --otp_uit om 2FA uit te zetten voor deze accounts')

    """
        performance debug helper:
    
        from django.db import connection
    
            q_begin = len(connection.queries)
    
            # queries here
    
            print('queries: %s' % (len(connection.queries) - q_begin))
            for obj in connection.queries[q_begin:]:
                print('%10s %s' % (obj['time'], obj['sql'][:200]))
            # for
            sys.exit(1)
    
        test uitvoeren met DEBUG=True via --settings=Site.settings_dev anders wordt er niets bijgehouden
    """

# end of file
