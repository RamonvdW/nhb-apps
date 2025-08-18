# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van RK/BK programma's in de vorm van Google Sheets in een folder structuur in Google Drive. """

from django.conf import settings
from CompKamp.operations.wedstrijdformulieren import iter_wedstrijdformulieren
from GoogleDrive.models import Bestand
from GoogleDrive.operations.google_drive import GoogleDriveStorage, StorageError


class KampStorage(GoogleDriveStorage):

    """ let op: genereert StorageError exception """

    FOLDER_NAME_TOP = settings.GOOGLE_DRIVE_FOLDER_NAME_TOP
    FOLDER_NAME_SITE = settings.NAAM_SITE
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


def ontbrekende_wedstrijdformulieren_rk_bk(comp) -> list:
    """ geef een lijst terug met de benodigde wedstrijdformulieren die nog niet aangemaakt zijn
        aan de hand van de informatie in tabel Bestand.
    """
    todo = list()

    # maak een map met de huidige bestanden
    sel2bestand = dict()
    for bestand in Bestand.objects.filter(begin_jaar=comp.begin_jaar, afstand=comp.afstand):
        sel = (bestand.begin_jaar, bestand.afstand, bestand.is_teams, bestand.is_bk, bestand.klasse_pk)
        sel2bestand[sel] = bestand
    # for

    for tup in iter_wedstrijdformulieren(comp):
        afstand, is_teams, is_bk, klasse_pk, fname = tup
        sel = (comp.begin_jaar, afstand, is_teams, is_bk, klasse_pk)
        try:
            bestand = sel2bestand[sel]
        except KeyError:
            # niet gevonden; voeg toe aan de todo lijst
            todo.append(tup)
    # for

    return todo


# end of file
