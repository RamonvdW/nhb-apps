# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_SPELD, BESTELLING_KORT_BREAK
from Bestelling.models import BestellingRegel
from Betaal.format import format_bedrag_euro
from Spelden.definities import (SPELD_DISCIPLINE2STR, SPELD_BOOGTYPE2STR, SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
                                SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR, SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
                                SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC, SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
                                SPELD_CATEGORIE_NL_TUSSENSPELD)
from Spelden.models import Speld, SpeldBestelling
from Webwinkel.definities import KEUZE_STATUS_RESERVERING_MANDJE, KEUZE_STATUS_BESTELD, KEUZE_STATUS_BACKOFFICE
from decimal import Decimal


class SpeldenBestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        mandje_pks = list()
        for keuze in (SpeldBestelling
                      .objects
                      .filter(status=KEUZE_STATUS_RESERVERING_MANDJE,
                              aangemaakt_op__lt=verval_datum)
                      .select_related('bestelling_regel')):

            regel = keuze.bestelling_regel

            # onthoud in welk mandje deze lag
            mandje = regel.bestellingmandje_set.first()
            if mandje:
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

    def _bepaal_speld_prijs(self, speld: Speld, is_nieuwe_aanvraag: bool) -> Decimal:
        if not is_nieuwe_aanvraag:
            return Decimal(settings.SPELD_PRIJS_VERVANG)

        if speld.categorie in (SPELD_CATEGORIE_NL_GRAADSPELD_INDOOR,
                               SPELD_CATEGORIE_NL_GRAADSPELD_OUTDOOR,
                               SPELD_CATEGORIE_NL_GRAADSPELD_VELD,
                               SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC,
                               SPELD_CATEGORIE_NL_GRAADSPELD_ALGEMEEN,
                               SPELD_CATEGORIE_NL_TUSSENSPELD):
            return Decimal(settings.SPELD_PRIJS_KHSN)

        return Decimal(settings.SPELD_PRIJS_WA)

    def reserveer(self, product_pk: int, mandje_van_str: str) -> BestellingRegel | None:
        """ De speld wordt in het mandje gelegd.
            Geef een BestellingRegel terug.
        """
        bestelling = (SpeldBestelling
                      .objects
                      .select_related('speld',
                                      'aanvraag')
                      .filter(pk=product_pk)
                      .first())

        if not bestelling:
            self.stdout.write('[WARNING] {spelden bestel plugin}.reserveer: ' +
                              'kan SpeldBestelling met pk=%s niet vinden' % product_pk)
            return None

        speld = bestelling.speld

        # bepaal de prijs van de speld
        prijs_euro = self._bepaal_speld_prijs(speld, bestelling.is_nieuwe_aanvraag)

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

        aanvraag = bestelling.aanvraag

        score = aanvraag.score_sm if speld.categorie == SPELD_CATEGORIE_NL_GRAADSPELD_SHORT_METRIC else aanvraag.score

        details1 = [
            SPELD_DISCIPLINE2STR[aanvraag.discipline],
            aanvraag.datum_wedstrijd.strftime('%Y-%m-%d'),
            SPELD_BOOGTYPE2STR[aanvraag.boog] + ' boog',
            'score %s' % score]

        details2 = list(aanvraag.informatie_wedstrijd.split('|'))
        if aanvraag.wedstrijd:
            details2.insert(0, aanvraag.wedstrijd.titel)

        kort = 'Speld: %s' % speld.beschrijving
        kort += BESTELLING_KORT_BREAK
        kort += '[%s]' % " / ".join(details1)
        kort += BESTELLING_KORT_BREAK
        kort += '[%s]' % " / ".join(details2)

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel.objects.create(
                        korte_beschrijving=kort,
                        bedrag_euro=prijs_euro,
                        btw_percentage=btw_str,
                        btw_euro=btw_euro,
                        code=BESTELLING_REGEL_CODE_SPELD)

        bestelling.bestelling_regel = regel

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, mandje_van_str)
        bestelling.log += msg

        bestelling.save(update_fields=['bestelling_regel', 'log'])

        return regel

    def annuleer(self, regel: BestellingRegel):
        """
            Het product wordt uit het mandje gehaald of de bestelling wordt geannuleerd (voordat deze betaald is)
        """
        bestelling = SpeldBestelling.objects.filter(bestelling_regel=regel).first()
        if not bestelling:
            self.stdout.write('[ERROR] Kan SpeldBestelling voor regel met pk=%s niet vinden' % regel.pk)
            return

        # verwijder de bestelling, maar laat de aanvraag staan omdat deze voor meerdere speld bestelling kan gelden
        self.stdout.write('[INFO] SpeldBestelling pk=%s wordt verwijderd' % bestelling.pk)
        bestelling.delete()

    def is_besteld(self, regel: BestellingRegel):
        """
            De speld in het mandje is nu omgezet in een bestelling.
            Verander de status van het gevraagde product naar 'besteld maar nog niet betaald'
        """
        bestelling = SpeldBestelling.objects.filter(bestelling_regel=regel.pk).first()
        if bestelling:
            stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
            msg = "[%s] Speld is is besteld\n" % stamp_str
            bestelling.log += msg
            bestelling.status = KEUZE_STATUS_BESTELD
            bestelling.save(update_fields=['status', 'log'])

    def is_betaald(self, regel: BestellingRegel, bedrag_ontvangen: Decimal):
        """
            Het product is betaald, dus de reservering moet definitief gemaakt worden.
            Wordt ook aangeroepen als een bestelling niet betaald hoeft te worden (totaal bedrag nul).
        """
        bestelling = SpeldBestelling.objects.filter(bestelling_regel=regel.pk).first()
        if not bestelling:
            self.stdout.write('[ERROR] Kan SpeldBestelling voor regel met pk=%s niet vinden' % regel.pk)
            return

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        bedrag_str = format_bedrag_euro(bedrag_ontvangen)
        msg = "[%s] Betaling is ontvangen (%s); overgedragen aan backoffice\n" % (stamp_str, bedrag_str)
        bestelling.log += msg

        bestelling.status = KEUZE_STATUS_BACKOFFICE
        bestelling.save(update_fields=['status', 'log'])

    def get_verkoper_ver_nr(self, regel: BestellingRegel) -> int:
        """
            Bepaal welke vereniging de verkopende partij is
        """
        # verkoper van de webwinkel producten is altijd het bondsbureau
        return settings.WEBWINKEL_VERKOPER_VER_NR


spelden_bestel_plugin = SpeldenBestelPlugin()

# end of file

