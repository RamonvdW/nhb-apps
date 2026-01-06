# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.models import Bestelling, BestellingRegel, BestellingMandje
from decimal import Decimal
from typing import Tuple
import sys


class BestelPluginBase:

    """ basis class voor de bestellingen plugins """

    def __init__(self):
        self.stdout = sys.stdout

    def zet_stdout(self, stdout):
        """ zet de stdout van het management commando """
        self.stdout = stdout

    def mandje_opschonen(self, verval_datum):
        raise NotImplementedError()             # pragma: no cover

    def reserveer(self, product_pk, mandje_van_str: str) -> BestellingRegel | None:
        """
            Zet een reservering voor het gevraagde product, zodat deze na betaling gegarandeerd is.
            Voorbeeld: webwinkel product met beperkte voorraad
                       wedstrijd met beperkt aantal deelnemers

            product_pk kan verwijzen naar: Evenement, Opleiding, WebwinkelKeuze, WedstrijdInschrijving
        """
        raise NotImplementedError()             # pragma: no cover

    def aanpassen(self, product_pk, door_account_str: str, **kwargs):
        """
            Maak een aanpassing in een al gemaakte bestelling.
            Voorbeeld: sporter will van boogtype wisselen voor een wedstrijd

            product_pk kan verwijzen naar: Evenement, Opleiding, WebwinkelKeuze, WedstrijdInschrijving
            kwargs is een dictionary met alle mutaties
        """
        raise NotImplementedError()             # pragma: no cover

    def annuleer(self, regel: BestellingRegel):
        """
            Het product wordt uit het mandje gehaald of de bestelling wordt geannuleerd (voordat deze betaald is)
            Geef een eerder gemaakte reservering voor het product weer vrij.
        """
        raise NotImplementedError()             # pragma: no cover

    def is_besteld(self, regel: BestellingRegel):
        """
            Het gereserveerde product in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        raise NotImplementedError()             # pragma: no cover

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """
        raise NotImplementedError(regel)        # pragma: no cover

    def afmelden(self, inschrijving_pk):
        """
            Verwerk het verzoek tot afmelden voor een wedstrijd/evenement/opleiding.
            inschrijving_pk kan verwijzen naar: EvenementInschrijving, OpleidingInschrijving, WedstrijdInschrijving
        """
        raise NotImplementedError()             # pragma: no cover

    def bereken_verzendkosten(self, obj: BestellingMandje | Bestelling) -> Tuple[Decimal, str, Decimal]:
        """
            Bereken de verzendkosten van toepassing op het mandje of de bestelling
        """
        raise NotImplementedError(obj)          # pragma: no cover

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
            Geeft het verenigingsnummer terug, of -1 als dit niet te bepalen was
        """
        raise NotImplementedError(regel)        # pragma: no cover

    def wil_kwalificatiescores(self, regel: BestellingRegel) -> object | None:
        """
            Controleer of deze regel invoer van kwalificatiescores nodig heeft.
            Zoja, geeft Wedstrijd records terug met daarin:
                - datum_str
                - plaats_str
                - sporter_str
                - url_kwalificatie_scores    Voor het bijwerken van de kwalificatie scores
        """
        raise NotImplementedError(regel)        # pragma: no cover

# end of file
