# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Evenement', 'm0002_afgemeld'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='EvenementSessie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titel', models.CharField(default='', max_length=50)),
                ('presentator', models.CharField(default='', max_length=50)),
                ('begin_tijd', models.TimeField(default='11:00')),
                ('duur_min', models.PositiveSmallIntegerField(default=60)),
                ('evenement', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Evenement.evenement')),
                ('beschrijving', models.TextField(blank=True, default='', max_length=1000)),
                ('aantal_inschrijvingen', models.SmallIntegerField(default=0)),
                ('max_deelnemers', models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                'verbose_name': 'Evenement sessie',
            },
        ),
        migrations.AddField(
            model_name='evenementinschrijving',
            name='gekozen_sessies',
            field=models.ManyToManyField(to='Evenement.evenementsessie'),
        ),
    ]

# end of file
