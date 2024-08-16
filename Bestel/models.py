# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from django.utils import timezone
from Account.models import Account
from Bestel.definities import (BESTELLING_STATUS_CHOICES, BESTELLING_STATUS_NIEUW, BESTELLING_STATUS2STR,
                               BESTEL_MUTATIE_TO_STR, BESTEL_TRANSPORT_NVT, BESTEL_TRANSPORT_OPTIES)
from Betaal.models import BetaalActief, BetaalTransactie, BetaalMutatie, BetaalInstellingenVereniging
from Evenement.models import EvenementInschrijving
from Webwinkel.models import WebwinkelKeuze
from Wedstrijden.models import WedstrijdInschrijving
from decimal import Decimal


class BestelProduct(models.Model):

    """ Een product dat opgenomen kan worden in een bestelling en in een mandje geplaatst kan worden,
        eventueel met korting.
    """

    # inschrijving voor een wedstrijd
    wedstrijd_inschrijving = models.ForeignKey(WedstrijdInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # inschrijving voor een evenement
    evenement_inschrijving = models.ForeignKey(EvenementInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # keuze in de webwinkel
    webwinkel_keuze = models.ForeignKey(WebwinkelKeuze, on_delete=models.SET_NULL, null=True, blank=True)

    # FUTURE: andere mogelijke producten (opleiding)

    # prijs van deze regel (een positief bedrag)
    prijs_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))       # max 999,99

    # de korting op deze regel (ook een positief bedrag!)
    korting_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))     # max 999,99

    # FUTURE: gedeeltelijke terugstorting bijhouden

    # FUTURE: traceer gestuurde e-mails (voor sturen herinnering)

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = "[%s] " % self.pk

        if self.wedstrijd_inschrijving:
            msg += str(self.wedstrijd_inschrijving)
        elif self.evenement_inschrijving:
            msg += str(self.evenement_inschrijving)
        elif self.webwinkel_keuze:
            msg += str(self.webwinkel_keuze)
        else:
            # FUTURE: andere producten
            msg += '?'

        msg += ' %s' % self.prijs_euro
        if self.korting_euro > 0.0001:
            msg += ' -%s' % self.korting_euro

        return msg

    def korte_beschrijving(self):
        if self.wedstrijd_inschrijving:
            return self.wedstrijd_inschrijving.korte_beschrijving()
        if self.evenement_inschrijving:
            return self.evenement_inschrijving.korte_beschrijving()
        if self.webwinkel_keuze:
            return self.webwinkel_keuze.korte_beschrijving()
        return "?"

    class Meta:
        verbose_name = "Bestel product"
        verbose_name_plural = "Bestel producten"


class BestelMandje(models.Model):

    """ Een verzameling producten die nog veranderd kunnen worden en waaraan een korting gekoppeld kan worden.
        Wordt omgezet in een Bestelling zodra 'afrekenen' wordt gekozen.
    """

    # van wie is dit mandje?
    # maximaal 1 mandje per account
    account = models.OneToOneField(Account, on_delete=models.CASCADE)

    # de gekozen producten met prijs en korting
    producten = models.ManyToManyField(BestelProduct)

    # afleveradres: automatisch voor leden, handmatig voor gastaccounts (kan ook buitenlands adres zijn)
    # (gebaseerd op info van https://docs.superoffice.com/nl/company/learn/address-formats.html)
    afleveradres_regel_1 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_2 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_3 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_4 = models.CharField(max_length=100, default='', blank=True)      # postcode + plaats
    afleveradres_regel_5 = models.CharField(max_length=100, default='', blank=True)      # land

    # verzendkosten
    transport = models.CharField(max_length=1, default=BESTEL_TRANSPORT_NVT, choices=BESTEL_TRANSPORT_OPTIES)
    verzendkosten_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))    # max 9999,99

    # belasting in verschillende categorieën: leeg = niet gebruikt
    btw_percentage_cat1 = models.CharField(max_length=5, default='', blank=True)        # 21,00
    btw_percentage_cat2 = models.CharField(max_length=5, default='', blank=True)
    btw_percentage_cat3 = models.CharField(max_length=5, default='', blank=True)

    # het aantal van het totaal voor elk van de BTW percentages
    # (dus niet optellen bij het totaal!)
    btw_euro_cat1 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat2 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat3 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))           # max 99999,99

    # maximaal 1x per dag mag een e-mail herinnering verstuurd worden als er nog producten in het mandje liggen
    vorige_herinnering = models.DateField(default='2000-01-01')

    def bepaal_totaalprijs_opnieuw(self):
        """ Bepaal het totaal_euro veld opnieuw, gebaseerd op alles wat in het mandje ligt

            Let op: Roep deze aan met een select_for_update() lock
        """
        self.totaal_euro = Decimal(0)
        for product in self.producten.all():
            self.totaal_euro += product.prijs_euro
            self.totaal_euro -= product.korting_euro
        # for
        self.totaal_euro += self.verzendkosten_euro
        self.save(update_fields=['totaal_euro'])

    def __str__(self):
        """ beschrijving voor de admin interface """
        return self.account.username

    class Meta:
        verbose_name = "Mandje"
        verbose_name_plural = "Mandjes"


