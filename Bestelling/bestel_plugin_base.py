# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.models import BestellingRegel
import sys


class BestelPluginBase:

    """ basis class voor de bestellingen plugins """

    def __init__(self):
        self.stdout = sys.stdout

    def zet_stdout(self, stdout):
        """ zet de stdout van het management commando """
        self.stdout = stdout

    def mandje_opschonen(self, verval_datum):
        raise NotImplementedError()

    def reserveer(self, inschrijving, mandje_van_str: str) -> BestellingRegel:
        # inschrijving kan van verschillende typen zijn: Evenement, Opleiding, Webwinkel, Wedstrijd
        raise NotImplementedError()

    def verwijder_reservering(self, regel: BestellingRegel) -> BestellingRegel | None:
        """
            Het product wordt uit het mandje gehaald
            of de bestelling wordt geannuleerd (voordat deze betaald is)
        """
        raise NotImplementedError()

    def beschrijf_product(self, obj) -> list:
        """
            Geef een lijst van tuples terug waarin aspecten van het product beschreven staan.
        """
        raise NotImplementedError()


# end of file
