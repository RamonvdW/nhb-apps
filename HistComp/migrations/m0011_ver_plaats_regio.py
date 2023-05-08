# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def amend_histcomp(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    hist_klas = apps.get_model('HistComp', 'HistCompRegioIndiv')
    ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')

    ver_nr2regio_nr = dict()
    ver_nr2plaats = dict()
    for ver in ver_klas.objects.select_related('regio'):
        ver_nr2regio_nr[ver.ver_nr] = ver.regio.regio_nr
        ver_nr2plaats[ver.ver_nr] = ver.plaats
    # for

    # al verwijderde verenigingen
    """
    1026 Victoria
    1028 E.M.M. Riel
    1058 Willem Tell
    1066 Sint Sebastiaan Prinsenbeek
    1093 De Bosjagers
    1147 Diana
    1152 Ons Genoegen
    1170 Batavieren Treffers
    1191 Eendracht St Sebast
    1226 Centaur Asten
    1310 Goja Schutters
    1355 Ver. Voor Aangepast Sporten Tytsjerksteradiel
    """
    ver_nr2regio_nr[1026] = 109
    ver_nr2regio_nr[1028] = 107
    ver_nr2regio_nr[1058] = 109
    ver_nr2regio_nr[1066] = 107
    ver_nr2regio_nr[1093] = 111
    ver_nr2regio_nr[1147] = 114
    ver_nr2regio_nr[1152] = 114
    ver_nr2regio_nr[1170] = 115
    ver_nr2regio_nr[1191] = 116
    ver_nr2regio_nr[1226] = 113
    ver_nr2regio_nr[1310] = 102
    ver_nr2regio_nr[1355] = 103

    ver_nr2plaats[1026] = 'Elshout'
    ver_nr2plaats[1028] = 'Riel'
    ver_nr2plaats[1058] = 'Vught'
    ver_nr2plaats[1066] = 'Prinsenbeek'
    ver_nr2plaats[1093] = 'Best'
    ver_nr2plaats[1147] = 'Venray'
    ver_nr2plaats[1152] = 'America'
    ver_nr2plaats[1170] = 'Weert'
    ver_nr2plaats[1191] = 'Maastricht'
    ver_nr2plaats[1226] = 'Asten'
    ver_nr2plaats[1310] = 'Culemborg'
    ver_nr2plaats[1355] = 'Drachten'

    for ver_nr in ver_nr2regio_nr.keys():
        regio_nr = ver_nr2regio_nr[ver_nr]
        plaats = ver_nr2plaats[ver_nr]
        hist_klas.objects.filter(vereniging_nr=ver_nr).update(regio_nr=regio_nr, vereniging_plaats=plaats)
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('HistComp', 'm0010_team_en_kamp'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(code=amend_histcomp,
                             reverse_code=migrations.RunPython.noop)
    ]

# end of file
