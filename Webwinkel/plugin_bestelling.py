# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL
from Bestelling.models import BestellingRegel
from Webwinkel.definities import KEUZE_STATUS_RESERVERING_MANDJE
from Webwinkel.models import WebwinkelKeuze
from decimal import Decimal


class BestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        mandje_pks = list()
        for keuze in (WebwinkelKeuze
                      .objects
                      .filter(status=KEUZE_STATUS_RESERVERING_MANDJE,
                              wanneer__lt=verval_datum)
                      .select_related('bestelling',
                                      'koper')):

            regel = keuze.bestelling

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s webwinkel keuze (%s) in mandje van %s' % (
                              regel.pk, keuze, keuze.koper))

            # onthoud in welk mandje deze lag
            mandje = regel.bestellingmandje_set.first()
            mandje_pks.append(mandje)

            # geef de reservering op de producten weer vrij
            product = keuze.product
            aantal = keuze.aantal

            if not product.onbeperkte_voorraad:
                # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
                product.aantal_op_voorraad += aantal
                product.save(update_fields=['aantal_op_voorraad'])

            # verwijder de webwinkel keuze
            self.stdout.write('[INFO] WebwinkelKeuze met pk=%s wordt verwijderd' % keuze.pk)
            keuze.delete()

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, webwinkel_keuze: WebwinkelKeuze) -> BestellingRegel:
        """ Maak een reservering voor het webwinkel product (zodat iemand anders deze niet kan reserveren)
            en geef een BestellingRegel terug.
        """
        product = webwinkel_keuze.product
        aantal = webwinkel_keuze.aantal
        kort = webwinkel_keuze.korte_beschrijving()

        if not product.onbeperkte_voorraad:
            # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
            product.aantal_op_voorraad -= aantal
            product.save(update_fields=['aantal_op_voorraad'])

        prijs_euro = aantal * product.prijs_euro

        btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
        while btw_str[-1] == '0':
            btw_str = btw_str[:-1]              # 21,10 --> 21,1 / 21,00 --> 21,
        btw_str = btw_str.replace('.', ',')     # localize
        if btw_str[-1] == ",":
            btw_str = btw_str[:-1]              # drop the trailing dot/comma

        # de prijs is inclusief BTW, dus 100% + BTW% (voorbeeld: 121%)
        # reken uit hoeveel daarvan de BTW is (voorbeeld: 21 / 121)
        btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
        btw_euro = prijs_euro * btw_deel
        btw_euro = round(btw_euro, 2)             # afronden op 2 decimalen

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel(
                        korte_beschrijving=kort,
                        btw_percentage=btw_str,
                        prijs_euro=prijs_euro,
                        btw_euro=btw_euro,
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        webwinkel_keuze.bestelling = regel
        webwinkel_keuze.save(update_fields=['bestelling'])

        return regel

    def verwijder_reservering(self, regel: BestellingRegel):
        """ Geef een eerder gemaakte reservering voor een webwinkel product weer vrij
        """
        raise NotImplementedError()


webwinkel_bestel_plugin = BestelPlugin()


# end of file

