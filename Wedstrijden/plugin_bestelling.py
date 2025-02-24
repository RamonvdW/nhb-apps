# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Bestelling.bestel_plugin_base import BestelPluginBase
from Bestelling.models import BestellingRegel
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR)
from Wedstrijden.models import WedstrijdInschrijving


class BestelPlugin(BestelPluginBase):

    def __init__(self):
        super().__init__()

    def mandje_opschonen(self, verval_datum):
        # evenementen
        mandje_pks = list()

        # wedstrijden
        for inschrijving in (WedstrijdInschrijving
                             .objects
                             .filter(wanneer__lt=verval_datum,
                                     status=WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE)
                             .select_related('bestelling',
                                             'koper')):

            regel = inschrijving.bestelling

            self.stdout.write('[INFO] Vervallen: BestellingRegel pk=%s inschrijving (%s) in mandje van %s' % (
                              regel.pk, inschrijving, inschrijving.koper))

            self._verwijder_reservering(inschrijving)

            mandje = regel.bestellingmandje_set.first()
            if mandje.pk not in mandje_pks:
                mandje_pks.append(mandje.pk)

            # verwijder het product, dan verdwijnt deze ook uit het mandje
            self.stdout.write('[INFO] BestellingRegel met pk=%s wordt verwijderd' % regel.pk)
            regel.delete()
        # for

        return mandje_pks

    def reserveer(self, inschrijving: WedstrijdInschrijving) -> BestellingRegel:
        """ Maak een reservering voor de wedstrijd sessie (zodat iemand anders deze niet kan reserveren)
            en geef een BestellingRegel terug.
        """

        # verhoog het aantal inschrijvingen op deze sessie
        # hiermee geven we een garantie op een plekje
        # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
        sessie = inschrijving.sessie
        sessie.aantal_inschrijvingen += 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

        wedstrijd = inschrijving.wedstrijd
        sporter = inschrijving.sporterboog.sporter

        prijs_euro = wedstrijd.bepaal_prijs_voor_sporter(sporter)
        korting_euro = self.bepaal_korting(inschrijving)
        # btw en gewicht zijn niet van toepassing

        regel = BestellingRegel(
                    korte_beschrijving=kort,
                    prijs_euro=prijs_euro,
                    korting_euro=korting_euro,
                    code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel.save()

        inschrijving.bestelling = regel
        inschrijving.save(update_fields=['bestelling'])

        return regel

    def verwijder_reservering(self, regel: BestellingRegel):
        raise NotImplementedError()

    def _verwijder_reservering(self, inschrijving: WedstrijdInschrijving): # -> WedstrijdAfmelding:

        if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_RESERVERING_MANDJE:
            # schrijf de sporter uit bij de sessie
            # Noteer: geen concurrency risico want serialisatie via deze achtergrondtaak
            sessie = inschrijving.sessie
            if sessie.aantal_inschrijvingen > 0:  # voorkom ongelukken: kan negatief niet opslaan
                sessie.aantal_inschrijvingen -= 1
                sessie.save(update_fields=['aantal_inschrijvingen'])

            self.stdout.write('[INFO] WedstrijdInschrijving pk=%s reservering wordt verwijderd' % inschrijving.pk)
            inschrijving.delete()

        # # TODO: ombouwen naar WedstrijdAfmelding
        #
        # # zet de inschrijving om in status=afgemeld of verwijderd
        # # dit heeft de voorkeur over het echt verwijderen van inschrijvingen,
        # # want als er wel een betaling volgt dan kunnen we die nergens aan koppelen
        # oude_status = inschrijving.status
        # if oude_status ==
        #
        # stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        #
        # if inschrijving.status == WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF:
        #     msg = "[%s] Afgemeld voor de wedstrijd en reservering verwijderd\n" % stamp_str
        #     inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD
        # else:
        #     msg = "[%s] Reservering voor wedstrijd verwijderd\n" % stamp_str
        #     inschrijving.status = WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD
        #
        # inschrijving.korting = None
        # inschrijving.log += msg
        # inschrijving.save(update_fields=['status', 'log', 'korting'])



wedstrijd_bestel_plugin = BestelPlugin()

# end of file

