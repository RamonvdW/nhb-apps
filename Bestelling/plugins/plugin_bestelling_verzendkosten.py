# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL, BESTELLING_REGEL_CODE_SPELD
from Bestelling.models import Bestelling, BestellingRegel, BestellingMandje
from Webwinkel.definities import VERZENDKOSTEN_BRIEFPOST, VERZENDKOSTEN_PAKKETPOST
from Webwinkel.models import WebwinkelKeuze
from decimal import Decimal


class VerzendkostenBestelPlugin(BestelPluginBase):

    def mandje_opschonen(self, verval_datum):
        # nothing to do
        return []

    # TODO: ook een verklaring voor de transportkosten terug geven (tekst regel): gram + afstand
    # TODO: ook btw teruggeven, want sommige(!) pakketkosten zijn inclusief btw
    def bereken_verzendkosten(self, obj: BestellingMandje | Bestelling) -> tuple[Decimal, str, Decimal]:
        """
            Bereken de verzendkosten van toepassing op het mandje of de bestelling
            0 = geen producten zijn die verstuurd hoeven te worden
        """

        verzendkosten_euro = Decimal(0)
        btw_percentage = ''
        btw_euro = Decimal(0)

        verzend_gratis = 0
        verzend_briefpost = 0
        verzend_pakketpost = 0

        # zoek de regels die over prestatiespelden gaan
        regel_pks = list(obj.regels.filter(code=BESTELLING_REGEL_CODE_SPELD).values_list('pk', flat=True))
        speld_count = len(regel_pks)
        if speld_count > 0:
            verzend_gratis = 1

        # zoek de regels die over webwinkel producten gaan
        regel_pks = list(obj.regels.filter(code=BESTELLING_REGEL_CODE_WEBWINKEL).values_list('pk', flat=True))
        webwinkel_count = len(regel_pks)
        if webwinkel_count > 0:
            qset = WebwinkelKeuze.objects.filter(bestelling_regel__pk__in=regel_pks)
            verzend_briefpost = qset.filter(product__type_verzendkosten=VERZENDKOSTEN_BRIEFPOST).count()
            verzend_pakketpost = qset.filter(product__type_verzendkosten=VERZENDKOSTEN_PAKKETPOST).count()

        if verzend_gratis > 0:
            verzendkosten_euro = Decimal(0.0001)    # not zero; rounds down to zero

        if verzend_briefpost > 0:
            # TODO: meerdere brieven (voorbeeld: 1 per muts)
            verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_2KG_VERZENDKOSTEN_EURO)

        if verzend_pakketpost > 0:
            # TODO: gewicht pakketpost
            verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_10KG_VERZENDKOSTEN_EURO)

        return verzendkosten_euro, btw_percentage, btw_euro

    def annuleer(self, regel: BestellingRegel):
        """
            Het product wordt uit het mandje gehaald of de bestelling wordt geannuleerd (voordat deze betaald is)
            Geef een eerder gemaakte reservering voor het webwinkel product weer vrij.
        """
        pass

    def is_besteld(self, regel: BestellingRegel):
        """
            Het gereserveerde product in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        pass

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """
        pass

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
        """
        # "verkoper" van de transportkosten is altijd het bondsbureau
        return settings.WEBWINKEL_VERKOPER_VER_NR


verzendkosten_bestel_plugin = VerzendkostenBestelPlugin()

# end of file

