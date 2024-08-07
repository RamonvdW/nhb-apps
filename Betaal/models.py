# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils.timezone import localtime
from Account.models import Account
from Betaal.definities import (MOLLIE_API_KEY_MAXLENGTH, BETAAL_PAYMENT_ID_MAXLENGTH, BETAAL_PAYMENT_STATUS_MAXLENGTH,
                               BETAAL_BESCHRIJVING_MAXLENGTH, BETAAL_KLANT_NAAM_MAXLENGTH,
                               BETAAL_KLANT_ACCOUNT_MAXLENGTH, BETAAL_MUTATIE_TO_STR)
from Vereniging.models import Vereniging


class BetaalInstellingenVereniging(models.Model):

    # bij welke vereniging hoort deze informatie?
    vereniging = models.OneToOneField(Vereniging, on_delete=models.CASCADE)

    # de API key van deze vereniging voor Mollie
    mollie_api_key = models.CharField(max_length=MOLLIE_API_KEY_MAXLENGTH, blank=True)

    # mag deze vereniging betalingen ontvangen via de bond
    akkoord_via_bond = models.BooleanField(default=False)

    def obfuscated_mollie_api_key(self):
        # mollie key heeft een prefix live_ of test_ gevolgd door iets van 20 letters/cijfers
        # verwijder het middelste stuk
        key = self.mollie_api_key

        # laat aan beide kanten 20% van de sleutel zien
        sub = len(key) - 5
        sub = int(sub / 5)
        sub = max(sub, 1)       # prevent 0

        key = key[:5+sub] + '[...]' + key[-sub:]
        return key

    def moet_handmatig(self):
        # als deze vereniging een eigen Mollie sleutel ingesteld heeft
        # of akkoord heeft om via de bond betalingen te ontvangen
        # dan hoeft het niet handmatig
        kan_online = self.mollie_api_key or self.akkoord_via_bond
        return not kan_online

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return str(self.vereniging)

    class Meta:
        verbose_name = "Betaal instellingen vereniging"
        verbose_name_plural = "Betaal instellingen verenigingen"


class BetaalActief(models.Model):

    """ Deze tabel houdt bij welke payment_id actief zijn
        Hiermee kunnen we rommel filteren in de POST handler van de webhook.
    """

    # datum/tijdstip van aanmaak (wordt gebruikt voor opschonen)
    # de online-betaalmethoden verlopen na 3 uur, iDEAL al na 15 minuten
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # referentie naar de instellingen voor de vereniging waar de betaling bij hoort
    # TODO: bij akkoord_via_bond is dit niet de vereniging waar het heen moet!
    ontvanger = models.ForeignKey(BetaalInstellingenVereniging, on_delete=models.PROTECT)

    # het nummer dat ooit teruggegeven is toen de transactie aangemaakt werd
    payment_id = models.CharField(max_length=BETAAL_PAYMENT_ID_MAXLENGTH)

    # de laatste ontvangen status
    payment_status = models.CharField(max_length=BETAAL_PAYMENT_STATUS_MAXLENGTH, default='')

    # logboek met status veranderingen
    log = models.TextField(default='')

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "%s - %s" % (self.payment_id, localtime(self.when).strftime('%Y-%m-%d %H:%M:%S'))

    class Meta:
        verbose_name = "Actief payment_id"
        verbose_name_plural = "Actieve payment_id's"


