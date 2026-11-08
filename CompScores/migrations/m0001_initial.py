# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0125_mutatie_match'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='ExterneScoresImportLogboek',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logboek', models.TextField(blank=True)),
                ('match', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Competitie.competitiematch')),
            ],
            options={
                'verbose_name': 'Externe scores import logboek',
                'verbose_name_plural': 'Externe scores import logboeken',
            },
        ),
    ]

# end of file
