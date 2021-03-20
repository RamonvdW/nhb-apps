# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# toon de beheerders van elke functies en eventuele bijzonderheden

from django.core.management.base import BaseCommand
from Functie.models import Functie


class Command(BaseCommand):
    help = "Check aan de functies gekoppelde beheerders"

    def handle(self, *args, **options):
        for functie in (Functie
                        .objects
                        .prefetch_related('accounts')
                        .order_by('nhb_ver', 'rol')):
            self.stdout.write('Functie: %s' % functie.beschrijving)
            for account in functie.accounts.all():
                let_op = ''
                try:
                    nhblid = account.nhblid_set.all()[0]
                except IndexError:
                    nhblid = None
                    let_op = 'LET OP: geen koppeling met NHB lid'
                else:
                    if not nhblid.bij_vereniging or not nhblid.is_actief_lid:
                        # deze melding komt na 15 januari
                        let_op = 'LET OP: geen lid meer bij een vereniging'
                    elif functie.nhb_ver and nhblid.bij_vereniging != functie.nhb_ver:
                        # functie voor beheerder van een vereniging
                        # lid is overgestapt
                        let_op = 'LET OP: geen lid bij deze vereniging'

                self.stdout.write('  %s (%s) %s' % (account.username, account.volledige_naam(), let_op))
            # for
        # for

# end of file
