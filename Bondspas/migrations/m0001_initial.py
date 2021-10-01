# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = []

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Bondspas',
            fields=[
                ('lid_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('N', 'Nieuw verzoek'), ('O', 'Ophaal verzoek'), ('B', 'In behandeling'), ('A', 'Aanwezig'), ('F', 'Mislukt'), ('V', 'Verwijderd')], default='N', max_length=1)),
                ('aanwezig_sinds', models.DateTimeField(null=True)),
                ('opnieuw_proberen_na', models.DateTimeField(null=True)),
                ('filename', models.CharField(max_length=50)),
                ('aantal_keer_bekeken', models.PositiveIntegerField(default=0)),
                ('aantal_keer_opgehaald', models.PositiveIntegerField(default=0)),
                ('log', models.TextField()),
            ],
            options={
                'verbose_name': 'Bondspas',
                'verbose_name_plural': 'Bondspassen',
            },
        ),
    ]

# end of file
