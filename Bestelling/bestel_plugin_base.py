# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.models import Bestelling, BestellingRegel, BestellingMandje
from decimal import Decimal
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

    def reserveer(self, inschrijving, mandje_van_str: str) -> BestellingRegel:
        """
            Zet een reservering voor het gevraagde product, zodat deze na betaling gegarandeerd is.
            Voorbeeld: webwinkel product met beperkte voorraad
                       wedstrijd met beperkt aantal deelnemers

            inschrijving kan van verschillende typen zijn: Evenement, Opleiding, Webwinkel, Wedstrijd
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

    def beschrijf_product(self, obj) -> list:
        """
            Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
            obj is specifiek voor de plugin, bijvoorbeeld WedstrijdInschrijving
        """
        raise NotImplementedError(obj)          # pragma: no cover

    def afmelden(self, obj):
        """
            Verwerk het verzoek tot afmelden voor een wedstrijd/evenement/opleiding.
        """
        raise NotImplementedError()             # pragma: no cover

    def bereken_verzendkosten(self, obj: BestellingMandje | Bestelling) -> Decimal:
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

# end of file
