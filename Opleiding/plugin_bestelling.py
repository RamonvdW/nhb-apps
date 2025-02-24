# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING
from Bestelling.models import BestellingRegel
from Opleiding.definities import (OPLEIDING_INSCHRIJVING_STATUS_TO_STR, OPLEIDING_AFMELDING_STATUS_TO_STR,
                                  OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF,
                                  OPLEIDING_AFMELDING_STATUS_AFGEMELD, OPLEIDING_AFMELDING_STATUS_GEANNULEERD)
from Opleiding.models import OpleidingInschrijving, OpleidingAfgemeld


class BestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        mandje_pks = list()
        for inschrijving in (OpleidingInschrijving
                             .objects
                             .filter(status=OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                     wanneer_aangemeld__lt=verval_datum)
                             .select_related('bestelling',
                                             'koper')):

            regel = inschrijving.bestelling

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s inschrijving (%s) in mandje van %s' % (
                              regel.pk, inschrijving, inschrijving.koper))

            # onthoud in welk mandje deze lag
            mandje = regel.bestellingmandje_set.first()
            mandje_pks.append(mandje)

            self._verwijder_reservering(inschrijving)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, inschrijving: OpleidingInschrijving) -> BestellingRegel:
        """ Maak een reservering voor de opleiding
            en geef een BestellingRegel terug.
        """

        opleiding = inschrijving.opleiding
        kort = opleiding.titel
        # (nog) geen aantallen om bij te werken
        # btw, korting en gewicht zijn niet van toepassing

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel(
                        korte_beschrijving=kort,
                        prijs_euro=opleiding.kosten_euro,
                        code=BESTELLING_REGEL_CODE_OPLEIDING_INSCHRIJVING)
        regel.save()

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])

        return regel

    def verwijder_reservering(self, regel: BestellingRegel):
        raise NotImplementedError()

    def _verwijder_reservering(self, inschrijving: OpleidingInschrijving) -> OpleidingAfgemeld:

        afmelding = None

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Annuleer inschrijving voor deze opleiding\n" % stamp_str

        if inschrijving.status == OPLEIDING_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            # verwijdering uit mandje
            self.stdout.write('[INFO] Inschrijving opleiding pk=%s status %s --> verwijderd uit mandje' % (
                              inschrijving.pk,
                              OPLEIDING_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))
        else:
            # zet de inschrijving om in een afmelding
            afmelding = OpleidingAfgemeld(
                            wanneer_aangemeld=inschrijving.wanneer_aangemeld,
                            nummer=inschrijving.nummer,
                            wanneer_afgemeld=now,
                            status=OPLEIDING_AFMELDING_STATUS_AFGEMELD,
                            opleiding=inschrijving.opleiding,
                            sporter=inschrijving.sporter,
                            koper=inschrijving.koper,
                            bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                            log=inschrijving.log + msg)

            if inschrijving.status != OPLEIDING_INSCHRIJVING_STATUS_DEFINITIEF:
                # nog niet betaald
                afmelding.status = OPLEIDING_AFMELDING_STATUS_GEANNULEERD

            afmelding.save()

            self.stdout.write('[INFO] Opleiding deelnemer pk=%s status %s --> afgemeld pk=%s status %s' % (
                              inschrijving.pk,
                              OPLEIDING_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
                              afmelding.pk,
                              OPLEIDING_AFMELDING_STATUS_TO_STR[afmelding.status]))

        # verwijder de inschrijving
        inschrijving.delete()

        return afmelding


opleiding_bestel_plugin = BestelPlugin()

# end of file

