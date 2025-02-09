# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import models
from Evenement.models import EvenementInschrijving, EvenementAfgemeld
from Opleiding.models import OpleidingInschrijving, OpleidingAfgemeld
from Webwinkel.models import WebwinkelKeuze
from Wedstrijden.models import WedstrijdInschrijving
from decimal import Decimal


class BestellingProduct(models.Model):

    """ Een product dat opgenomen kan worden in een bestelling en in een mandje geplaatst kan worden,
        eventueel met korting.
    """

    # inschrijving voor een wedstrijd
    wedstrijd_inschrijving = models.ForeignKey(WedstrijdInschrijving, on_delete=models.SET_NULL, null=True, blank=True)

    # inschrijving voor een evenement
    evenement_inschrijving = models.ForeignKey(EvenementInschrijving, on_delete=models.SET_NULL, null=True, blank=True)
    evenement_afgemeld = models.ForeignKey(EvenementAfgemeld, on_delete=models.SET_NULL, null=True, blank=True)

    # keuze in de webwinkel
    webwinkel_keuze = models.ForeignKey(WebwinkelKeuze, on_delete=models.SET_NULL, null=True, blank=True)

    # inschrijving voor een opleiding
    opleiding_inschrijving = models.ForeignKey(OpleidingInschrijving, on_delete=models.SET_NULL, null=True, blank=True)
    opleiding_afgemeld = models.ForeignKey(OpleidingAfgemeld, on_delete=models.SET_NULL, null=True, blank=True)

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
        elif self.evenement_afgemeld:
            msg += str(self.evenement_afgemeld)
        elif self.webwinkel_keuze:
            msg += str(self.webwinkel_keuze)
        elif self.opleiding_inschrijving:
            msg += str(self.opleiding_inschrijving)
        elif self.opleiding_afgemeld:
            msg += str(self.opleiding_afgemeld)
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
        if self.evenement_afgemeld:
            return self.evenement_afgemeld.korte_beschrijving()
        if self.opleiding_inschrijving:
            return self.opleiding_inschrijving.korte_beschrijving()
        if self.opleiding_afgemeld:
            return self.opleiding_afgemeld.korte_beschrijving()
        if self.webwinkel_keuze:
            return self.webwinkel_keuze.korte_beschrijving()
        return "?"

    class Meta:
        verbose_name = "Bestelling product"
        verbose_name_plural = "Bestelling producten"


# end of file
