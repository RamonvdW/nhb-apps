# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleSheet, MonitorDriveFiles
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations.wedstrijdformulieren_indiv import LeesIndivWedstrijdFormulier
from CompKampioenschap.operations.wedstrijdformulieren_teams import LeesTeamsWedstrijdFormulier


class MonitorGoogleSheetsWedstrijdformulieren:

    def __init__(self, stdout, werk: list):
        """ initialiseer de bestanden monitor
            werk = list of tuples (begin_jaar, afstand, is_bk, is_teams)
        """
        self.stdout = stdout
        self._sheets = StorageGoogleSheet(stdout)
        self._drive = MonitorDriveFiles(stdout)

        self._bestanden = list()
        self._bestanden_nieuw = list()          # zonder SheetStatus
        self._sheetstatus_cache = dict()
        self._sheetstatus_todo = list()

        for status in SheetStatus.objects.select_related('bestand'):
            self._sheetstatus_cache[status.bestand.pk] = status

            if status.gewijzigd_op > status.bekeken_op:
                self._sheetstatus_todo.append(status)
        # for

        # for tup in werk:
        #     self.stdout.write('{werk} %s' % repr(tup))
        # # for

        for begin_jaar, afstand, is_bk, is_teams in werk:
            self._laad_bestanden(begin_jaar, afstand, is_bk, is_teams)
        # for

    def _laad_bestanden(self, begin_jaar: int, afstand: int, is_bk: bool, is_teams: bool):
        for bestand in Bestand.objects.filter(begin_jaar=begin_jaar, afstand=afstand, is_bk=is_bk, is_teams=is_teams):
            if bestand.pk not in self._sheetstatus_cache:
                self._bestanden_nieuw.append(bestand)
            else:
                self._bestanden.append(bestand)
        # for

    def _get_sheetstatus(self, bestand):
        status = self._sheetstatus_cache.get(bestand.pk, None)
        if not status:
            status = SheetStatus.objects.create(bestand=bestand)
            self._sheetstatus_cache[bestand.pk] = status

        return status

    def _kijk_in_google_sheet(self, status: SheetStatus):
        self.stdout.write('[INFO] analyseer wedstrijdformulier %s' % repr(status.bestand))
        self._sheets.selecteer_file(status.bestand.file_id)

        if status.bestand.is_teams:
            lezer = LeesTeamsWedstrijdFormulier(self.stdout, self._sheets)
        else:
            lezer = LeesIndivWedstrijdFormulier(self.stdout, status.bestand, self._sheets)

        # vastgestelde fase van de wedstrijd
        # - nog niet begonnen
        # - klaar
        # indiv:
        # - voorronde 1 (individueel)
        # - voorronde 2 (individueel)
        # - laatste 16 / 8 / 4
        # - bronzen finale
        # - gouden finale
        # teams:
        # - ronde 1..7
        # wedstrijd_fase = models.CharField(max_length=100, default='')

        heeft_scores = lezer.heeft_scores()
        if heeft_scores != status.bevat_scores:
            self.stdout.write('[INFO] heeft_scores %s --> %s' % (status.bevat_scores, heeft_scores))
            status.bevat_scores = heeft_scores
            status.save(update_fields=['bevat_scores'])

        # is de uitslag al compleet?
        if status.bevat_scores or True:
            aantal_deelnemers = lezer.tel_deelnemers()

            if aantal_deelnemers != status.aantal_deelnemers:
                self.stdout.write('[INFO] aantal_deelnemers %s --> %s' % (status.aantal_deelnemers, aantal_deelnemers))
                status.aantal_deelnemers = aantal_deelnemers
                status.save(update_fields=['aantal_deelnemers'])

            uitslag_is_compleet = False

            # TODO

            if uitslag_is_compleet != status.uitslag_is_compleet:
                self.stdout.write('[INFO] uitslag_is_compleet %s --> %s' % (status.uitslag_is_compleet,
                                                                            uitslag_is_compleet))
                status.uitslag_is_compleet = uitslag_is_compleet
                status.save(update_fields=['uitslag_is_compleet'])

        elif status.uitslag_is_compleet:
            self.stdout.write('[INFO] uitslag_is_compleet %s --> %s' % (status.uitslag_is_compleet,
                                                                        False))
            status.uitslag_is_compleet = False
            status.save(update_fields=['uitslag_is_compleet'])

        # update bekeken_op
        status.bekeken_op = timezone.now()
        #status.save(update_fields=['bekeken_op'])      # TODO: enable

    def _get_bestand_todo(self) -> Bestand | None:
        if len(self._bestanden_nieuw):
            return self._bestanden_nieuw.pop(0)

        if len(self._bestanden):
            return self._bestanden.pop(0)

        return None

    def _get_sheet_todo(self) -> SheetStatus | None:
        if len(self._sheetstatus_todo):
            return self._sheetstatus_todo.pop(0)

        return None

    def doe_beetje_werk(self):
        """
            deze functie wordt ongeveer elke 3 seconden aangeroepen om een beetje werk te doen
            we willen binnen 1 uur door al het werk heen zijn, dus 60*60 = 3600 / 5 = 720 calls
            welke keer 1 doen is dus OK
        """
        bestand_count = len(self._bestanden) + len(self._bestanden_nieuw)
        sheet_count = len(self._sheetstatus_todo)
        self.stdout.write('{doe_beetje_werk} %s sheets en %s bestanden te gaan' % (sheet_count, bestand_count))

        # analyseer de inhoud van een wedstrijdformulier
        status = self._get_sheet_todo()
        if status:
            self._kijk_in_google_sheet(status)
            return

        # zoek naar nieuwe revisies van de google drive bestanden
        bestand = self._get_bestand_todo()
        if bestand:
            self.stdout.write('[INFO] bepaal laatste wijziging voor Bestand met pk=%s' % repr(bestand.pk))
            status = self._get_sheetstatus(bestand)

            # wanneer is het bestand voor het laatst gewijzigd?
            op, door = self._drive.get_laatste_wijziging(bestand.file_id)
            if op and door:
                status.gewijzigd_op, status.gewijzigd_door = op, door
                status.save(update_fields=['gewijzigd_op', 'gewijzigd_door'])

                # get the converted date/time
                status.refresh_from_db()

                if status.gewijzigd_op > status.bekeken_op:
                    self._sheetstatus_todo.append(status)


# end of file