class BetaalTransactie(models.Model):
    """ Afgeronde transacties: ontvangst en restitutie
    """

    # datum/tijdstip van aanmaak
    when = models.DateTimeField()

    # is dit een handmatig ingevoerde informatie van een overboeking?
    is_handmatig = models.BooleanField(default=False)

    # handmatige overboeking:
    # - bedrag_euro_klant == bedrag_euro_boeking
    # - optioneel: klant_naam, klant_account
    # - payment_id: leeg, wordt niet gebruikt

    # Mollie:
    # - payment_id = koppeling aan hun systeem
    # - beschrijving = ontvangen informatie

    # het nummer dat door de CPSP toegekend is
    payment_id = models.CharField(max_length=BETAAL_PAYMENT_ID_MAXLENGTH)

    # beschrijving voor op het afschrift van de klant
    # hierin staat normaal het bestelnummer
    beschrijving = models.CharField(max_length=BETAAL_BESCHRIJVING_MAXLENGTH)

    # is dit een restitutie of ontvangst?
    is_restitutie = models.BooleanField(default=False)

    # het bedrag wat de klant ziet (betaling / refund)
    bedrag_euro_klant = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)        # max 99999,99

    # het bedrag wat wij krijgen/uitgeven
    # betaling: het bedrag wat ontvangen is (dus transfer kosten al ingehouden door de CPSP)
    # refund: het bedrag wat uitbetaald is  (dus inclusief transfer kosten van de CPSP)
    bedrag_euro_boeking = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)      # max 99999,99

    # naam wat bij het rekeningnummer van de klant hoort
    klant_naam = models.CharField(max_length=BETAAL_KLANT_NAAM_MAXLENGTH)

    # informatie over de rekening waarmee betaald is
    klant_account = models.CharField(max_length=BETAAL_KLANT_ACCOUNT_MAXLENGTH)

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        return "[%s] %s - %s - %s euro %s" % (self.pk, self.payment_id,
                                              localtime(self.when).strftime('%Y-%m-%d %H:%M:%S'), self.beschrijving,
                                              self.bedrag_euro_klant)

    class Meta:
        verbose_name = "Betaal transactie"
        verbose_name_plural = "Betaal transacties"


class BetaalMutatie(models.Model):

    """ Deze tabel voedt de achtergrondtaak die de interacties met de CPSP doet """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie BETALINGEN_MUTATIE_*)
    code = models.PositiveSmallIntegerField(default=0)

    # houdt bij hoeveel pogingen er gedaan zijn
    # de achtergrondtaak verhoogt deze teller elke keer de taak opgepakt wordt
    # alleen mutaties met minder dan N pogingen worden opgepakt
    pogingen = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # BETAAL_MUTATIE_START_ONTVANGST:
    # BETAAL_MUTATIE_START_RESTITUTIE:

    # beschrijving voor op het afschrift van de klant
    # hierin staat normaal het bestelnummer
    beschrijving = models.CharField(max_length=BETAAL_BESCHRIJVING_MAXLENGTH, blank=True)

    # referentie naar de instellingen voor de vereniging waar de betaling heen moet
    ontvanger = models.ForeignKey(BetaalInstellingenVereniging, on_delete=models.PROTECT, blank=True, null=True)

    # het bedrag
    bedrag_euro = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)         # max 99999,99

    # waar naartoe (bij ons) als de betaling gedaan is?
    url_betaling_gedaan = models.CharField(max_length=100, default='', blank=True)

    # waar naartoe om de betaling te doen (bij de CPSP)
    url_checkout = models.CharField(max_length=400, default='', blank=True)

    # BETAAL_MUTATIE_START_RESTITUTIE:
    # BETAAL_MUTATIE_PAYMENT_STATUS_CHANGED:

    # Mollie-id ontvangen met de payment status changed webhook aanroep
    payment_id = models.CharField(max_length=BETAAL_PAYMENT_ID_MAXLENGTH, blank=True)

    class Meta:
        verbose_name = "Betaal mutatie"

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        msg = "[" + localtime(self.when).strftime('%Y-%m-%d %H:%M:%S') + "] "

        if not self.is_verwerkt:
            msg += "(nog niet verwerkt)"
        try:
            msg += "%s (%s)" % (self.code, BETAAL_MUTATIE_TO_STR[self.code])
        except KeyError:
            msg += "%s (???)" % self.code

        msg = msg + ' ' + self.beschrijving
        msg = msg.replace(' MijnHandboogsport', '')

        return msg


# TODO: boekhouding: betaald bedrag, ingehouden transactiekosten door CPSP, ontvangen bedrag, uitbetaalde bedragen,
#                   opsplitsing btw/transactiekosten


# end of file
