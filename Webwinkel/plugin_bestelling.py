# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_WEBWINKEL
from Bestelling.models import Bestelling, BestellingRegel, BestellingMandje
from Betaal.format import format_bedrag_euro
from Webwinkel.definities import (KEUZE_STATUS_RESERVERING_MANDJE, KEUZE_STATUS_BESTELD, KEUZE_STATUS_BACKOFFICE,
                                  KEUZE_STATUS_GEANNULEERD, VERZENDKOSTEN_BRIEFPOST, VERZENDKOSTEN_PAKKETPOST)
from Webwinkel.models import WebwinkelKeuze
from decimal import Decimal


class WebwinkelBestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        mandje_pks = list()
        for keuze in (WebwinkelKeuze
                      .objects
                      .filter(status=KEUZE_STATUS_RESERVERING_MANDJE,
                              wanneer__lt=verval_datum)
                      .select_related('bestelling')):

            regel = keuze.bestelling

            # onthoud in welk mandje deze lag
            mandje = regel.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s webwinkel keuze (%s) in mandje van %s' % (
                              regel.pk, keuze, mandje.account))

            self.annuleer(regel)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, product_pk: int, mandje_van_str: str) -> BestellingRegel | None:
        """ Maak een reservering voor het webwinkel product (zodat iemand anders deze niet kan reserveren)
            en geef een BestellingRegel terug.
        """
        webwinkel_keuze = (WebwinkelKeuze
                           .objects
                           .select_related('product')
                           .filter(pk=product_pk)
                           .first())

        if not webwinkel_keuze:
            self.stdout.write('[WARNING] {webwinkel bestel plugin}.reserveer: ' +
                              'kan WebwinkelKeuze met pk=%s niet vinden' % product_pk)
            return None

        product = webwinkel_keuze.product
        aantal = webwinkel_keuze.aantal
        kort = webwinkel_keuze.korte_beschrijving()

        if not product.onbeperkte_voorraad:
            # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
            # TODO: waar zit de bescherming tegen "geen voorraad meer"?
            product.aantal_op_voorraad -= aantal
            product.save(update_fields=['aantal_op_voorraad'])

        prijs_euro = aantal * product.prijs_euro

        # TODO: bij levering aan het buitenland (ook particulieren) 0% btw in rekening brengen
        # zie https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/btw/zakendoen_met_het_buitenland/zakendoen_buiten_de_eu/btw_berekenen/btw_berekenen_bij_export_van_goederen_naar_niet_eu_landen/btw_berekenen_bij_het_uitvoeren_naar_niet_eu_landen

        btw_str = "%.2f" % settings.WEBWINKEL_BTW_PERCENTAGE
        while btw_str[-1] == '0':
            btw_str = btw_str[:-1]              # 21,10 --> 21,1 / 21,00 --> 21,
        btw_str = btw_str.replace('.', ',')     # localize
        if btw_str[-1] == ",":
            btw_str = btw_str[:-1]              # drop the trailing dot/comma: 21, --> 21

        # de prijs is inclusief BTW, dus 100% + BTW% (voorbeeld: 121%)
        # reken uit hoeveel daarvan de BTW is (voorbeeld: 21 / 121)
        btw_deel = Decimal(settings.WEBWINKEL_BTW_PERCENTAGE / (100 + settings.WEBWINKEL_BTW_PERCENTAGE))
        btw_euro = prijs_euro * btw_deel
        btw_euro = round(btw_euro, 2)             # afronden op 2 decimalen

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel(
                        korte_beschrijving=kort,
                        bedrag_euro=prijs_euro,
                        btw_percentage=btw_str,
                        btw_euro=btw_euro,
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        webwinkel_keuze.bestelling = regel

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, mandje_van_str)
        webwinkel_keuze.log += msg

        webwinkel_keuze.save(update_fields=['bestelling', 'log'])

        return regel

    def annuleer(self, regel: BestellingRegel):
        """
            Het product wordt uit het mandje gehaald of de bestelling wordt geannuleerd (voordat deze betaald is)
            Geef een eerder gemaakte reservering voor het webwinkel product weer vrij.
        """
        keuze = WebwinkelKeuze.objects.filter(bestelling=regel).select_related('product').first()
        if not keuze:
            self.stdout.write('[ERROR] Kan WebwinkelKeuze voor regel met pk=%s niet vinden' % regel.pk)
            return

        product = keuze.product
        if not product.onbeperkte_voorraad:
            # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
            product.aantal_op_voorraad += keuze.aantal
            product.save(update_fields=['aantal_op_voorraad'])

        # keuze.status = KEUZE_STATUS_GEANNULEERD
        # keuze.save(update_fields=['status'])

        # verwijder de keuze
        self.stdout.write('[INFO] WebwinkelKeuze pk=%s wordt verwijderd' % keuze.pk)
        keuze.delete()

    def is_besteld(self, regel: BestellingRegel):
        """
            Het gereserveerde product in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        keuze = WebwinkelKeuze.objects.filter(bestelling=regel.pk).first()
        if keuze:
            stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Reservering is omgezet in een bestelling\n" % stamp_str
            keuze.log += msg
            keuze.status = KEUZE_STATUS_BESTELD
            keuze.save(update_fields=['status', 'log'])

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """
        keuze = WebwinkelKeuze.objects.filter(bestelling=regel.pk).first()
        if not keuze:
            self.stdout.write('[ERROR] Kan WebwinkelKeuze voor regel met pk=%s niet vinden' % regel.pk)
            return

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        bedrag_str = format_bedrag_euro(bedrag_ontvangen)
        msg = "[%s] Betaling is ontvangen (%s); overgedragen aan backoffice\n" % (stamp_str, bedrag_str)
        keuze.log += msg

        keuze.status = KEUZE_STATUS_BACKOFFICE
        keuze.save(update_fields=['status', 'log'])

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
        """
        # verkoper van de webwinkel producten is altijd het bondsbureau
        return settings.WEBWINKEL_VERKOPER_VER_NR


class VerzendkostenBestelPlugin(BestelPluginBase):

    def mandje_opschonen(self, verval_datum):
        # nothing to do
        return []

    # TODO: ook een verklaring voor de transportkosten terug geven (tekst regel): gram + afstand
    # TODO: ook btw teruggeven, want sommige(!) pakketkosten zijn inclusief btw
    def bereken_verzendkosten(self, obj: BestellingMandje | Bestelling) -> (Decimal, str, Decimal):
        """
            Bereken de verzendkosten van toepassing op het mandje of de bestelling
            0 = geen producten zijn die verstuurd hoeven te worden
        """

        # zoek de regels die over webwinkel producten gaan
        regel_pks = list(obj.regels.filter(code=BESTELLING_REGEL_CODE_WEBWINKEL).values_list('pk', flat=True))
        webwinkel_count = len(regel_pks)

        verzendkosten_euro = Decimal(0)
        btw_percentage = ''
        btw_euro = Decimal(0)

        if webwinkel_count > 0:
            qset = WebwinkelKeuze.objects.filter(bestelling__pk__in=regel_pks)
            webwinkel_briefpost = qset.filter(product__type_verzendkosten=VERZENDKOSTEN_BRIEFPOST).count()
            webwinkel_pakketpost = qset.filter(product__type_verzendkosten=VERZENDKOSTEN_PAKKETPOST).count()

            if webwinkel_briefpost > 0:
                # TODO: meerdere brieven (voorbeeld: 1 per muts)
                verzendkosten_euro = Decimal(settings.WEBWINKEL_PAKKET_2KG_VERZENDKOSTEN_EURO)

            if webwinkel_pakketpost > 0:
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


webwinkel_bestel_plugin = WebwinkelBestelPlugin()
verzendkosten_bestel_plugin = VerzendkostenBestelPlugin()

# end of file

