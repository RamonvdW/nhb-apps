# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" management commando dat 1x per dag gedraaid wordt (crontab) om een e-mail te sturen als herinnering
    aan producten die nog in het mandje liggen maar niet omgezet zijn in een bestelling.
"""

from django.core.management.base import BaseCommand
from Bestelling.models import Bestelling
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_RESTITUTIE, TRANSACTIE_TYPE_HANDMATIG
from Betaal.models import BetaalTransactie


class Command(BaseCommand):

    help = "Koppel betaling en restitutie aan juist bestelling"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

    def _amend_overboekingen(self):
        for transactie in BetaalTransactie.objects.filter(transactie_type=TRANSACTIE_TYPE_HANDMATIG):
            count = transactie.bestelling_set.count()
            if count != 1:
                print('[ERROR] BetaalTransactie pk=%s heeft raar aantal bestellingen: %s' % (transactie.pk, count))
                for bestelling in transactie.bestelling_set.all():
                    print('    bestelling: %s' % bestelling)
            else:
                bestelling = transactie.bestelling_set.first()
                mh_nr = bestelling.mh_bestel_nr()
                if mh_nr not in transactie.beschrijving:
                    print('Adding %s to transactie %s beschrijving' % (mh_nr, transactie.pk))
                    transactie.beschrijving += ' voor ' + mh_nr
                    transactie.save(update_fields=['beschrijving'])
        # for

    def _zoek_transacties(self, mh_nr: str):
        return BetaalTransactie.objects.filter(beschrijving__contains=mh_nr).exclude(transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE)

    def _zoek_restituties(self, tr_nrs: list):
        return BetaalTransactie.objects.filter(transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE, payment_id__in=tr_nrs)

    def _check_bestellingen(self):
        for bestelling in Bestelling.objects.prefetch_related('transacties').order_by('pk'):
            mh_nr = bestelling.mh_bestel_nr()

            pks = list(bestelling.transacties.values_list('pk', flat=True))

            tr_nrs = list()
            transacties = self._zoek_transacties(mh_nr)
            for transactie in transacties:
                # print('  +%s' % transactie)
                if transactie.payment_id:
                    tr_nrs.append(transactie.payment_id)
                try:
                    pks.remove(transactie.pk)
                except ValueError:
                    print(mh_nr)
                    print('  toevoegen: %s' % transactie)
                    bestelling.transacties.add(transactie)
            # for
            # print('  tr_nrs: %s' % repr(tr_nrs))

            transacties = self._zoek_restituties(tr_nrs)
            for transactie in transacties:
                # print('  -%s' % transactie)
                try:
                    pks.remove(transactie.pk)
                except ValueError:
                    print(mh_nr)
                    print('  toevoegen: %s' % transactie)
                    bestelling.transacties.add(transactie)
            # for

            if len(pks) > 0:
                print(mh_nr)
                print('  left over: %s' % repr(pks))

        # for

    def handle(self, *args, **options):
        self._amend_overboekingen()
        self._check_bestellingen()


# end of file
