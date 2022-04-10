# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Account.models import Account
from NhbStructuur.models import NhbVereniging


BETALINGEN_MUTATIE_AFREKENEN = 1
BETALINGEN_MUTATIE_CREATE_PAYMENT_RESPONSE = 2
BETALINGEN_MUTATIE_PAYMENT_STATUS_CHANGED = 3

BETALINGEN_MUTATIE_TO_STR = {
    BETALINGEN_MUTATIE_AFREKENEN: "Afrekenen",
    BETALINGEN_MUTATIE_CREATE_PAYMENT_RESPONSE: "Create payment response",
    BETALINGEN_MUTATIE_PAYMENT_STATUS_CHANGED: "Payment status changed",
}

# geen maximum lengte kunnen vinden in de documentatie
MOLLIE_PAYMENT_ID_MAXLENGTH = 32
MOLLIE_API_KEY_MAXLENGTH = 50


class BetalingenActieveTransacties(models.Model):

    """ Deze tabel houdt bij welke payment transacties actief zijn
        Hiermee kunnen we al in de POST handler van de webhook rommel filteren.
    """

    # datum/tijdstip van aanmaak (wordt gebruikt voor opschonen)
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # het nummer dat ooit teruggegeven is toen de transactie aangemaakt werd
    payment_id = models.CharField(max_length=MOLLIE_PAYMENT_ID_MAXLENGTH)

    class Meta:
        verbose_name = "Betalingen actieve transacties"


class BetalingTransacties(models.Model):
    """ afgeronde transacties """

    # bij welke account hoort deze transactie?
    account = models.ForeignKey(Account, on_delete=models.PROTECT)

    # het nummer dat door de CPSP toegekend is
    payment_id = models.CharField(max_length=MOLLIE_PAYMENT_ID_MAXLENGTH)

    # datum/tijdstip van aanmaak
    when = models.DateTimeField()

    # de bedragen
    bedrag_ontvangen_euro = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)      # max 99999,99
    bedrag_retour_euro = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)         # max 99999,99

    # naam wat bij het rekeningnummer van de klant hoort
    klant_naam = models.CharField(max_length=100)

    # IBAN nummer van de rekening waarmee betaal id
    # zie https://bank.codes/iban/structure/netherlands/
    klant_iban = models.CharField(max_length=18)
    klant_bic = models.CharField(max_length=11)

    # logboek van hoeveel en wanneer er ontvangen en terugbetaald is
    log = models.TextField()


class BetalingenVerenigingInstellingen(models.Model):

    # bij welke vereniging hoort deze informatie?
    vereniging = models.ForeignKey(NhbVereniging, on_delete=models.CASCADE)

    # de API key van deze vereniging voor Mollie
    mollie_api_key = models.CharField(max_length=MOLLIE_API_KEY_MAXLENGTH)

    # mag deze vereniging betalingen ontvangen via de NHB?
    akkoord_via_nhb = models.BooleanField(default=False)

    def obfuscated_mollie_api_key(self):
        # mollie key heeft een prefix live_ of test_ gevolgd door iets van 20 letters/cijfers
        # verwijder het middelste stuk
        key = self.mollie_api_key
        key = key[:5+2] + '[...]' + key[-2:]
        return key

    class Meta:
        verbose_name = "Betalingen vereniging instellingen"


class BetalingenMutatie(models.Model):

    """ Deze tabel voedt de achtergrondtaak die de interacties met de CPSP doet """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie BETALINGEN_MUTATIE_*)
    code = models.PositiveSmallIntegerField(default=0)

    # referentie naar de boeking waar deze mutatie over gaat
    boekingsnummer = models.PositiveIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # Mollie id ontvangen met de payment status changed webhook aanroep
    payment_id = models.CharField(max_length=MOLLIE_PAYMENT_ID_MAXLENGTH)

    # afrekenen: beschrijving van de items die afrekenend moeten worden

    class Meta:
        verbose_name = "Betalingen mutatie"

    def __str__(self):
        msg = "[%s]" % self.when
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.code, BETALINGEN_MUTATIE_TO_STR[self.code])
        except KeyError:
            msg += " %s (???)" % self.code

        return msg


# er is maar een BetalingenHoogsteBoekingsnummer record en dit is het nummer
BETALINGEN_HOOGSTE_PK = 1

class BetalingenHoogsteBoekingsnummer(models.Model):

    """ een kleine tabel om het hoogst gebruikte boekingsnummer bij te houden """

    # hoogste gebruikte boekingsnummer
    hoogste_gebruikte_boekingsnummer = models.PositiveIntegerField(default=0)


# TODO: boekhouding: betaald bedrag, ingehouden transactiekosten door CPSP, ontvangen bedrag, uitbetaalde bedragen, opsplitsing btw/transactiekosten


# end of file