class Bestelling(models.Model):

    """ een volledige bestelling die afgerekend kan worden / afgerekend is """

    # het unieke bestelnummer
    bestel_nr = models.PositiveIntegerField()

    # wanneer aangemaakt?
    # hiermee kunnen onbetaalde bestellingen na een tijdje opgeruimd worden
    aangemaakt = models.DateTimeField(auto_now_add=True)

    # van wie is deze bestelling
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)

    # welke vereniging is ontvanger van de gelden voor deze bestelling?
    # per bestelling kan er maar 1 ontvanger zijn
    ontvanger = models.ForeignKey(BetaalInstellingenVereniging, on_delete=models.PROTECT,
                                  null=True, blank=True)        # alleen nodig voor migratie

    # verplichte informatie over de verkoper
    # naam, adres, kvk, email, telefoon
    verkoper_naam = models.CharField(max_length=100, default='', blank=True)
    verkoper_adres1 = models.CharField(max_length=100, default='', blank=True)      # straat
    verkoper_adres2 = models.CharField(max_length=100, default='', blank=True)      # postcode, plaats
    verkoper_kvk = models.CharField(max_length=15, default='', blank=True)
    verkoper_btw_nr = models.CharField(max_length=15, default='', blank=True)
    verkoper_email = models.EmailField(default='', blank=True)
    verkoper_telefoon = models.CharField(max_length=20, default='', blank=True)

    # bankrekening details
    verkoper_iban = models.CharField(max_length=18, default='', blank=True)
    verkoper_bic = models.CharField(max_length=11, default='', blank=True)          # 8 of 11 tekens
    verkoper_heeft_mollie = models.BooleanField(default=False)

    # de bestelde producten met prijs en korting
    producten = models.ManyToManyField(BestelProduct)

    # afleveradres: automatisch voor leden, handmatig voor gastaccounts (kan ook buitenlands adres zijn)
    # (gebaseerd op info van https://docs.superoffice.com/nl/company/learn/address-formats.html)
    afleveradres_regel_1 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_2 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_3 = models.CharField(max_length=100, default='', blank=True)
    afleveradres_regel_4 = models.CharField(max_length=100, default='', blank=True)      # postcode + plaats
    afleveradres_regel_5 = models.CharField(max_length=100, default='', blank=True)      # land

    # verzendkosten
    transport = models.CharField(max_length=1, default=BESTEL_TRANSPORT_NVT, choices=BESTEL_TRANSPORT_OPTIES)
    verzendkosten_euro = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))    # max 9999,99

    # belasting in verschillende categorieën: leeg = niet gebruikt
    btw_percentage_cat1 = models.CharField(max_length=5, default='', blank=True)
    btw_percentage_cat2 = models.CharField(max_length=5, default='', blank=True)
    btw_percentage_cat3 = models.CharField(max_length=5, default='', blank=True)

    btw_euro_cat1 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat2 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99
    btw_euro_cat3 = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))         # max 9999,99

    # het af te rekenen totaalbedrag
    totaal_euro = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal(0))       # max 99999,99

    # de status van de hele bestelling
    status = models.CharField(max_length=1, default=BESTELLING_STATUS_NIEUW, choices=BESTELLING_STATUS_CHOICES)

    # de opgestarte betaling/restitutie wordt hier bijgehouden
    # de BetaalMutatie wordt opgeslagen zodat deze is aangemaakt. Daarin zet de achtergrond taak een payment_id.
    # daarmee kunnen we het BetaalActief record vinden met de status van de betaling en de log
    betaal_mutatie = models.ForeignKey(BetaalMutatie, on_delete=models.SET_NULL, null=True, blank=True)
    betaal_actief = models.ForeignKey(BetaalActief, on_delete=models.SET_NULL, null=True, blank=True)

    # de afgeronde betalingen: ontvangst en restitutie
    transacties = models.ManyToManyField(BetaalTransactie, blank=True)

    # logboek van hoeveel en wanneer er ontvangen en terugbetaald is
    log = models.TextField()

    def __str__(self):
        """ beschrijving voor de admin interface """
        msg = "%s" % self.bestel_nr
        msg += " %s" % BESTELLING_STATUS2STR[self.status]
        msg += " [%s]" % timezone.localtime(self.aangemaakt).strftime('%Y-%m-%d %H:%M:%S')
        msg += " koper=%s" % self.account.username

        bedrag = " € %s" % self.totaal_euro
        msg += bedrag.replace('.', ',')

        return msg

    def mh_bestel_nr(self):
        return "MH-%s" % self.bestel_nr

    class Meta:
        verbose_name = "Bestelling"
        verbose_name_plural = "Bestellingen"


