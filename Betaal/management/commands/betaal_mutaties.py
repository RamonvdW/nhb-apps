# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via BetaalMutatie
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.utils import OperationalError, IntegrityError
from django.core.management.base import BaseCommand
from Bestelling.operations.mutaties import bestel_mutatieverzoek_betaling_afgerond, bestel_betaling_is_gestart
from Betaal.definities import (BETAAL_MUTATIE_START_ONTVANGST, BETAAL_MUTATIE_START_RESTITUTIE,
                               BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED, BETAAL_PAYMENT_STATUS_MAXLENGTH,
                               BETAAL_PAYMENT_ID_MAXLENGTH, BETAAL_REFUND_ID_MAXLENGTH, BETAAL_BESCHRIJVING_MAXLENGTH,
                               BETAAL_KLANT_NAAM_MAXLENGTH, BETAAL_KLANT_ACCOUNT_MAXLENGTH,
                               BETAAL_CHECKOUT_URL_MAXLENGTH)
from Betaal.models import BetaalMutatie, BetaalActief, BetaalInstellingenVereniging, BetaalTransactie
from Mailer.operations import mailer_notify_internal_error
from Overig.background_sync import BackgroundSync
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
    help = "Betaal mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__BETAAL_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

        # cache de redelijke statische instellingen (voor 1 uur)
        try:
            self._instellingen_bond = (BetaalInstellingenVereniging
                                       .objects
                                       .get(vereniging__ver_nr=settings.BETAAL_VIA_BOND_VER_NR))
        except BetaalInstellingenVereniging.DoesNotExist:
            self._instellingen_bond = None

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

        self._mollie_webhook_url = settings.SITE_URL + reverse('Betaal:mollie-webhook')

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices=(1, 2, 5, 7, 10, 15, 20, 30, 45, 60),
                            help="Maximum aantal minuten actief blijven")
        parser.add_argument('--stop_exactly', type=int, default=None, choices=range(60),
                            help="Stop op deze minuut")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_mutatie_start_ontvangst(self, mutatie: BetaalMutatie):
        instellingen = mutatie.ontvanger
        if instellingen.akkoord_via_bond and self._instellingen_bond:
            instellingen = self._instellingen_bond

        beschrijving = mutatie.beschrijving
        bedrag_euro_str = str(mutatie.bedrag_euro)      # moet decimale punt geven

        # schakel de Mollie-client over op de API key van deze vereniging
        # als de betaling via de bond loopt, dan zijn dit al de instellingen van de bond
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
                    if len(obj.checkout_url) > BETAAL_CHECKOUT_URL_MAXLENGTH:
                        self.stderr.write('[ERROR] Checkout URL is te lang en wordt afgekapt op %s tekens' %
                                          BETAAL_CHECKOUT_URL_MAXLENGTH)
                        url_checkout = url_checkout[:BETAAL_CHECKOUT_URL_MAXLENGTH]

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
                                                ontvanger=instellingen)     # TODO: bij akkoord_via_bond...
                    if not is_created:
                        actief.log = "Reused\n"
                    actief.log += "[%s]: created\n" % timezone.localtime(timezone.now())
                    actief.log += json.dumps(payment, indent=4)
                    actief.log += '\n'
                    actief.payment_status = status
                    actief.save()

                    try:
                        bestelling = mutatie.bestelling_set.all()[0]
                    except IndexError:
                        # niet gevonden
                        pass
                    else:
                        bestel_betaling_is_gestart(bestelling, actief)

    def _verwerk_mutatie_start_restitutie(self, mutatie: BetaalMutatie):
        # FUTURE: implementeer restitutie
        pass

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

        te_ontvangen = obj.amount
        if te_ontvangen:
            te_ontvangen['field'] = 'amount / te_ontvangen'

        terugbetaald = obj.amount_refunded
        if terugbetaald:
            terugbetaald['field'] = 'amount_refunded / terugbetaald'

        beschikbaar = obj.amount_remaining
        if beschikbaar:
            beschikbaar['field'] = 'amount_remaining / beschikbaar'

        teruggevorderd = obj.amount_chargedback
        if teruggevorderd:
            teruggevorderd['field'] = 'amount_chargedback / teruggevorderd'

        verrekening = obj.settlement_amount
        if verrekening:
            verrekening['field'] = 'settlement_amount / verrekening'

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

        transactie.bedrag_euro_klant = te_ontvangen['bedrag']      # TODO: oud. Verwijderen?
        if verrekening:
            transactie.bedrag_euro_boeking = verrekening['bedrag']     # TODO: oud. Verwijderen?

        if obj.method and obj.details:
            methode = obj.method
            details = obj.details

            klant_naam = None
            klant_account = None

            # haal de gegevens van de betaler op
            if methode in ('ideal', 'bancontact', 'banktransfer', 'belfius', 'kbc', 'sofort', 'directdebit'):   # noqa
                # methode 1: "consumer" velden
                try:
                    klant_naam = details['consumerName']
                    if klant_naam:      # hanteer lege string, maar ook None (gezien bij bancontact)
                        klant_naam = klant_naam[:BETAAL_KLANT_NAAM_MAXLENGTH]
                    else:
                        klant_naam = '?'
                    klant_account = '%s (%s)' % (details['consumerAccount'], details['consumerBic'])
                    klant_account = klant_account[:BETAAL_KLANT_ACCOUNT_MAXLENGTH]
                except KeyError:
                    self.stderr.write('[ERROR] {payment_opslaan} Incomplete details over consumer: %s' % repr(details))
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
                    self.stderr.write('[ERROR] {payment_opslaan} Incomplete details voor paypal: %s' % repr(details))
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

    def _get_payment_refunds(self, payment_id):
        """ Haal bij Mollie de details op van de refunds voor de opgegeven payment_id
            Let op: Mollie API key moet al gezet zijn.
        """
        # vraag Mollie om de status van de betaling
        try:
            refunds = self._mollie_client.payment_refunds.with_parent_id(payment_id).list()
        except (RequestError, RequestSetupError, ResponseError, ResponseHandlingError) as exc:
            self.stderr.write(
                '[ERROR] {get_payment_refunds} Onverwachte fout van Mollie payment_refunds.list: %s' % str(exc))
        else:
            self.stdout.write('[INFO] {get_payment_refunds} Payment refunds ontvangen met count=%s' % refunds.count)

            for refund in refunds:
                self.stdout.write('[DEBUG] {get_payment_refunds} Refund: %s' % repr(refund))

                status = refund.status
                refund_id = refund.id       # re_Xxx
                amount = refund.settlement_amount
                beschrijving = refund.description
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
                            self.stderr.write('[ERROR] {get_payment_refunds} Currency not in EUR in %s' % repr(amount))
                        else:
                            bedrag = Decimal(amount['value'])

                    except (KeyError, DecimalException) as exc:
                        self.stderr.write('[ERROR] {get_payment_refunds} Probleem met value in %s (%s)' % (
                                            repr(amount), str(exc)))

                self.stdout.write(
                    '[DEBUG] {get_payment_refunds} refund_id=%s, status=%s, amount=%.2f, beschrijving=%s' % (
                                        repr(refund_id), repr(status), bedrag, repr(beschrijving)))

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

    def _verwerk_mutatie_payment_status_changed(self, mutatie: BetaalMutatie):
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
            # als de betaling via de bond loopt, dan zijn dit al de instellingen van de bond
            instellingen = actief.ontvanger
            if instellingen.akkoord_via_bond and self._instellingen_bond:
                instellingen = self._instellingen_bond

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

                    actief.log += "[%s] Mollie exception\n" % timezone.localtime(timezone.now())
                    actief.save(update_fields=['log'])
                else:
                    self.stdout.write('[DEBUG] Get payment response: %s' % repr(payment))

                    obj = Payment(payment)
                    status = obj.status
                    payment_id = obj.id

                    if payment_id is None or status is None:
                        self.stderr.write('[ERROR] Missing mandatory information in get payment response: %s, %s' % (
                                            repr(payment_id), repr(status)))

                    elif payment_id != actief.payment_id:
                        self.stderr.write('[ERROR] Mismatch in payment id: %s, %s' % (
                                            repr(payment_id), repr(actief.payment_id)))
                    else:
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

                        else:
                            # success

                            # haal eventuele restitutie transacties op
                            if transactie.bedrag_terugbetaald > 0.00:
                                self._get_payment_refunds(actief.payment_id)

                            self.stdout.write('[INFO] Payment %s status aangepast: %s --> %s' % (
                                actief.payment_id, repr(actief.payment_status), repr(status)))

                            actief.log += "[%s]: payment status %s --> %s\n" % (timezone.localtime(timezone.now()),
                                                                                repr(actief.payment_status),
                                                                                repr(status))
                            actief.log += payment_dump
                            actief.log += '\n'
                            actief.payment_status = status[:BETAAL_PAYMENT_STATUS_MAXLENGTH]
                            actief.save(update_fields=['payment_status', 'log'])

                            if obj.is_paid():
                                # print('is_paid() is True')
                                # TODO: na een refund blijft deze op 'paid' staan
                                # TODO: indien bedrag_terugbetaald > 0 dat refunds ophalen via Refunds API
                                actief.log += 'Betaling is voldaan\n\n'
                                actief.save(update_fields=['log'])

                                # betaling is afgerond en alle benodigde informatie staat nu in een transactie
                                bestel_mutatieverzoek_betaling_afgerond(actief, gelukt=True, snel=True)

                            elif obj.is_canceled() or obj.is_expired():
                                # print('is_cancelled of is_expired is True')
                                actief.log += 'Betaling is mislukt\n\n'
                                actief.save(update_fields=['log'])

                                # geef door dat de betaling mislukt is, zodat deze opnieuw opgestart kan worden
                                bestel_mutatieverzoek_betaling_afgerond(actief, gelukt=False, snel=True)

                            elif obj.is_pending() or obj.is_open():
                                # print('is_pending of is_open is True')
                                # do nothing
                                actief.log += 'Betaling staat nog open\n\n'
                                actief.save(update_fields=['log'])

                            elif obj.is_failed():
                                # print('is_failed is True')
                                # verwachting: Mollie stuurt gebruiker terug naar kies-betaalmethode
                                # TODO: voor sommige betaalmethodes zijn 'failure reasons' beschikbaar onder details
                                actief.log += 'Betaling is mislukt\n\n'
                                actief.save(update_fields=['log'])

    def _verwerk_mutatie(self, mutatie: BetaalMutatie):
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
        except BetaalMutatie.DoesNotExist:      # pragma: no cover
            # alle mutatie records zijn verwijderd
            return
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk is not None:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste BetaalMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (BetaalMutatie
                    .objects
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (BetaalMutatie
                    .objects
                    .filter(is_verwerkt=False,
                            pogingen__lt=MAX_POGINGEN))

        mutatie_pks = qset.values_list('pk', flat=True)     # deferred

        self._hoogste_mutatie_pk = mutatie_latest.pk

        work_count = 0
        for pk in mutatie_pks:
            # we halen de records hier 1 voor 1 op
            # zodat we verse informatie hebben inclusief de vorige mutatie
            # en zodat we 1 plek hebben voor select/prefetch
            mutatie = (BetaalMutatie
                       .objects
                       .select_related('ontvanger')
                       .get(pk=pk))

            if not mutatie.is_verwerkt and mutatie.pogingen < MAX_POGINGEN:
                mutatie.pogingen += 1
                mutatie.save(update_fields=['pogingen'])

                self._verwerk_mutatie(mutatie)

                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                work_count += 1
        # for

        if work_count:
            self.stdout.write('[INFO] nieuwe hoogste BetaalMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] %s BetaalMutaties verwerkt in %s seconden' % (work_count, klaar - begin))

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
        duration = options['duration']
        stop_minute = options['stop_exactly']

        now = datetime.datetime.now()
        self.stop_at = now + datetime.timedelta(minutes=duration)

        if isinstance(stop_minute, int):
            delta = stop_minute - now.minute
            if delta < 0:
                delta += 60
            if delta != 0:    # avoid stopping in start minute
                stop_at_exact = now + datetime.timedelta(minutes=delta)
                stop_at_exact -= datetime.timedelta(seconds=self.stop_at.second,
                                                    microseconds=self.stop_at.microsecond)
                self.stdout.write('[INFO] Calculated stop at is %s' % stop_at_exact)
                if stop_at_exact < self.stop_at:
                    # run duration passes the requested stop minute
                    self.stop_at = stop_at_exact

        if options['quick']:        # pragma: no branch
            # test moet snel stoppen dus interpreteer duration in seconden
            if options['duration'] == 60:
                # speciale testcase
                self._hoogste_mutatie_pk = 0
                duration = 2
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):

        self._set_stop_time(**options)

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except (OperationalError, IntegrityError) as exc:  # pragma: no cover
            # OperationalError treed op bij system shutdown, als database gesloten wordt
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout in betaal_mutaties: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

        except KeyboardInterrupt:                       # pragma: no cover
            pass

        except Exception as exc:
            # schrijf in de output
            tups = sys.exc_info()
            lst = traceback.format_tb(tups[2])
            tb = traceback.format_exception(*tups)

            tb_msg_start = 'Onverwachte fout tijdens betaal_mutaties\n'
            tb_msg_start += '\n'

            self.stderr.write('[ERROR] Onverwachte fout tijdens betaal_mutaties: ' + str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))

            # stuur een mail naar de ontwikkelaars
            # reduceer tot de nuttige regels
            tb = [line for line in tb if '/site-packages/' not in line]
            tb_msg = tb_msg_start + '\n'.join(tb)

            # deze functie stuurt maximaal 1 mail per dag over hetzelfde probleem
            mailer_notify_internal_error(tb_msg)

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

    test uitvoeren met DEBUG=True via --settings=SiteMain.settings_dev anders wordt er niets bijgehouden
"""

# end of file
