# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via CompetitieMutatie
"""

from Competitie.definities import (MUTATIE_COMPETITIE_OPSTARTEN, MUTATIE_AG_VASTSTELLEN,
                                   MUTATIE_DOORZETTEN_REGIO_NAAR_RK,
                                   MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK, MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK,
                                   MUTATIE_KAMP_INDIV_AFSLUITEN, MUTATIE_KAMP_TEAMS_AFSLUITEN)
from Competitie.models import Competitie, CompetitieMutatie
from Competitie.operations import (competities_aanmaken,
                                   bepaal_startjaar_nieuwe_competitie,
                                   aanvangsgemiddelden_vaststellen_voor_afstand,
                                   uitslag_regio_indiv_naar_histcomp, uitslag_regio_teams_naar_histcomp,
                                   uitslag_rk_indiv_naar_histcomp, uitslag_rk_teams_naar_histcomp,
                                   uitslag_bk_indiv_naar_histcomp, uitslag_bk_teams_naar_histcomp)
from CompLaagBond.operations.verwerk_mutaties import VerwerkCompLaagBondMutaties
from CompLaagRayon.operations.verwerk_mutaties import VerwerkCompLaagRayonMutaties


class VerwerkCompBeheerMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompBeheer applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger

    def _verwerk_mutatie_competitie_opstarten(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: Competitie opstarten' % mutatie.pk)
        jaar = bepaal_startjaar_nieuwe_competitie()
        # beveiliging tegen dubbel aanmaken
        if Competitie.objects.filter(begin_jaar=jaar).count() == 0:
            competities_aanmaken(jaar)

    def _verwerk_mutatie_ag_vaststellen(self, mutatie: CompetitieMutatie):
        comp = mutatie.competitie
        afstand = int(comp.afstand)
        self.stdout.write('[INFO] Verwerk mutatie %s: AG vaststellen %dm' % (mutatie.pk, afstand))
        aanvangsgemiddelden_vaststellen_voor_afstand(afstand)

    def _verwerk_mutatie_regio_naar_rk(self, mutatie: CompetitieMutatie):
        """ de BKO heeft gevraagd de regiocompetitie af te sluiten en alles klaar te maken voor het RK """
        self.stdout.write('[INFO] Verwerk mutatie %s: afsluiten regiocompetitie' % mutatie.pk)
        comp = mutatie.competitie

        # controleer dat de competitie in fase G is
        if not comp.regiocompetitie_is_afgesloten:
            # ga door naar fase J
            comp.regiocompetitie_is_afgesloten = True
            comp.save(update_fields=['regiocompetitie_is_afgesloten'])

            rk_mutaties = VerwerkCompLaagRayonMutaties(self.stdout, self.my_logger)
            rk_mutaties.verwerk_mutatie_regio_naar_rk(comp)

            # eindstand individuele regiocompetitie naar historisch uitslag overzetten
            # (ook nodig voor AG's nieuwe competitie)
            uitslag_regio_indiv_naar_histcomp(comp)

            # eindstand teamcompetitie regio naar historische uitslag overzetten
            uitslag_regio_teams_naar_histcomp(comp)

            # FUTURE: maak taken aan voor de HWL's om deelname RK voor sporters van eigen vereniging door te geven

            # FUTURE: versturen e-mails uitnodigingen naar de deelnemers gebeurt tijdens opstarten elk uur

    def _verwerk_mutatie_opstarten_bk_indiv(self, mutatie: CompetitieMutatie):
        """ de BKO heeft gevraagd alles klaar te maken voor het BK individueel """

        self.stdout.write('[INFO] Verwerk mutatie %s: indiv doorzetten van RK naar BK' % mutatie.pk)
        comp = mutatie.competitie

        # controleer dat de competitie in fase N is
        if not comp.rk_indiv_afgesloten:

            uitslag_rk_indiv_naar_histcomp(comp)

            # individuele deelnemers vaststellen
            bk_mutaties = VerwerkCompLaagBondMutaties(self.stdout, self.my_logger)
            bk_mutaties.maak_deelnemerslijst_bk_indiv(comp)

            # ga door naar fase N
            comp.rk_indiv_afgesloten = True
            comp.save(update_fields=['rk_indiv_afgesloten'])

    def _verwerk_mutatie_opstarten_bk_teams(self, mutatie: CompetitieMutatie):
        """ de BKO heeft gevraagd alles klaar te maken voor het BK teams """

        self.stdout.write('[INFO] Verwerk mutatie %s: teams doorzetten van RK naar BK' % mutatie.pk)
        comp = mutatie.competitie

        # controleer dat de competitie in fase N is
        if not comp.rk_teams_afgesloten:

            uitslag_rk_teams_naar_histcomp(comp)

            # individuele deelnemers vaststellen
            bk_mutaties = VerwerkCompLaagBondMutaties(self.stdout, self.my_logger)
            bk_mutaties.maak_deelnemerslijst_bk_teams(comp)

            # ga door naar fase N
            comp.rk_teams_afgesloten = True
            comp.save(update_fields=['rk_teams_afgesloten'])

    def _verwerk_mutatie_afsluiten_bk_indiv(self, mutatie: CompetitieMutatie):
        """ BK individueel afsluiten """

        self.stdout.write('[INFO] Verwerk mutatie %s: afsluiten BK indiv' % mutatie.pk)
        comp = mutatie.competitie

        # controleer dat de competitie in fase P is
        if not comp.bk_indiv_afgesloten:

            uitslag_bk_indiv_naar_histcomp(comp)

            # ga door naar fase Q
            comp.bk_indiv_afgesloten = True
            comp.save(update_fields=['bk_indiv_afgesloten'])

    def _verwerk_mutatie_afsluiten_bk_teams(self, mutatie: CompetitieMutatie):
        """ BK teams afsluiten"""

        self.stdout.write('[INFO] Verwerk mutatie %s: afsluiten BK teams' % mutatie.pk)
        comp = mutatie.competitie

        # controleer dat de competitie in fase N is
        if not comp.bk_teams_afgesloten:

            uitslag_bk_teams_naar_histcomp(comp)

            # ga door naar fase Q
            comp.bk_teams_afgesloten = True
            comp.save(update_fields=['bk_teams_afgesloten'])

    HANDLERS = {
        MUTATIE_COMPETITIE_OPSTARTEN: _verwerk_mutatie_competitie_opstarten,
        MUTATIE_AG_VASTSTELLEN: _verwerk_mutatie_ag_vaststellen,
        MUTATIE_DOORZETTEN_REGIO_NAAR_RK: _verwerk_mutatie_regio_naar_rk,
        MUTATIE_KAMP_INDIV_DOORZETTEN_NAAR_BK: _verwerk_mutatie_opstarten_bk_indiv,
        MUTATIE_KAMP_TEAMS_DOORZETTEN_NAAR_BK: _verwerk_mutatie_opstarten_bk_teams,
        MUTATIE_KAMP_INDIV_AFSLUITEN: _verwerk_mutatie_afsluiten_bk_indiv,
        MUTATIE_KAMP_TEAMS_AFSLUITEN: _verwerk_mutatie_afsluiten_bk_teams,
    }

    def verwerk(self, mutatie: CompetitieMutatie) -> bool:
        """ Verwerk een mutatie die via de database tabel ontvangen is """

        code = mutatie.mutatie
        try:
            mutatie_code_verwerk_functie = self.HANDLERS[code]
        except KeyError:
            # code niet ondersteund door deze plugin
            return False

        mutatie_code_verwerk_functie(self, mutatie)  # noqa
        return True

    def verwerk_in_achtergrond(self):
        # doe een klein beetje werk
        pass


# end of file
