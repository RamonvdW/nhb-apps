# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.utils import timezone
from Competitie.definities import MUTATIE_MAAK_WEDSTRIJDFORMULIEREN, MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN
from Competitie.models import Competitie, CompetitieMatch, CompetitieMutatie
from CompKampioenschap.operations import maak_mutatie_update_dirty_wedstrijdformulieren
from CompKampioenschap.operations import iter_indiv_wedstrijdformulieren, iter_teams_wedstrijdformulieren
from CompKampioenschap.operations.wedstrijdformulieren_indiv_update import UpdateIndivWedstrijdFormulier
from CompKampioenschap.operations.wedstrijdformulieren_teams import UpdateTeamsWedstrijdFormulier
from CompKampioenschap.operations.storage_wedstrijdformulieren import (StorageWedstrijdformulieren,
                                                                       iter_dirty_wedstrijdformulieren)
from CompKampioenschap.operations.monitor_wedstrijdformulieren import MonitorGoogleSheetsWedstrijdformulieren
from CompLaagBond.models import KampBK
from CompLaagRayon.models import KampRK
from GoogleDrive.operations import StorageGoogleSheet, StorageError
import time


class VerwerkCompKampMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompKampioenschap applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.

        Ook gedeelde code voor afhandelen mutaties voor RK en BK.
    """

    def __init__(self, stdout):
        self.stdout = stdout
        self._achtergrond_monitor = None

    def _verwerk_mutatie_maak_wedstrijdformulieren(self, mutatie):
        """ maak alle Google Sheet wedstrijdformulieren aan in de gedeelde Google Drive folders
            deze mutatie wordt opgestart zodra de toestemming binnen is.
        """
        comp = mutatie.competitie
        self.stdout.write('[INFO] Maak wedstrijdformulieren voor %s' % comp.beschrijving)

        try:
            storage = StorageWedstrijdformulieren(self.stdout, comp.begin_jaar, settings.GOOGLE_DRIVE_SHARE_WITH)
            storage.check_access()

            is_teams = False
            for afstand, is_bk, klasse_pk, rayon_nr, fname in iter_indiv_wedstrijdformulieren(comp):
                self.stdout.write('[INFO] Maak %s' % fname)
                storage.maak_sheet_van_template(afstand, is_teams, is_bk, klasse_pk, rayon_nr, fname)
            # for

            is_teams = True
            for afstand, is_bk, klasse_pk, rayon_nr, fname in iter_teams_wedstrijdformulieren(comp):
                self.stdout.write('[INFO] Maak %s' % fname)
                storage.maak_sheet_van_template(afstand, is_teams, is_bk, klasse_pk, rayon_nr, fname)
            # for

            # laat alle formulieren vullen
            maak_mutatie_update_dirty_wedstrijdformulieren(comp)

        except StorageError as err:
            msg = 'Onverwachte fout in verwerk_mutatie_maak_wedstrijdformulieren:\n'
            msg += '   %s\n' % str(err)
            self.stdout.write('[ERROR] {CompKampioenschap.verwerk_mutaties} ' + msg)

    def _verwerk_mutatie_update_dirty_wedstrijdformulieren(self, mutatie):
        begin_jaar = mutatie.competitie.begin_jaar
        self.stdout.write('[INFO] Update dirty wedstrijdformulieren')
        sheet = None

        # note: Indoor en 25m1pijl hebben aparte klassen, maar BK+elk RK hebben dezelfde klasse_pk, dus rayon_nr nodig
        indiv_klasse_pk_rayon2match = dict[tuple[int, int], CompetitieMatch]()
        team_klasse_pk_rayon2match = dict[tuple[int, int], CompetitieMatch]()

        # doorloop alle wedstrijden
        for deelkamp in (KampRK
                         .objects
                         .filter(competitie__begin_jaar=begin_jaar)
                         .select_related('rayon')
                         .prefetch_related('matches')):

            rayon_nr = deelkamp.rayon.rayon_nr

            for match in (deelkamp.matches
                          .prefetch_related('indiv_klassen',
                                            'team_klassen')
                          .select_related('vereniging',
                                          'locatie')):

                for klasse in match.indiv_klassen.all():
                    indiv_klasse_pk_rayon2match[(klasse.pk, rayon_nr)] = match
                # for

                for klasse in match.team_klassen.all():
                    team_klasse_pk_rayon2match[(klasse.pk, rayon_nr)] = match
                # for
        # for

        for deelkamp in (KampBK
                         .objects
                         .filter(competitie__begin_jaar=begin_jaar)
                         .prefetch_related('matches')):

            rayon_nr = 0
            for match in (deelkamp.matches
                          .prefetch_related('indiv_klassen',
                                            'team_klassen')
                          .select_related('vereniging',
                                          'locatie')):

                for klasse in match.indiv_klassen.all():
                    indiv_klasse_pk_rayon2match[(klasse.pk, rayon_nr)] = match
                # for

                for klasse in match.team_klassen.all():
                    team_klasse_pk_rayon2match[(klasse.pk, rayon_nr)] = match
                # for
        # for

        for bestand in iter_dirty_wedstrijdformulieren(begin_jaar):
            self.stdout.write('[INFO] Update dirty bestand [pk=%s] %s' % (bestand.pk, bestand.fname))

            # om te voorkomen dat we over de quota van 60 per minuut heen gaan
            # altijd 1 seconden vertragen
            time.sleep(1.0)

            if not sheet:
                sheet = StorageGoogleSheet(self.stdout)
            sheet.selecteer_file(bestand.file_id)

            if bestand.is_bk:
                rayon_nr = 0
            else:
                rayon_nr = bestand.rayon_nr

            res = ''
            if bestand.is_teams:
                # teams
                updater = UpdateTeamsWedstrijdFormulier(self.stdout, sheet)
                match = team_klasse_pk_rayon2match.get((bestand.klasse_pk, rayon_nr), None)
            else:
                # individueel
                updater = UpdateIndivWedstrijdFormulier(self.stdout, sheet)
                match = indiv_klasse_pk_rayon2match.get((bestand.klasse_pk, rayon_nr), None)

            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

            if match:
                res = updater.update_wedstrijdformulier(bestand, match)
                msg = '[%s] Bijgewerkt met resultaat %s\n' % (stamp_str, res)
            else:
                msg = '[%s] ERROR: kan CompetitieMatch niet vinden voor Bestand pk=%s\n' % (stamp_str, bestand.pk)

            bestand.is_dirty = False
            # newline toevoegen na handmatige edit in admin interface
            bestand.log = bestand.log.strip() + '\n'
            bestand.log += msg
            bestand.save(update_fields=['is_dirty', 'log'])
        # for

    HANDLERS = {
        MUTATIE_MAAK_WEDSTRIJDFORMULIEREN: _verwerk_mutatie_maak_wedstrijdformulieren,
        MUTATIE_UPDATE_DIRTY_WEDSTRIJDFORMULIEREN: _verwerk_mutatie_update_dirty_wedstrijdformulieren,
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
        if not self._achtergrond_monitor:
            werk = list()
            for comp in Competitie.objects.all():
                comp.bepaal_fase()

                is_teams = False
                if 'J' <= comp.fase_indiv <= 'L':
                    is_bk = False
                    tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                    werk.append(tup)

                if 'N' <= comp.fase_indiv <= 'P':
                    is_bk = True
                    tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                    werk.append(tup)

                if False:       # teams are Excel, for now
                    is_teams = True
                    if 'J' <= comp.fase_teams <= 'L':
                        is_bk = False
                        tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                        werk.append(tup)

                    if 'N' <= comp.fase_teams <= 'P':
                        is_bk = True
                        tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                        werk.append(tup)

            # for

            self._achtergrond_monitor = MonitorGoogleSheetsWedstrijdformulieren(self.stdout, werk)

        self._achtergrond_monitor.doe_beetje_werk()


# end of file
