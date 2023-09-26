# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0028_scheids'),
        ('Wedstrijden', 'm0047_aantal_scheids'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WedstrijdDagScheids',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dag_offset', models.SmallIntegerField(default=0)),
                ('volgorde', models.SmallIntegerField(default=0)),
                ('titel', models.CharField(default='', max_length=20)),
                ('gekozen', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Sporter.sporter')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Wedstrijden.wedstrijd')),
            ],
            options={'verbose_name': 'Wedstrijddag scheids', 'verbose_name_plural': 'Wedstrijddag scheids'},
        ),
        migrations.CreateModel(
            name='ScheidsBeschikbaarheid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField()),
                ('opgaaf', models.CharField(choices=[('?', 'Niet ingevuld'), ('J', 'Ja'), ('D', 'Onzeker'), ('N', 'Nee')], default='?', max_length=1)),
                ('log', models.TextField(default='')),
                ('scheids', models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter')),
            ],
            options={'verbose_name': 'Scheids beschikbaarheid', 'verbose_name_plural': 'Scheids beschikbaarheid'},
        ),
    ]

# end of file
