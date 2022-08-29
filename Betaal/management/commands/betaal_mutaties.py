# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BetaalMutatie
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.utils import DataError, OperationalError, IntegrityError
from django.core.management.base import BaseCommand
from Bestel.mutaties import bestel_mutatieverzoek_betaling_afgerond, bestel_betaling_is_gestart
from Betaal.models import (BetaalMutatie, BetaalActief, BetaalInstellingenVereniging, BetaalTransactie,
                           BETAAL_MUTATIE_START_ONTVANGST, BETAAL_MUTATIE_START_RESTITUTIE,
                           BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED, BETAAL_PAYMENT_STATUS_MAXLENGTH,
                           BETAAL_PAYMENT_ID_MAXLENGTH, BETAAL_BESCHRIJVING_MAXLENGTH,
                           BETAAL_KLANT_NAAM_MAXLENGTH, BETAAL_KLANT_ACCOUNT_MAXLENGTH)
from Overig.background_sync import BackgroundSync
from mollie.api.client import Client, RequestSetupError, RequestError
from mollie.api.error import ResponseError, ResponseHandlingError
from mollie.api.objects.payment import Payment
from decimal import Decimal, DecimalException
import traceback
import datetime
import json
import sys


class Command(BaseCommand):
    help = "Betaal mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__BETAAL_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

        # cache de redelijke statische instellingen (voor 1 uur)
        try:
            self._instellingen_nhb = (BetaalInstellingenVereniging
                                      .objects
                                      .get(vereniging__ver_nr=settings.BETAAL_VIA_NHB_VER_NR))
        except BetaalInstellingenVereniging.DoesNotExist:
            self._instellingen_nhb = None

        # maak de Mollie-client instantie aan
        # de API key zetten we later, afhankelijk van de vereniging waar we deze transactie voor doen
        self._mollie_client = Client(api_endpoint=settings.BETAAL_API)

        # begrens hoeveel informatie er over ons platform doorgegeven wordt
        # verder wordt doorgegeven:
        #  - Mollie pakket versie: "2.12.0"
        #  - Python versie: "3.9.2"
        #  - OpenSSL versie: "OpenSSL 1.1.1n  15 Mar 2022"
        # standaard werd doorgegeven:
        #  - OS, hostname, kernel versie + distributie, machine arch
        self._mollie_client.UNAME = settings.NAAM_SITE      # MijnHandboogsport [test]

        self._mollie_webhook_url = settings.SITE_URL + reverse('Betaal:mollie-webhook')

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

        # schakel de Mollie-client over op de API key van deze vereniging
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
            except (RequestError, RequestSetupError, ResponseError, ResponseHandlingError) as exc:
                self.stderr.write('[ERROR] Unexpected exception from Mollie payments.create: %s' % str(exc))
            else:
                self.stdout.write('[DEBUG] Create payment response: %s' % repr(payment))

                obj = Payment(payment)
                payment_id = obj.id
                url_checkout = obj.checkout_url
                status = obj.status

                if payment_id is None or url_checkout is None or status is None:
                    self.stderr.write('[ERROR] Missing mandatory information in create payment response: %s, %s, %s' % (
                                        repr(payment_id), repr(url_checkout), repr(status)))
                elif not obj.is_open():
                    self.stderr.write('[ERROR] Onverwachte status %s in create payment response' % repr(status))
                else:
                    # het is gelukt om de betaling op te starten
                    mutatie.payment_id = payment_id
                    mutatie.url_checkout = url_checkout
                    mutatie.save(update_fields=['payment_id', 'url_checkout'])

                    # remove some keys we don't need in the log
                    try:
                        del payment['webhookUrl']
                        del payment['redirectUrl']
                        del payment['_links']['dashboard']
                        # del payment['_links']['self']
                        del payment['_links']['documentation']
                    except KeyError:
                        pass

                    # houd de actieve betalingen bij
                    actief, is_created = BetaalActief.objects.get_or_create(
                                                payment_id=payment_id,
                                                ontvanger=instellingen)     # TODO: bij akkoord_via_nhb...
                    if not is_created:
                        actief.log = "Reused\n"
                    actief.log += "[%s]: created\n" % timezone.localtime(timezone.now())
                    actief.log += json.dumps(payment)
                    actief.log += '\n'
                    actief.payment_status = status
                    actief.save()

                    try:
                        bestelling = mutatie.bestelling_set.all()[0]
                    except KeyError:        # TODO: correct exceptie invullen
                        pass
                    else:
                        bestel_betaling_is_gestart(bestelling, actief)

    def _verwerk_mutatie_start_restitutie(self, mutatie):
        # TODO: implementeer restitutie
        pass

    def _maak_transactie(self, obj, payment_id):
        description = str(obj.description)  # ensure string (just in case)
        euro_klant = obj.amount
        euro_boeking = obj.settlement_amount
        details = obj.details
        methode = obj.method

        if euro_klant is None or euro_boeking is None or details is None or methode is None:
            self.stderr.write('[ERROR] {maak_transactie} Missing field: %s, %s, %s, %s' % (
                                repr(euro_klant), repr(euro_boeking), repr(details), repr(methode)))
            return False

        try:
            if euro_klant['currency'] != 'EUR' or euro_boeking['currency'] != 'EUR':
                self.stderr.write('[ERROR] {maak_transactie} Currency not in EUR: %s, %s' % (
                                    repr(euro_klant), repr(euro_boeking)))
                return False

            bedrag_klant = Decimal(euro_klant['value'])
            bedrag_boeking = Decimal(euro_boeking['value'])
        except (KeyError, DecimalException) as exc:
            self.stderr.write('[ERROR] {maak_transactie} Probleem met de bedragen: %s, %s (%s)' % (
                                repr(euro_klant), repr(euro_boeking), str(exc)))
            return False

        klant_naam = None
        klant_account = None

        # haal de gegevens van de betaler op
        # FUTURE: Paypal
        if methode in ('ideal', 'bancontact', 'banktransfer', 'belfius', 'kbc', 'sofort', 'directdebit'):
            # methode 1: "consumer" velden
            try:
                klant_naam = details['consumerName'][:BETAAL_KLANT_NAAM_MAXLENGTH]
                klant_account = '%s (%s)' % (details['consumerAccount'], details['consumerBic'])
                klant_account = klant_account[:BETAAL_KLANT_ACCOUNT_MAXLENGTH]
            except KeyError:
                self.stderr.write('[ERROR] {maak_transactie} Incomplete details over consumer: %s' % repr(details))
                return False

        elif methode in ('creditcard',):
            # methode 2: credit cards (inclusief apple pay)
            try:
                klant_naam = details['cardHolder']
                klant_account = '%s %s %s' % (details['cardCountryCode'], details['cardLabel'], details['cardNumber'])
            except KeyError:
                self.stderr.write('[ERROR] {maak_transactie} Incomplete details voor card: %s' % repr(details))
                return False

        if klant_naam is None or klant_account is None:
            self.stderr.write('[ERROR] {maak_transactie} Incomplete informatie over betaler: %s, %s' % (
                                repr(klant_naam), repr(klant_account)))
            return False

        # transactie geschiedenis aanmaken
        BetaalTransactie(
                payment_id=payment_id[:BETAAL_PAYMENT_ID_MAXLENGTH],
                when=timezone.now(),
                beschrijving=description[:BETAAL_BESCHRIJVING_MAXLENGTH],
                is_restitutie=False,
                bedrag_euro_klant=bedrag_klant,
                bedrag_euro_boeking=bedrag_boeking,
                klant_naam=klant_naam,
                klant_account=klant_account).save()

        # bestel_mutaties vind de transacties die bij een bestelling horen d.m.v. het payment_id
        # en legt de koppeling aan Bestelling.transacties
        return True

    def _verwerk_mutatie_payment_status_changed(self, mutatie):
        """ Een voor ons bekende transactie is van status gewijzigd
            Haal de laatste stand van zaken op bij Mollie.
        """

        # zoek de bijbehorende API key op
        try:
            actief = BetaalActief.objects.get(payment_id=mutatie.payment_id)
        except BetaalActief.DoesNotExist:
            # niet (meer) gevonden --> we kunnen niets doen
            pass
        else:
            actief.log += '\n\n'

            # schakel de Mollie client over op de API key van deze vereniging
            # als de betaling via de NHB loopt, dan zijn dit al de instellingen van de NHB
            instellingen = actief.ontvanger
            if instellingen.akkoord_via_nhb and self._instellingen_nhb:
                instellingen = self._instellingen_nhb

            try:
                self._mollie_client.set_api_key(instellingen.mollie_api_key)
            except (RequestError, RequestSetupError) as exc:
                self.stderr.write('[ERROR] Unexpected exception from Mollie set API key: %s' % str(exc))
            else:
                # vraag Mollie om de status van de betaling
                try:
                    payment = self._mollie_client.payments.get(actief.payment_id)
                except (RequestError, RequestSetupError, ResponseError, ResponseHandlingError) as exc:
                    self.stderr.write('[ERROR] Unexpected exception from Mollie payments.get: %s' % str(exc))

                    actief.log += "[%s]: Mollie exception\n" % timezone.localtime(timezone.now())
                    actief.save(update_fields=['log'])
                else:
                    self.stdout.write('[DEBUG] Get payment response: %s' % repr(payment))

                    obj = Payment(payment)
                    status = obj.status
                    payment_id = obj.id

                    if payment_id is None or status is None:
                        self.stderr.write('[ERROR] Missing mandatory information in get payment response: %s, %s' % (
                                            repr(payment_id), repr(status)))

                    elif payment_id != mutatie.payment_id:
                        self.stderr.write('[ERROR] Mismatch in payment id: %s, %s' % (
                                            repr(payment_id), repr(mutatie.payment_id)))
                    else:
                        # remove some keys we don't need in the log
                        try:
                            del payment['webhookUrl']
                            del payment['redirectUrl']
                            del payment['_links']['dashboard']
                            # del payment['_links']['self']
                            del payment['_links']['documentation']
                        except KeyError:
                            pass

                        self.stdout.write('[INFO] Payment %s status aangepast: %s --> %s' % (actief.payment_id,
                                                                                             actief.payment_status,
                                                                                             status))

                        actief.log += "[%s]: payment status %s --> %s\n" % (timezone.localtime(timezone.now()),
                                                                            actief.payment_status,
                                                                            status)
                        actief.log += json.dumps(payment)
                        actief.log += '\n'
                        actief.payment_status = status[:BETAAL_PAYMENT_STATUS_MAXLENGTH]
                        actief.save(update_fields=['payment_status', 'log'])

                        if obj.is_paid():
                            actief.log += 'Betaling is voldaan\n\n'
                            actief.save(update_fields=['log'])

                            if self._maak_transactie(obj, payment_id):
                                # betaling is afgerond en alle benodigde informatie staat nu in een transactie
                                bestel_mutatieverzoek_betaling_afgerond(actief, gelukt=True, snel=True)

                        elif obj.is_canceled() or obj.is_expired():
                            actief.log += 'Betaling is mislukt\n\n'
                            actief.save(update_fields=['log'])

                            # geef door dat de betaling mislukt is, zodat deze opnieuw opgestart kan worden
                            bestel_mutatieverzoek_betaling_afgerond(actief, gelukt=False, snel=True)
                        elif obj.is_pending() or obj.is_open():
                            # do nothing
                            pass
                        elif obj.is_failed():
                            # verwachting: Mollie stuurt gebruiker terug naar kies-betaalmethode
                            # voor sommige betaalmethodes zijn 'failure reasons' beschikbaar onder details
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

        try:
            mutatie_latest = BetaalMutatie.objects.latest('pk')
        except BetaalMutatie.DoesNotExist:
            # alle mutatie records zijn verwijderd
            return
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste BetaalMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (BetaalMutatie
                    .objects
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (BetaalMutatie
                    .objects
                    .all())         # deferred

        mutatie_pks = qset.values_list('pk', flat=True)     # deferred

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # we halen de records hier 1 voor 1 op
            # zodat we verse informatie hebben inclusief de vorige mutatie
            # en zodat we 1 plek hebben voor select/prefetch
            mutatie = (BetaalMutatie
                       .objects
                       .select_related('ontvanger')
                       .get(pk=pk))

            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste BetaalMutatie pk is %s' % self._hoogste_mutatie_pk)

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
        except (DataError, OperationalError, IntegrityError) as exc:  # pragma: no cover
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
