# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van RK/BK programma's in de vorm van Google Sheets in een folder structuur in Google Drive. """

from django.conf import settings
from django.utils import timezone
from Competitie.models import Competitie
from CompKampioenschap.operations import iter_indiv_wedstrijdformulieren, iter_teams_wedstrijdformulieren
from GoogleDrive.models import Bestand
from GoogleDrive.operations import StorageGoogleDrive, StorageError
from typing import Generator


class StorageWedstrijdformulieren(StorageGoogleDrive):

    """ let op: genereert StorageError exception """

    FOLDER_NAME_TOP = settings.GOOGLE_DRIVE_FOLDER_NAME_TOP
    FOLDER_NAME_SITE = settings.GOOGLE_DRIVE_FOLDER_SITE
    FOLDER_NAME_TEMPLATES = settings.GOOGLE_DRIVE_FOLDER_NAME_TEMPLATES

    COMP2TEMPLATE = {
        # dezelfde template voor 25m1pijl indoor RK/BK
        '25m1pijl Individueel RK': 'template-25m1pijl-individueel',
        '25m1pijl Individueel BK': 'template-25m1pijl-individueel',

        # dezelfde template voor Indoor individueel RK/BK
        'Indoor Individueel RK': 'template-indoor-individueel',
        'Indoor Individueel BK': 'template-indoor-individueel',

        # dezelfde template voor alle team wedstrijden
        '25m1pijl Teams RK': 'template-teams',
        '25m1pijl Teams BK': 'template-teams',
        'Indoor Teams RK': 'template-teams',
        'Indoor Teams BK': 'template-teams',
    }

    @staticmethod
    def _params_to_folder_name(afstand: int, is_teams: bool, is_bk: bool) -> str:
        if afstand == 18:
            folder_name = "Indoor "
        elif afstand == 25:
            folder_name = "25m1pijl "
        else:
            raise StorageError('Geen valide afstand: %s' % repr(afstand))

        if is_teams:
            folder_name += "Teams "
        else:
            folder_name += "Individueel "

        if is_bk:
            folder_name += 'BK'
        else:
            folder_name += 'RK'

        return folder_name


def aantal_ontbrekende_wedstrijdformulieren_rk_bk(comp: Competitie) -> int:
    """ tel het aantal wedstrijdformulieren dat nog niet aangemaakt is
        aan de hand van de informatie in tabel Bestand.
    """
    todo_count = 0

    if comp:
        # maak een map met de huidige bestanden
        sel2bestand = dict()
        for bestand in Bestand.objects.filter(begin_jaar=comp.begin_jaar, afstand=comp.afstand):
            sel = (bestand.begin_jaar, bestand.afstand, bestand.klasse_pk,
                   bestand.is_teams, bestand.is_bk, bestand.rayon_nr)
            sel2bestand[sel] = bestand
        # for

        for tup in iter_indiv_wedstrijdformulieren(comp):
            afstand, is_bk, klasse_pk, rayon_nr, fname = tup
            #                                           is_teams
            sel = (comp.begin_jaar, afstand, klasse_pk, False, is_bk, rayon_nr)
            if sel not in sel2bestand:
                # niet gevonden; voeg toe aan de todo lijst
                todo_count += 1
        # for

        for tup in iter_teams_wedstrijdformulieren(comp):
            afstand, is_bk, klasse_pk, rayon_nr, fname = tup
            #                                           is_teams
            sel = (comp.begin_jaar, afstand, klasse_pk, True, is_bk, rayon_nr)
            if sel not in sel2bestand:
                # niet gevonden; voeg toe aan de todo lijst
                todo_count += 1
        # for

    return todo_count


def get_url_wedstrijdformulier(begin_jaar: int, afstand: int, rayon_nr: int, klasse_pk: int, is_bk: bool, is_teams: bool):

    bestand = Bestand.objects.filter(begin_jaar=begin_jaar,
                                     afstand=afstand,
                                     rayon_nr=rayon_nr,
                                     klasse_pk=klasse_pk,
                                     is_bk=is_bk,
                                     is_teams=is_teams).first()

    if bestand:
        return "https://docs.google.com/spreadsheets/d/%s/edit" % bestand.file_id

    return None


def zet_dirty(begin_jaar: int, afstand: int, rayon_nr: int, klasse_pk: int, is_bk: bool, is_teams: bool):

    bestand = Bestand.objects.filter(begin_jaar=begin_jaar,
                                     afstand=afstand,
                                     rayon_nr=rayon_nr,
                                     klasse_pk=klasse_pk,
                                     is_bk=is_bk,
                                     is_teams=is_teams).first()

    if bestand:
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        bestand.is_dirty = True
        bestand.log += '[%s] Dirty gemaakt\n' % stamp_str
        bestand.save(update_fields=['is_dirty', 'log'])
    # else:
    #     print('[DEBUG] Bestand niet gevonden: %s, %s, %s, %s, %s' % (begin_jaar, afstand, klasse_pk, is_bk, is_teams))


def iter_dirty_wedstrijdformulieren(begin_jaar: int) -> Generator[Bestand, None, None]:
    """ geef een lijst terug met de wedstrijdformulieren die de is_dirty vlag gezet hebben in tabel Bestand.

        Returns: [tup, ...] with tup = (afstand, klasse_pk, is_bk, is_teams, file_id)
    """
    for bestand in Bestand.objects.filter(begin_jaar=begin_jaar, is_dirty=True):
        yield bestand
    # for


# end of file