class BestelHoogsteBestelNr(models.Model):

    """ een kleine tabel om het hoogst gebruikte bestelnummer bij te houden """

    # hoogste gebruikte boekingsnummer
    hoogste_gebruikte_bestel_nr = models.PositiveIntegerField(default=0)


class BestelMutatie(models.Model):

    """ Deze tabel voedt de achtergrondtaak die de interactie met het mandje en bestellingen doet """

    # datum/tijdstip van mutatie
    when = models.DateTimeField(auto_now_add=True)      # automatisch invullen

    # wat is de wijziging (zie BESTEL_MUTATIE_*)
    code = models.PositiveSmallIntegerField(default=0)

    # is deze mutatie al verwerkt?
    is_verwerkt = models.BooleanField(default=False)

    # BESTEL_MUTATIE_WEDSTRIJD_INSCHRIJVEN      account(=mandje), wedstrijd_inschrijving
    # BESTEL_MUTATIE_WEBWINKEL_KEUZE            account(=mandje), webwinkel_keuze
    # BESTEL_MUTATIE_VERWIJDER:                 account(=mandje), product
    # BESTEL_MUTATIE_MAAK_BESTELLING:           account(=mandje)
    # BESTEL_MUTATIE_WEDSTRIJD_AFMELDEN:        inschrijving
    # BESTEL_MUTATIE_BETALING_AFGEROND:         bestelling, betaling_is_gelukt
    # BESTEL_MUTATIE_OVERBOEKING_ONTVANGEN:     bestelling, bedrag_euro
    # BESTEL_MUTATIE_RESTITUTIE_UITBETAALD:
    # BESTEL_MUTATIE_ANNULEER:                  bestelling
    # BESTEL_MUTATIE_TRANSPORT:
    # BESTEL_MUTATIE_EVENEMENT_INSCHRIJVEN:     evenement_inschrijving

    # mandje van dit account
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    # de wedstrijd inschrijving
    wedstrijd_inschrijving = models.ForeignKey(WedstrijdInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # inschrijving voor een evenement
    evenement_inschrijving = models.ForeignKey(EvenementInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # de webwinkel keuze
    webwinkel_keuze = models.ForeignKey(WebwinkelKeuze, on_delete=models.SET_NULL, null=True, blank=True)

    # het product waar deze mutatie betrekking op heeft
    product = models.ForeignKey(BestelProduct, on_delete=models.SET_NULL, null=True, blank=True)

    # gevraagde korting om toe te passen
    korting = models.CharField(max_length=20, default='', blank=True)

    # de bestelling waar deze mutatie betrekking op heeft
    bestelling = models.ForeignKey(Bestelling, on_delete=models.SET_NULL, null=True, blank=True)

    # status van de betaling: gelukt, of niet?
    betaling_is_gelukt = models.BooleanField(default=False)

    # het ontvangen of betaalde bedrag
    bedrag_euro = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal(0))       # max 999,99

    # nieuwe transport keuze
    transport = models.CharField(max_length=1, default=BESTEL_TRANSPORT_NVT, choices=BESTEL_TRANSPORT_OPTIES)

    class Meta:
        verbose_name = "Bestel mutatie"

    def __str__(self):
        """ Lever een tekstuele beschrijving voor de admin interface """
        msg = "[%s]" % self.when
        if not self.is_verwerkt:
            msg += " (nog niet verwerkt)"
        try:
            msg += " %s (%s)" % (self.code, BESTEL_MUTATIE_TO_STR[self.code])
        except KeyError:
            msg += " %s (???)" % self.code

        return msg


# end of file
