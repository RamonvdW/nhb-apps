# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BetalingenMutatie
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.models import F
from django.core.management.base import BaseCommand
from Betaal.models import (BetaalMutatie, BetaalActief, BetaalInstellingenVereniging,
                           BETAAL_MUTATIE_START_ONTVANGST, BETAAL_MUTATIE_START_RESTITUTIE,
                           BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED)
from Mailer.models import mailer_queue_email
from Overig.background_sync import BackgroundSync
import django.db.utils
import traceback
import datetime
import sys
from mollie.api.client import Client, RequestSetupError, RequestError
from mollie.api.error import ResponseError


class Command(BaseCommand):
    help = "Kalender mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__BETALINGEN_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

        try:
            self._instellingen_nhb = (BetaalInstellingenVereniging
                                      .objects
                                      .get(vereniging__ver_nr=settings.BETAAL_VIA_NHB_VER_NR))
        except BetaalInstellingenVereniging.DoesNotExist:
            self._instellingen_nhb = None

        # maak de Mollie client instantie aan
        # de API key zetten we later, afhankelijk van de vereniging waar we deze transactie voor doen
        self._mollie_client = Client()

        # limiteer hoeveel informatie er over ons platform doorgegeven wordt
        # verder wordt doorgegeven:
        #  - Mollie pakket versie: "2.12.0"
        #  - Python versie: "3.9.2"
        #  - OpenSSL versie: "OpenSSL 1.1.1n  15 Mar 2022"
        # standaard werd doorgegeven:
        #  - OS, hostname, kernel versie + distributie, machine arch
        self._mollie_client.UNAME = settings.NAAM_SITE      # MijnHandboogsport [test]

        self._mollie_webhook_url = reverse('Betaal:mollie-webhook')

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_mutatie_start_ontvangst(self, mutatie):
        instellingen = mutatie.ontvanger
        if instellingen.akkoord_via_nhb and self._instellingen_nhb:
            instellingen = self._instellingen_nhb

        beschrijving = mutatie.beschrijving
        bedrag_euro_str = str(mutatie.bedrag_euro)      # moet decimale punt geven

        # schakel de Mollie client over op de API key van deze vereniging
        # als de betaling via de NHB loopt, dan zijn dit al de instellingen van de NHB
        try:
            self._mollie_client.set_api_key(instellingen.mollie_api_key)
        except (RequestError, RequestSetupError) as exc:
            self.stderr.write('[ERROR] Unexpected exception from Mollie set API key: %s' % str(exc))
        else:
            # vraag Mollie om de betaling op te zetten
            # sla het payment_id op in de mutatie en in BetaalActief

            data = {
                'amount': {'currency': 'EUR', 'value': bedrag_euro_str},
                'description': beschrijving,
                'webhookUrl': self._mollie_webhook_url,
                'redirectUrl': mutatie.url_betaling_gedaan,
            }

            try:
                payment = self._mollie_client.payments.create(data)
            except (RequestError, RequestSetupError, ResponseError) as exc:
                self.stderr.write('[ERROR] Unexpected exception from Mollie create payment: %s' % str(exc))
            else:
                self.stdout.write('[DEBUG] Create payment response: %s' % repr(payment))
                payment_id = payment['id']

                mutatie.payment_id = payment_id
                mutatie.save(update_fields=['payment_id'])

                # houd de actieve betalingen bij
                BetaalActief(payment_id=payment_id).save()

    def _verwerk_mutatie_start_restitutie(self, mutatie):
        pass

    def _verwerk_mutatie_payment_status_changed(self, mutatie):
        pass

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == BETAAL_MUTATIE_START_ONTVANGST:
            self.stdout.write('[INFO] Verwerk mutatie %s: Start ontvangst' % mutatie.pk)
            self._verwerk_mutatie_start_ontvangst(mutatie)

        elif code == BETAAL_MUTATIE_START_RESTITUTIE:
            self.stdout.write('[INFO] Verwerk mutatie %s: Start restitutie' % mutatie.pk)
            self._verwerk_mutatie_start_restitutie(mutatie)

        elif code == BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED:
            self.stdout.write('[INFO] Verwerk mutatie %s: payment status changed' % mutatie.pk)
            self._verwerk_mutatie_payment_status_changed(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = BetaalMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste BetalingenMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (BetaalMutatie
                    .objects
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (BetaalMutatie
                    .objects
                    .all())

        mutatie_pks = qset.values_list('pk', flat=True)

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            #         en zodat we 1 plek hebben voor select/prefetch
            mutatie = (BetaalMutatie
                       .objects             # geen select_related nodig
                       .get(pk=pk))

            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste KalenderMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = BetaalMutatie.objects.count()
            if new_count != mutatie_count:
                mutatie_count = new_count
                self._verwerk_nieuwe_mutaties()
                now = datetime.datetime.now()

            # wacht 5 seconden voordat we opnieuw in de database kijken
            # het wachten kan onderbroken worden door een ping, als er een nieuwe mutatie toegevoegd is
            secs = (self.stop_at - now).total_seconds()
            if secs > 1:                                    # pragma: no branch
                timeout = min(5.0, secs)
                if self._sync.wait_for_ping(timeout):       # pragma: no branch
                    self._count_ping += 1                   # pragma: no cover
            else:
                # near the end
                break       # from the while                # pragma: no cover

            now = datetime.datetime.now()
        # while

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 15 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self.stop_at = (datetime.datetime.now()
                        + datetime.timedelta(minutes=duration)
                        - datetime.timedelta(seconds=15))

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):

        self._set_stop_time(**options)

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except django.db.utils.DataError as exc:        # pragma: no cover
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))
        except KeyboardInterrupt:                       # pragma: no cover
            pass

        self.stdout.write('[DEBUG] Aantal pings ontvangen: %s' % self._count_ping)

        self.stdout.write('Klaar')


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

    test uitvoeren met --debug-mode anders wordt er niets bijgehouden
"""

# end of file
