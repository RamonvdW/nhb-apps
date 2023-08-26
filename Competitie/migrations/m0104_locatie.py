# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def locatie_omzetten(apps, _):
    """ migratie van veld locatie """

    fix_klas = apps.get_model('Competitie', 'CompetitieMatch')

    for obj in fix_klas.objects.select_related('locatie').exclude(locatie=None).all():    # pragma: no cover
        obj.locatie_new = obj.locatie.locatie_new
        obj.save(update_fields=['locatie_new'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0103_vereniging_2'),
        ('Wedstrijden', 'm0043_locatie_1'),
    ]

    # migratie functies
    operations = [

        # maak nieuw
        migrations.AddField(
            model_name='competitiematch',
            name='locatie_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='Locatie.locatie'),
        ),

        # vertaal oud naar nieuw
        migrations.RunPython(locatie_omzetten, migrations.RunPython.noop),

        # verwijder oud
        migrations.RemoveField(
            model_name='competitiematch',
            name='locatie',
        ),

        # hernoem nieuw naar oud
        migrations.RenameField(
            model_name='competitiematch',
            old_name='locatie_new',
            new_name='locatie',
        ),
    ]

# end of file
