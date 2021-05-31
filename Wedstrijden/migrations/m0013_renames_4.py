# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0012_renames_3'),
        ('Competitie', 'm0037_renames_4')
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijdenplan',
            name='wedstrijden',
        ),
        migrations.RenameField(
            model_name='wedstrijdenplan',
            old_name='wedstrijden2',
            new_name='wedstrijden',
        ),
        migrations.RemoveField(
            model_name='competitiewedstrijd',
            name='old',
        ),
        migrations.DeleteModel(
            name='Wedstrijd',
        ),
        # verwijder de related_name
        migrations.AlterField(
            model_name='wedstrijdenplan',
            name='wedstrijden',
            field=models.ManyToManyField(blank=True, to='Wedstrijden.CompetitieWedstrijd'),
        ),
    ]

# end of file
