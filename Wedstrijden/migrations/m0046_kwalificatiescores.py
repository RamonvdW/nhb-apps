# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0045_locatie_3'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijd',
            name='eis_kwalificatie_scores',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Kwalificatiescore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField(default='2000-01-01')),
                ('naam', models.CharField(max_length=50)),
                ('waar', models.CharField(max_length=50)),
                ('resultaat', models.PositiveSmallIntegerField(default=0)),
                ('inschrijving', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijdinschrijving')),
            ],
        ),
    ]

# end of file
