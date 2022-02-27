# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def converteer_team_volgorde(apps, _):

    teamtype_klas = apps.get_model('BasisTypen', 'TeamType')

    for teamtype in teamtype_klas.objects.all():
        try:
            teamtype.volgorde_nr = int(teamtype.volgorde)
        except ValueError:
            teamtype.volgorde_nr = 0

        teamtype.save(update_fields=['volgorde_nr'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0026_wa_rename'),
    ]

    # migratie functies
    operations = [
        migrations.RenameField(
            model_name='leeftijdsklasse',
            old_name='geslacht',
            new_name='wedstrijd_geslacht',
        ),
        migrations.RemoveIndex(
            model_name='teamtype',
            name='BasisTypen__volgord_4984e4_idx',
        ),
        migrations.AddField(
            model_name='teamtype',
            name='volgorde_nr',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(converteer_team_volgorde),
        migrations.RemoveField(
            model_name='teamtype',
            name='volgorde',
        ),
        migrations.RenameField(
            model_name='teamtype',
            old_name='volgorde_nr',
            new_name='volgorde',
        ),
        migrations.AddIndex(
            model_name='teamtype',
            index=models.Index(fields=['volgorde'], name='BasisTypen__volgord_4984e4_idx'),
        ),
    ]

# end of file
