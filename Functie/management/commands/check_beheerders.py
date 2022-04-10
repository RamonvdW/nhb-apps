# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# toon de beheerders van elke functies en eventuele bijzonderheden

from django.core.management.base import BaseCommand
from Functie.models import Functie


class Command(BaseCommand):
    help = "Check aan de functies gekoppelde beheerders"

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help="Toon alle")

    def handle(self, *args, **options):

        toon_alle = options['all']

        for functie in (Functie
                        .objects
                        .prefetch_related('accounts')
                        .select_related('nhb_ver')
                        .order_by('nhb_ver', 'rol')):

            functie_getoond = False
            for account in functie.accounts.prefetch_related('sporter_set').all():
                let_op = ''
                try:
                    sporter = account.sporter_set.prefetch_related('bij_vereniging').all()[0]
                except IndexError:
                    sporter = None
                    let_op = 'LET OP: geen koppeling met NHB lid'
                else:
                    if not sporter.bij_vereniging or not sporter.is_actief_lid:
                        # deze melding komt na 15 januari
                        let_op = 'LET OP: geen lid meer bij een vereniging'
                    elif functie.nhb_ver and sporter.bij_vereniging != functie.nhb_ver:
                        # functie voor beheerder van een vereniging
                        # lid is overgestapt
                        let_op = 'LET OP: geen lid bij deze vereniging'

                if toon_alle or len(let_op) > 0:
                    if not functie_getoond:
                        self.stdout.write('Functie: %s' % functie.beschrijving)
                        functie_getoond = True

                    self.stdout.write('  %s (%s) %s' % (account.username, account.volledige_naam(), let_op))
            # for
        # for

# end of file
