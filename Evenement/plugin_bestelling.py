# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.definities import BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING
from Bestelling.models import BestellingRegel
from Evenement.definities import (EVENEMENT_INSCHRIJVING_STATUS_TO_STR, EVENEMENT_AFMELDING_STATUS_TO_STR,
                                  EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF,
                                  EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                  EVENEMENT_AFMELDING_STATUS_GEANNULEERD,
                                  EVENEMENT_AFMELDING_STATUS_AFGEMELD)
from Evenement.models import EvenementInschrijving, EvenementAfgemeld


class BestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        # evenementen
        mandje_pks = list()
        for inschrijving in (EvenementInschrijving
                             .objects
                             .filter(status=EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                     wanneer__lt=verval_datum)
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

    def reserveer(self, inschrijving: EvenementInschrijving) -> BestellingRegel:
        """ Maak een reservering voor het evenement (zodat iemand anders deze niet kan reserveren)
            en geef een BestellingRegel terug.
        """
        evenement = inschrijving.evenement
        sporter = inschrijving.sporter

        # (nog) geen aantallen om bij te werken
        kort = evenement.titel
        prijs_euro = evenement.bepaal_prijs_voor_sporter(sporter)
        # btw, korting em gewicht zijn niet van toepassing

        # maak een product regel aan voor de bestelling
        regel = BestellingRegel(
                        korte_beschrijving=kort,
                        prijs_euro=prijs_euro,
                        code=BESTELLING_REGEL_CODE_EVENEMENT_INSCHRIJVING)
        regel.save()

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])

        return regel

    def verwijder_reservering(self, regel: BestellingRegel):
        pass

    def _verwijder_reservering(self, inschrijving: EvenementInschrijving) -> EvenementAfgemeld | None:
        # wordt gebruikt bij:
        # - inschrijving uit het mandje
        # - annuleren van een bestelling

        afmelding = None

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Verwijder reservering voor dit evenement\n" % stamp_str

        if inschrijving.status == EVENEMENT_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            # verwijdering uit mandje
            self.stdout.write('[INFO] Inschrijving evenement pk=%s status %s --> verwijderd uit mandje' % (
                              inschrijving.pk,
                              EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]))
        else:
            # zet de inschrijving om in een afmelding
            afmelding = EvenementAfgemeld(
                            wanneer_inschrijving=inschrijving.wanneer,
                            nummer=inschrijving.nummer,
                            wanneer_afgemeld=now,
                            status=EVENEMENT_AFMELDING_STATUS_AFGEMELD,
                            evenement=inschrijving.evenement,
                            sporter=inschrijving.sporter,
                            koper=inschrijving.koper,
                            bedrag_ontvangen=inschrijving.bedrag_ontvangen,
                            log=inschrijving.log + msg)

            if inschrijving.status != EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF:
                # nog niet betaald
                afmelding.status = EVENEMENT_AFMELDING_STATUS_GEANNULEERD

            afmelding.save()

            self.stdout.write('[INFO] Inschrijving evenement pk=%s status %s --> afgemeld pk=%s status %s' % (
                                inschrijving.pk,
                                EVENEMENT_INSCHRIJVING_STATUS_TO_STR[inschrijving.status],
                                afmelding.pk,
                                EVENEMENT_AFMELDING_STATUS_TO_STR[afmelding.status]))

        # verwijder de inschrijving
        inschrijving.delete()

        return afmelding


evenement_bestel_plugin = BestelPlugin()

# end of file

