# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from BasisTypen.definities import ORGANISATIE_KHSN
from BasisTypen.operations import get_organisatie_teamtypen
from Competitie.definities import MUTATIE_REGIO_TEAM_RONDE
from Competitie.models import (RegiocompetitieSporterBoog, RegiocompetitieTeam, RegiocompetitieRondeTeam,
                               CompetitieMutatie)
from Functie.models import Functie
from Taken.operations import maak_taak
import datetime


class VerwerkCompLaagRegioMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompLaagRegio applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger

        self._boogtypen = list()        # [boog_type.pk, ..]
        self._team_volgorde = list()    # [team_type.pk, ..]
        self._team_boogtypen = dict()   # [team_type.pk] = [boog_type.pk, ..]

        self._bepaal_boog2team()

    def _bepaal_boog2team(self):
        """ bepaalde boog typen mogen meedoen in bepaalde team types
            straks als we de team leden gaan verdelen over de teams moeten dat in een slimme volgorde
            zodat de sporters in toegestane teams en alle team typen gevuld worden.
            Voorbeeld: LB mag meedoen in LB, TR, BB en R teams terwijl C alleen in C team mag.
                       we moeten dus niet beginnen met de LB sporter in een R team te stoppen en daarna
                       geen sporters meer over hebben voor het LB team.
        """

        for team_type in get_organisatie_teamtypen(ORGANISATIE_KHSN):

            self._team_boogtypen[team_type.pk] = boog_lijst = list()

            for boog_type in team_type.boog_typen.all():
                boog_lijst.append(boog_type.pk)

                if boog_type.pk not in self._boogtypen:
                    self._boogtypen.append(boog_type.pk)
            # for
        # for

        team_aantal = [(len(boog_typen), team_type_pk) for team_type_pk, boog_typen in self._team_boogtypen.items()]
        team_aantal.sort()
        self._team_volgorde = [team_type_pk for _, team_type_pk in team_aantal]

    @staticmethod
    def _geef_hwl_taak_team_ronde(comp, ronde_nr, taak_ver):
        """ maak een taak aan voor de HWL van de verenigingen
            om door te geven dat de volgende team ronde gestart is en team invallers gekoppeld moeten worden
            alleen verenigingen met een team staan in taak_ver
        """

        comp.bepaal_fase()
        if comp.fase_teams > 'F':
            # voorbij de wedstrijden fase, dus vanaf nu is de RCL waarschijnlijk bezig om de laatste hand
            # aan de uitslag te leggen en dan willen we de HWLs niet meer kietelen.
            return

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        taak_log = "[%s] Taak aangemaakt" % stamp_str

        taak_tekst = "De teamcompetitie van de %s is zojuist doorgezet naar ronde %s.\n" % (comp.beschrijving, ronde_nr)
        taak_tekst += "Als HWL kan je nu invallers koppelen voor elk van de teams van jouw vereniging."

        taak_deadline = now + datetime.timedelta(days=5)

        taak_onderwerp = "Koppel invallers %s ronde %s" % (comp.beschrijving, ronde_nr)

        for functie_hwl in Functie.objects.filter(rol='HWL', vereniging__ver_nr__in=taak_ver):
            # maak een taak aan voor deze HWL
            maak_taak(toegekend_aan_functie=functie_hwl,
                      deadline=taak_deadline,
                      aangemaakt_door=None,  # systeem
                      onderwerp=taak_onderwerp,
                      beschrijving=taak_tekst,
                      log=taak_log)
        # for

    def _verwerk_mutatie_regio_team_ronde(self, mutatie: CompetitieMutatie):
        self.stdout.write('[INFO] Verwerk mutatie %s: regio team ronde' % mutatie.pk)
        deelcomp = mutatie.regiocompetitie

        # bepaal de volgende ronde
        if deelcomp.huidige_team_ronde > 7:
            # alle rondes al gehad - silently ignore
            return

        if deelcomp.huidige_team_ronde == 7:
            # afsluiten van de laatste ronde
            deelcomp.huidige_team_ronde = 99
            deelcomp.save(update_fields=['huidige_team_ronde'])
            return

        ronde_nr = deelcomp.huidige_team_ronde + 1

        if ronde_nr == 1:
            teams = (RegiocompetitieTeam
                     .objects
                     .filter(regiocompetitie=deelcomp))

            if teams.count() == 0:
                self.stdout.write('[WARNING] Team ronde doorzetten voor regio %s geweigerd want 0 teams' % deelcomp)
                return
        else:
            ronde_teams = (RegiocompetitieRondeTeam
                           .objects
                           .filter(team__regiocompetitie=deelcomp,
                                   ronde_nr=deelcomp.huidige_team_ronde))
            if ronde_teams.count() == 0:
                self.stdout.write(
                    '[WARNING] Team ronde doorzetten voor regio %s geweigerd want 0 ronde teams' % deelcomp)
                return

            aantal_scores = ronde_teams.filter(team_score__gt=0).count()
            if aantal_scores == 0:
                self.stdout.write(
                    '[WARNING] Team ronde doorzetten voor regio %s geweigerd want alle team_scores zijn 0' % deelcomp)
                return

        now = timezone.now()
        now = timezone.localtime(now)
        now_str = now.strftime("%Y-%m-%d %H:%M")

        ver_dict = dict()       # [ver_nr] = list(vsg, deelnemer_pk, boog_type_pk)

        # voor elke deelnemer het gemiddelde_begin_team_ronde invullen
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('bij_vereniging',
                                          'sporterboog',
                                          'sporterboog__boogtype')
                          .filter(regiocompetitie=deelcomp,
                                  inschrijf_voorkeur_team=True)):

            # let op: geen verschil vaste/vsg-teams meer sinds reglementswijziging 2021-06-28
            if deelnemer.aantal_scores == 0 or ronde_nr == 1:
                vsg = deelnemer.ag_voor_team
            else:
                vsg = deelnemer.gemiddelde  # individuele voortschrijdend gemiddelde

            deelnemer.gemiddelde_begin_team_ronde = vsg
            deelnemer.save(update_fields=['gemiddelde_begin_team_ronde'])

            ver_nr = deelnemer.bij_vereniging.ver_nr
            tup = (-vsg, deelnemer.pk, deelnemer.sporterboog.boogtype.pk)
            try:
                ver_dict[ver_nr].append(tup)
            except KeyError:
                ver_dict[ver_nr] = [tup]
        # for

        for team_lid in ver_dict.values():
            team_lid.sort()
        # for

        taak_ver = list()

        # verwijder eventuele oude team ronde records (veroorzaakt door het terugzetten van een ronde)
        qset = RegiocompetitieRondeTeam.objects.filter(team__regiocompetitie=deelcomp, ronde_nr=ronde_nr)
        count = qset.count()
        if count > 0:
            self.stdout.write('[INFO] Verwijder %s oude records voor team ronde %s in regio %s' % (
                        count, ronde_nr, deelcomp))
            qset.delete()

        # maak voor elk team een 'ronde instantie' aan waarin de invallers en score bijgehouden worden
        # verdeel ook de sporters volgens VSG
        for team_type_pk in self._team_volgorde:

            team_boogtypen = self._team_boogtypen[team_type_pk]

            for team in (RegiocompetitieTeam
                         .objects
                         .select_related('vereniging')
                         .prefetch_related('leden')
                         .filter(regiocompetitie=deelcomp,
                                 team_type__pk=team_type_pk)
                         .order_by('-aanvangsgemiddelde')):     # hoogste eerst

                ronde_team = RegiocompetitieRondeTeam(
                                team=team,
                                ronde_nr=ronde_nr,
                                logboek="[%s] Aangemaakt bij opstarten ronde %s\n" % (now_str, ronde_nr))
                ronde_team.save()

                # koppel de leden
                if deelcomp.regio_heeft_vaste_teams:
                    # vaste team begint elke keer met de vaste leden
                    sporter_pks = team.leden.values_list('pk', flat=True)
                else:
                    # voortschrijdend gemiddelde: pak de volgende 4 beste sporters van de vereniging
                    sporter_pks = list()
                    ver_nr = team.vereniging.ver_nr
                    ver_leden = ver_dict[ver_nr]
                    gebruikt = list()
                    for tup in ver_leden:
                        _, deelnemer_pk, boogtype_pk = tup
                        if boogtype_pk in team_boogtypen:
                            sporter_pks.append(deelnemer_pk)
                            gebruikt.append(tup)

                        if len(sporter_pks) == 4:
                            break
                    # for

                    for tup in gebruikt:
                        ver_leden.remove(tup)
                    # for

                ronde_team.deelnemers_geselecteerd.set(sporter_pks)
                ronde_team.deelnemers_feitelijk.set(sporter_pks)

                # schrijf de namen van de leden in het logboek
                ronde_team.logboek += '[%s] Geselecteerde leden:\n' % now_str
                for deelnemer in (RegiocompetitieSporterBoog
                                  .objects
                                  .select_related('sporterboog__sporter')
                                  .filter(pk__in=sporter_pks)):
                    ronde_team.logboek += '   ' + str(deelnemer.sporterboog.sporter) + '\n'
                # for
                ronde_team.save(update_fields=['logboek'])

                if team.vereniging.ver_nr not in taak_ver:
                    taak_ver.append(team.vereniging.ver_nr)
            # for
        # for

        deelcomp.huidige_team_ronde = ronde_nr
        deelcomp.save(update_fields=['huidige_team_ronde'])

        # geef de HWL's een taak om de invallers te koppelen
        self._geef_hwl_taak_team_ronde(deelcomp.competitie, ronde_nr, taak_ver)

    HANDLERS = {
        MUTATIE_REGIO_TEAM_RONDE: _verwerk_mutatie_regio_team_ronde,
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
