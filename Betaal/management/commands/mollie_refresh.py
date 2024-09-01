# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BetaalMutatie
"""
from django.conf import settings
from django.utils import timezone
from django.db.utils import OperationalError, IntegrityError
from django.core.management.base import BaseCommand
from Bestelling.models import Bestelling
from Betaal.definities import (BETAAL_REFUND_ID_MAXLENGTH, BETAAL_PAYMENT_STATUS_MAXLENGTH,
                               BETAAL_BESCHRIJVING_MAXLENGTH, BETAAL_PAYMENT_ID_MAXLENGTH,
                               BETAAL_KLANT_ACCOUNT_MAXLENGTH, BETAAL_KLANT_NAAM_MAXLENGTH)
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie, BetaalActief
from mollie.api.client import Client, RequestSetupError, RequestError
from mollie.api.error import ResponseError, ResponseHandlingError
from mollie.api.objects.payment import Payment
from decimal import Decimal, DecimalException
import traceback
import datetime
import json
import sys

# maximum aantal pogingen om een mutatie te verwerken
MAX_POGINGEN = 5


class Command(BaseCommand):
    help = "Devtest Mollie"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        # maak de Mollie-client instantie aan
        # de API key zetten we later, afhankelijk van de vereniging waar we deze transactie voor doen
        self._mollie_client = Client(api_endpoint=settings.BETAAL_API_URL)

        # begrens hoeveel informatie er over ons platform doorgegeven wordt
        # verder wordt doorgegeven:
        #  - Mollie pakket versie: "2.12.0"
        #  - Python versie: "3.9.2"
        #  - OpenSSL versie: "OpenSSL 1.1.1n  15 Mar 2022"
        # standaard werd doorgegeven:
        #  - OS, hostname, kernel versie + distributie, machine arch
        self._mollie_client.UNAME = settings.NAAM_SITE      # MijnHandboogsport [test]

    def add_arguments(self, parser):
        parser.add_argument('ver_nr', type=int)

    @staticmethod
    def _koppel_bestel_transacties():
        for bestelling in Bestelling.objects.exclude(betaal_mutatie=None).select_related('betaal_mutatie'):
            payment_id = bestelling.betaal_mutatie.payment_id
            transacties = BetaalTransactie.objects.filter(payment_id=payment_id)
            bestelling.transacties.set(transacties)
        # for

    def _get_all_refunds(self):
        """ Haal bij Mollie de details op van de refunds voor de opgegeven payment_id
            Let op: Mollie API key moet al gezet zijn.
        """
        # vraag Mollie om alle refunds
        try:
            refunds = self._mollie_client.refunds.list(limit=250)
        except (RequestError, RequestSetupError, ResponseError, ResponseHandlingError) as exc:
            self.stderr.write('[ERROR] Unexpected exception from Mollie refunds.list: %s' % str(exc))
        else:
            self.stdout.write('[DEBUG] List refunds response: count=%s' % refunds.count)

            for refund in refunds:
                # self.stdout.write('[DEBUG] Refund: %s' % repr(refund))

                # mollie.api.objects.refund.Refund
                status = refund.status
                refund_id = refund.id       # re_Xxx
                amount = refund.settlement_amount
                beschrijving = refund.description
                payment_id = refund.payment_id

                try:
                    created_at = datetime.datetime.strptime(refund.created_at, '%Y-%m-%dT%H:%M:%S%z')
                except ValueError:
                    created_at = timezone.now()
                    self.stderr.write(
                        '[ERROR] {get_payment_refunds} Conversie createdAt %s failed' % repr(refund.created_at))

                # controleer eenheid (euro) en converteer bedrag naar Decimal
                bedrag = 0.0
                if amount:
                    try:
                        if amount['currency'] != 'EUR':
                            self.stderr.write('[ERROR] {refund} Currency not in EUR in %s' % repr(amount))
                        else:
                            bedrag = Decimal(amount['value'])

                    except (KeyError, DecimalException) as exc:
                        self.stderr.write('[ERROR] {refund} Probleem met value in %s (%s)' % (repr(amount),
                                                                                              str(exc)))

                # self.stdout.write(
                #     '[DEBUG] payment_id=%s, refund_id=%s, status=%s, amount=%.2f, created_at=%s, beschrijving=%s' % (
                #         repr(payment_id), repr(refund_id), repr(status), bedrag, created_at, repr(beschrijving)))

                # als deze al bestaat, dan niet opnieuw aanmaken
                _ = BetaalTransactie.objects.get_or_create(
                                    when=created_at,
                                    payment_id=payment_id,
                                    is_restitutie=True,
                                    beschrijving=beschrijving[:BETAAL_BESCHRIJVING_MAXLENGTH],
                                    klant_naam='',
                                    klant_account='',
                                    refund_id=refund_id[:BETAAL_REFUND_ID_MAXLENGTH],
                                    refund_status=status[:BETAAL_PAYMENT_STATUS_MAXLENGTH],
                                    bedrag_refund=bedrag)
            # for

    def _payment_opslaan(self, obj: Payment) -> None | BetaalTransactie:
        """
            Maak een BetaalTransactie aan uit het Mollie Payment object en geeft deze terug.
            Geeft None terug als er een probleem was.
        """
        # transactie geschiedenis aanmaken
        transactie = BetaalTransactie(
                            when=timezone.now(),
                            is_handmatig=False,
                            payment_id=obj.id[:BETAAL_PAYMENT_ID_MAXLENGTH],
                            beschrijving=str(obj.description)[:BETAAL_BESCHRIJVING_MAXLENGTH],
                            is_restitutie=False,
                            payment_status=obj.status)

        if obj.amount:
            obj.amount['field'] = 'amount / te_ontvangen'
        if obj.amount_refunded:
            obj.amount_refunded['field'] = 'amount_refunded / terugbetaald'
        if obj.amount_remaining:
            obj.amount_remaining['field'] = 'amount_remaining / beschikbaar'
        if obj.amount_chargedback:
            obj.amount_chargedback['field'] = 'amount_chargedback / teruggevorderd'  # noqa
        if obj.settlement_amount:
            obj.settlement_amount['field'] = 'settlement_amount / euro_boeking'

        te_ontvangen = obj.amount
        terugbetaald = obj.amount_refunded
        beschikbaar = obj.amount_remaining
        teruggevorderd = obj.amount_chargedback
        verrekening = obj.settlement_amount

        # controleer eenheid (euro) en converteer bedrag naar Decimal
        for amount in (te_ontvangen, terugbetaald, beschikbaar, teruggevorderd, verrekening):
            if amount:
                try:
                    if amount['currency'] != 'EUR':
                        self.stderr.write('[ERROR] {payment_opslaan} Currency not in EUR in %s' % repr(amount))
                        return None

                    amount['bedrag'] = Decimal(amount['value'])

                except (KeyError, DecimalException) as exc:
                    self.stderr.write('[ERROR] {payment_opslaan} Probleem met value in %s (%s)' % (repr(amount),
                                                                                                   str(exc)))
                    return None

        transactie.bedrag_te_ontvangen = te_ontvangen['bedrag']
        if terugbetaald:
            transactie.bedrag_terugbetaald = terugbetaald['bedrag']
        if beschikbaar:
            transactie.bedrag_beschikbaar = beschikbaar['bedrag']
        if teruggevorderd:
            transactie.teruggevorderd = teruggevorderd['bedrag']

        transactie.bedrag_euro_klant = te_ontvangen['bedrag']  # TODO: oud. Verwijderen?
        if verrekening:
            transactie.bedrag_euro_boeking = verrekening['bedrag']  # TODO: oud. Verwijderen?

        if obj.method and obj.details:
            methode = obj.method
            details = obj.details

            klant_naam = None
            klant_account = None

            # haal de gegevens van de betaler op
            if methode in ('ideal', 'bancontact', 'belfius', 'kbc', 'sofort', 'directdebit'):  # noqa
                # methode 1: "consumer" velden
                try:
                    klant_naam = details['consumerName']
                    if klant_naam:  # hanteer lege string, maar ook None (gezien bij bancontact)
                        klant_naam = klant_naam[:BETAAL_KLANT_NAAM_MAXLENGTH]
                    else:
                        klant_naam = '?'
                    klant_account = '%s (%s)' % (details['consumerAccount'], details['consumerBic'])
                    klant_account = klant_account[:BETAAL_KLANT_ACCOUNT_MAXLENGTH]
                except KeyError:
                    self.stderr.write(
                        '[ERROR] {payment_opslaan} Incomplete details over consumer (methodr=%s): %s' % (repr(methode),
                                                                                                         repr(details)))
                    return None

            elif methode == 'creditcard':
                # methode 2: credit cards (inclusief apple pay)
                try:
                    klant_naam = details['cardHolder']
                    klant_account = '%s %s %s' % (details['cardCountryCode'], details['cardLabel'],
                                                  details['cardNumber'])
                except KeyError:
                    self.stderr.write('[ERROR] {payment_opslaan} Incomplete details voor card: %s' % repr(details))
                    return None

            elif methode == 'paypal':
                # methode 3: paypal
                try:
                    klant_naam = details['consumerName']
                    klant_account = '%s %s %s' % (details['consumerAccount'],
                                                  details['paypalReference'], details['paypalPayerId'])
                except KeyError:
                    self.stderr.write(
                        '[ERROR] {payment_opslaan} Incomplete details voor paypal: %s' % repr(details))
                    return None

            elif methode == 'banktransfer':
                # methode 4: "bank" velden
                try:
                    klant_naam = details['bankName']
                    if klant_naam:  # hanteer lege string, maar ook None (gezien bij bancontact)
                        klant_naam = klant_naam[:BETAAL_KLANT_NAAM_MAXLENGTH]
                    else:
                        klant_naam = '?'
                    klant_account = '%s (%s)' % (details['bankAccount'], details['bankBic'])
                    klant_account = klant_account[:BETAAL_KLANT_ACCOUNT_MAXLENGTH]
                except KeyError:
                    self.stderr.write(
                        '[ERROR] {payment_opslaan} Incomplete details voor  banktransfer: %s' % repr(details))
                    return None

            if klant_naam is None or klant_account is None:
                self.stderr.write('[ERROR] {payment_opslaan} Incomplete informatie over betaler: %s, %s' % (
                    repr(klant_naam), repr(klant_account)))
                return None

            transactie.klant_naam = klant_naam
            transactie.klant_account = klant_account

        transactie.save()

        # bestel_mutaties vindt de transacties die bij een bestelling horen d.m.v. het payment_id
        # en legt de koppeling aan Bestelling.transacties
        return transactie

    def _refresh_payments(self, ver_nr):
        for actief in BetaalActief.objects.filter(ontvanger__vereniging__ver_nr=ver_nr):

            actief.log += '[%s] mollie_refresh\n' % timezone.localtime(timezone.now())

            # vraag Mollie om de status van de betaling
            try:
                payment = self._mollie_client.payments.get(actief.payment_id)
            except (RequestError, RequestSetupError, ResponseError, ResponseHandlingError) as exc:
                self.stderr.write('[ERROR] Unexpected exception from Mollie payments.get: %s' % str(exc))
                continue

            obj = Payment(payment)
            status = obj.status
            payment_id = obj.id

            if payment_id is None or status is None:
                self.stderr.write('[ERROR] Missing mandatory information in get payment response: %s, %s' % (
                    repr(payment_id), repr(status)))
                continue

            if payment_id != actief.payment_id:
                self.stderr.write('[ERROR] Mismatch in payment id: %s, %s' % (repr(payment_id),
                                                                              repr(actief.payment_id)))
                continue

            # remove some keys we don't need in the log
            try:
                del payment['webhookUrl']
                del payment['redirectUrl']
                del payment['_links']['dashboard']
                del payment['_links']['self']
                del payment['_links']['documentation']
            except KeyError:
                pass

            # maak een tekst vertaling
            # (_payment_opslaan maakt wijzigingen)
            payment_dump = json.dumps(payment, indent=4)

            transactie = self._payment_opslaan(obj)

            if transactie is None:
                # probleem
                self.stdout.write('[WARNING] Payment %s bevat een probleem' % actief.payment_id)
                continue

            # success

            self.stdout.write('[INFO] Payment %s status aangepast: %s --> %s' % (
                                actief.payment_id, repr(actief.payment_status), repr(status)))

            actief.log += "[%s]: payment status %s --> %s\n" % (timezone.localtime(timezone.now()),
                                                                repr(actief.payment_status),
                                                                repr(status))
            actief.log += payment_dump
            actief.log += '\n'
            actief.payment_status = status[:BETAAL_PAYMENT_STATUS_MAXLENGTH]
            actief.save(update_fields=['payment_status', 'log'])
        # for

    def handle(self, *args, **options):

        ver_nr = options['ver_nr']
        self.stdout.write('[INFO] ver_nr: %s' % ver_nr)

        try:
            instellingen = (BetaalInstellingenVereniging.objects.get(vereniging__ver_nr=ver_nr))
        except BetaalInstellingenVereniging.DoesNotExist:
            self.stderr.write('[ERROR] Kan BetaalInstellingenVereniging voor vereniging %s niet vinden')
            return

        try:
            self._mollie_client.set_api_key(instellingen.mollie_api_key)
        except (RequestError, RequestSetupError) as exc:
            self.stderr.write('[ERROR] Unexpected exception from Mollie set API key: %s' % str(exc))
            return

        # vang generieke fouten af
        try:
            self._get_all_refunds()
            self._refresh_payments(ver_nr)
            self._koppel_bestel_transacties()
        except (OperationalError, IntegrityError) as exc:  # pragma: no cover
            # OperationalError treed op bij system shutdown, als database gesloten wordt
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout in mollie_refunds_ophalen: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

        except KeyboardInterrupt:                       # pragma: no cover
            pass

        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])

            self.stderr.write('[ERROR] Onverwachte fout tijdens mollie_refunds_ophalen: ' + str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

        self.stdout.write('Klaar')

# end of file
